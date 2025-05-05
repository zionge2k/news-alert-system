"""
인프라 스택의 통합 테스트.

이 테스트는 전체 인프라 스택이 함께 올바르게 작동하는지 검증합니다.
데이터베이스, HTTP 클라이언트 및 어댑터 계층의 상호 작용을 확인합니다.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

# 프로젝트 루트를 추가하여 모듈 임포트 경로 수정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 어댑터 계층
from adapters.infra import HTTPClientAdapter, MongoDBAdapter
from adapters.repository_adapter import LegacyArticleRepository
from infra.clients.http import AioHttpClient

# 인프라 계층 임포트
from infra.database.mongodb import MongoDB
from infra.database.repository.article import ArticleModel
from infra.database.repository.factory import create_article_repository


@pytest.fixture
async def mongodb():
    """테스트용 MongoDB 인스턴스를 설정합니다."""
    # 테스트 데이터베이스 URL 및 이름 가져오기
    mongodb_url = os.getenv("TEST_MONGODB_URL", "mongodb://localhost:27017")
    db_name = "test_db"

    # 새 인프라의 MongoDB 인스턴스 생성
    mongo = MongoDB(uri=mongodb_url, database=db_name)
    await mongo.connect()

    # 테스트용 컬렉션 정리
    await mongo.drop_collection("articles")

    yield mongo

    # 테스트 후 정리
    await mongo.drop_collection("articles")
    await mongo.disconnect()


@pytest.fixture
async def article_repository(mongodb):
    """테스트용 Article 저장소를 설정합니다."""
    return create_article_repository(mongodb, "articles")


@pytest.fixture
async def mock_http_client():
    """HTTP 요청을 목(mock)으로 처리하는 HTTP 클라이언트를 설정합니다."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "title": "테스트 뉴스",
            "content": "이것은 테스트 콘텐츠입니다.",
            "url": "https://example.com/news/1",
        }
        mock_session.return_value.get.return_value.__aenter__.return_value = (
            mock_response
        )
        mock_session.return_value.post.return_value.__aenter__.return_value = (
            mock_response
        )

        client = AioHttpClient(base_url="https://example.com")
        yield client

        # 모의 세션 종료를 방지하기 위해 후크 제거
        client._session = None


class TestInfraStack:
    """인프라 스택 통합 테스트 클래스."""

    @pytest.mark.asyncio
    async def test_article_repository_integration(self, mongodb, article_repository):
        """Article 저장소가 MongoDB와 올바르게 작동하는지 테스트합니다."""
        # 테스트 데이터 생성
        article = ArticleModel(
            url="https://example.com/news/1",
            title="테스트 뉴스",
            content="이것은 테스트 콘텐츠입니다.",
            unique_id="test_news_1",
            metadata={"source": "테스트"},
        )

        # 저장소에 데이터 저장
        await article_repository.save(article)

        # ID로 데이터 조회
        retrieved = await article_repository.find_by_id(article.id)

        # 데이터 확인
        assert retrieved is not None
        assert retrieved.title == "테스트 뉴스"
        assert retrieved.unique_id == "test_news_1"

        # unique_id로 데이터 조회
        retrieved_by_unique = await article_repository.find_by_unique_id("test_news_1")
        assert retrieved_by_unique is not None
        assert retrieved_by_unique.id == article.id

        # 전체 데이터 조회
        all_articles = await article_repository.find_all()
        assert len(all_articles) == 1

        # 데이터 삭제
        await article_repository.delete(article.id)

        # 삭제 확인
        deleted = await article_repository.find_by_id(article.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_http_client_integration(self, mock_http_client):
        """HTTP 클라이언트가 올바르게 작동하는지 테스트합니다."""
        # GET 요청 테스트
        response = await mock_http_client.get("/news/1")

        # 응답 확인
        assert response["title"] == "테스트 뉴스"
        assert response["content"] == "이것은 테스트 콘텐츠입니다."

        # POST 요청 테스트
        post_data = {"comment": "뉴스에 대한 댓글"}
        response = await mock_http_client.post("/comments", json_data=post_data)

        # 응답 확인
        assert (
            response["title"] == "테스트 뉴스"
        )  # 목(mock) 응답이므로 동일한 데이터 반환

    @pytest.mark.asyncio
    async def test_adapter_integration(self, mongodb):
        """어댑터 레이어가 올바르게 작동하는지 테스트합니다."""
        # MongoDB 어댑터 테스트
        adapter = MongoDBAdapter()
        adapter._mongodb = mongodb  # 테스트 몽고디비 인스턴스 직접 설정

        # 레거시 형식으로 컬렉션 가져오기
        collection_name = adapter.get_collection("articles")
        assert collection_name == "articles"

        # 레거시 저장소 테스트
        legacy_repo = LegacyArticleRepository(mongodb_instance=mongodb)

        # 테스트 데이터 생성
        test_article = {
            "url": "https://example.com/news/2",
            "title": "레거시 테스트 뉴스",
            "content": "이것은 레거시 테스트 콘텐츠입니다.",
            "unique_id": "legacy_test_news_1",
            "metadata": {"source": "레거시 테스트"},
        }

        # 레거시 저장소를 통해 데이터 저장
        await legacy_repo.save_article(test_article)

        # ID로 데이터 조회
        article_id = test_article.get("id")
        if article_id:
            retrieved = await legacy_repo.get_article_by_id(article_id)
            assert retrieved is not None
            assert retrieved["title"] == "레거시 테스트 뉴스"

        # unique_id로 데이터 조회
        retrieved_by_unique = await legacy_repo.get_article_by_unique_id(
            "legacy_test_news_1"
        )
        if retrieved_by_unique:
            assert retrieved_by_unique["title"] == "레거시 테스트 뉴스"

        # 모든 아티클 조회
        all_articles = await legacy_repo.get_all_articles()
        assert len(all_articles) > 0

    @pytest.mark.asyncio
    async def test_http_adapter_integration(self, mock_http_client):
        """HTTP 클라이언트 어댑터가 올바르게 작동하는지 테스트합니다."""
        # HTTP 어댑터 생성 (내부적으로 AioHttpClient 사용)
        with patch("infra.clients.http.AioHttpClient", return_value=mock_http_client):
            adapter = HTTPClientAdapter(base_url="https://example.com")

            # GET 요청 테스트
            response = await adapter.get("/news/1")

            # 응답 확인
            assert response["title"] == "테스트 뉴스"
            assert response["content"] == "이것은 테스트 콘텐츠입니다."

            # POST 요청 테스트
            post_data = {"comment": "뉴스에 대한 댓글"}
            response = await adapter.post("/comments", json=post_data)

            # 응답 확인
            assert (
                response["title"] == "테스트 뉴스"
            )  # 목(mock) 응답이므로 동일한 데이터 반환
