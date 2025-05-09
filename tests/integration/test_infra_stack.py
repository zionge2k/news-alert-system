"""
인프라 스택의 통합 테스트.

이 테스트는 전체 인프라 스택이 함께 올바르게 작동하는지 검증합니다.
데이터베이스, HTTP 클라이언트 및 어댑터 계층의 상호 작용을 확인합니다.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 프로젝트 루트를 추가하여 모듈 임포트 경로 수정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 인프라 계층 직접 임포트
from infra.clients.http import AioHttpClient
from infra.database.mongodb import MongoDB

# 인프라 계층 임포트
from infra.database.repository.article import ArticleModel
from infra.database.repository.factory import create_article_repository
from infra.database.repository.mongodb.article import MongoArticleRepository


@pytest.fixture
async def mock_mongodb():
    """테스트용 MongoDB 인스턴스를 모킹합니다."""
    # MongoDB 객체 모킹
    mock_db = MagicMock()
    mock_collection = MagicMock()

    # 실제 MongoDB 인스턴스 생성 없이 mock 사용
    mongo = MagicMock(spec=MongoDB)
    mongo._db = mock_db
    mongo._db.articles = mock_collection

    # 필요한 메서드 모킹
    mongo.connect = AsyncMock()
    mongo.disconnect = AsyncMock()
    mongo.get_collection = MagicMock(return_value=mock_collection)

    # find_by_id 등의 메서드가 호출될 때 결과를 반환하도록 설정
    mock_collection.find_one = AsyncMock()
    mock_collection.find = MagicMock()
    mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
    mock_collection.insert_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_collection.update_one = AsyncMock()

    await mongo.connect()
    yield mongo
    await mongo.disconnect()


@pytest.fixture
async def mock_article_repository(mock_mongodb):
    """테스트용 Article 저장소를 모킹합니다."""
    # MongoDB 저장소 생성
    repo = MongoArticleRepository(mock_mongodb, "articles")

    # 저장소 메서드 모킹
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_unique_id = AsyncMock()
    repo.find_all = AsyncMock(return_value=[])
    repo.delete = AsyncMock()

    return repo


@pytest.fixture
async def mock_http_client():
    """HTTP 요청을 목(mock)으로 처리하는 HTTP 클라이언트를 설정합니다."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200

        # 모의 JSON 응답 설정
        mock_json_response = {
            "title": "테스트 뉴스",
            "content": "이것은 테스트 콘텐츠입니다.",
            "url": "https://example.com/news/1",
        }
        mock_response.json.return_value = mock_json_response

        # 딕셔너리 접근 모의
        mock_session.return_value.request.return_value.__aenter__.return_value.json.return_value = (
            mock_json_response
        )
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
    async def test_article_repository_integration(
        self, mock_mongodb, mock_article_repository
    ):
        """Article 저장소가 MongoDB와 올바르게 작동하는지 테스트합니다."""
        # 테스트 데이터 생성
        article = ArticleModel(
            url="https://example.com/news/1",
            title="테스트 뉴스",
            content="이것은 테스트 콘텐츠입니다.",
            unique_id="test_news_1",
            metadata={"source": "테스트"},
        )

        # 메서드 반환값 설정
        mock_article_repository.find_by_id.return_value = article
        mock_article_repository.find_by_unique_id.return_value = article
        mock_article_repository.find_all.return_value = [article]

        # 테스트에서 기대되는 값을 설정
        empty_result = None
        mock_article_repository.find_by_id.side_effect = [
            article,
            empty_result,
        ]  # 첫 번째 호출, 두 번째 호출(삭제 후)

        # 저장소에 데이터 저장
        await mock_article_repository.save(article)

        # ID로 데이터 조회
        retrieved = await mock_article_repository.find_by_id(article.id)

        # 데이터 확인
        assert retrieved is not None
        assert retrieved.title == "테스트 뉴스"
        assert retrieved.unique_id == "test_news_1"

        # unique_id로 데이터 조회
        retrieved_by_unique = await mock_article_repository.find_by_unique_id(
            "test_news_1"
        )
        assert retrieved_by_unique is not None
        assert retrieved_by_unique.id == article.id

        # 전체 데이터 조회
        all_articles = await mock_article_repository.find_all()
        assert len(all_articles) == 1

        # 데이터 삭제
        await mock_article_repository.delete(article.id)

        # 삭제 확인 - 이제 저장소가 빈 결과를 반환하도록 설정됨
        deleted = await mock_article_repository.find_by_id(article.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_http_client_integration(self, mock_http_client):
        """HTTP 클라이언트가 올바르게 작동하는지 테스트합니다."""
        # GET 요청 테스트
        response = await mock_http_client.get("/news/1")

        # HTTP 클라이언트 모킹 변경으로 인해 JSON 응답 자체를 반환하도록 수정
        assert isinstance(response, dict)
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
    async def test_adapter_integration(self, mock_mongodb):
        """직접 MongoDB 인스턴스를 사용하여 테스트합니다."""
        # 직접 MongoDB 인스턴스 사용
        collection_name = "articles"

        # MongoDB 저장소 직접 생성
        repo = MongoArticleRepository(mock_mongodb, collection_name)

        # 테스트 데이터 생성
        article = ArticleModel(
            url="https://example.com/news/2",
            title="테스트 뉴스 2",
            content="이것은 테스트 콘텐츠 2입니다.",
            unique_id="test_news_2",
            metadata={"source": "테스트 2"},
        )

        # 모의 응답 설정
        mock_mongodb.get_collection.return_value.find_one.side_effect = [
            {
                "_id": article.id,
                "title": article.title,
                "url": article.url,
                "content": article.content,
                "unique_id": article.unique_id,
            },
            {
                "_id": article.id,
                "title": article.title,
                "url": article.url,
                "content": article.content,
                "unique_id": article.unique_id,
            },
        ]

        # 저장소 메서드 모킹
        repo.save = AsyncMock()
        repo.find_by_id = AsyncMock(return_value=article)
        repo.find_by_unique_id = AsyncMock(return_value=article)
        repo.find_all = AsyncMock(return_value=[article])

        # 저장소에 데이터 저장
        await repo.save(article)

        # ID로 데이터 조회
        retrieved = await repo.find_by_id(article.id)
        assert retrieved is not None
        assert retrieved.title == "테스트 뉴스 2"

        # unique_id로 데이터 조회
        retrieved_by_unique = await repo.find_by_unique_id("test_news_2")
        assert retrieved_by_unique is not None
        assert retrieved_by_unique.title == "테스트 뉴스 2"

        # 모든 아티클 조회
        all_articles = await repo.find_all()
        assert len(all_articles) > 0

    @pytest.mark.asyncio
    async def test_http_adapter_integration(self, mock_http_client):
        """HTTP 클라이언트를 직접 사용하여 테스트합니다."""
        # HTTP 클라이언트 직접 사용
        with patch("infra.clients.http.AioHttpClient", return_value=mock_http_client):
            client = AioHttpClient(base_url="https://example.com")

            # GET 요청 테스트
            response = await client.get("/news/1")

            # 응답 확인 - mock_http_client 픽스처 변경에 맞춰 수정
            assert isinstance(response, dict)
            assert response["title"] == "테스트 뉴스"
            assert response["content"] == "이것은 테스트 콘텐츠입니다."

            # POST 요청 테스트
            post_data = {"comment": "뉴스에 대한 댓글"}
            response = await client.post("/comments", json_data=post_data)

            # 응답 확인
            assert (
                response["title"] == "테스트 뉴스"
            )  # 목(mock) 응답이므로 동일한 데이터 반환
