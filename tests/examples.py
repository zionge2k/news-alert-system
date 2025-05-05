"""
테스트 헬퍼와 픽스처 사용 예제

이 파일은 테스트 작성을 위한 예제 코드를 제공합니다.
실제 테스트가 아니라 사용법을 보여주는 예시 코드입니다.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.crawler.base import BaseNewsCrawler
from app.models.article import ArticleModel

# 헬퍼 및 유틸리티 임포트
from tests.helpers import dummy_article_dto, load_test_data, random_datetime
from tests.unit.crawler.utils import MockNewsCrawler, mock_html_response
from tests.unit.models.utils import create_mock_article_model, insert_mock_articles

###############################################
# 1. 기본 단위 테스트 예제
###############################################


@pytest.mark.unit
def test_basic_example():
    """기본 단위 테스트 예제"""
    # 테스트할 값 설정
    test_value = "테스트"

    # 검증
    assert test_value == "테스트"
    assert len(test_value) == 3


###############################################
# 2. 더미 데이터 생성 예제
###############################################


@pytest.mark.unit
def test_dummy_data_example():
    """더미 데이터 생성 예제"""
    # 기본 더미 기사 생성
    article = dummy_article_dto()

    # 검증
    assert article.title is not None
    assert article.url is not None
    assert article.metadata.platform is not None

    # 커스텀 더미 기사 생성
    custom_article = dummy_article_dto(title="커스텀 제목", author="커스텀 작성자")

    # 검증
    assert custom_article.title == "커스텀 제목"
    assert custom_article.author == "커스텀 작성자"


###############################################
# 3. MongoDB 모킹 예제
###############################################


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mongodb_mock_example(mock_mongodb):
    """MongoDB 모킹 예제"""
    # 클라이언트 모의 객체 가져오기
    mock_client = mock_mongodb.return_value

    # DB 및 컬렉션 모의 객체 설정
    mock_db = mock_client["test_db"]
    mock_collection = mock_db["articles"]

    # 모의 객체 메서드 호출
    await mock_collection.insert_one({"test": "data"})
    await mock_collection.find_one({"test": "data"})

    # 호출 검증
    mock_collection.insert_one.assert_called_once()
    mock_collection.find_one.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_article_collection_mock_example(mock_article_collection):
    """향상된 기사 컬렉션 모킹 예제"""
    # 모의 컬렉션에 테스트 문서 추가
    test_doc = {
        "title": "테스트 제목",
        "url": "https://example.com/test",
        "unique_id": "TEST_123",
        "metadata": {"platform": "TEST"},
    }

    await mock_article_collection.insert_one(test_doc)

    # 문서 검색
    found_doc = await mock_article_collection.find_one({"unique_id": "TEST_123"})

    # 검증
    assert found_doc is not None
    assert found_doc["title"] == "테스트 제목"

    # 모든 문서 가져오기
    all_docs = mock_article_collection.get_all_docs()
    assert len(all_docs) == 1


###############################################
# 4. HTTP 요청 모킹 예제
###############################################


@pytest.mark.unit
@pytest.mark.asyncio
async def test_http_response_mock_example(mock_http_response):
    """HTTP 응답 모킹 예제"""
    # 모의 응답 생성
    response = mock_http_response(
        json_data={"items": [{"title": "테스트 뉴스"}]}, status=200
    )

    # 비동기 메서드 호출
    async with response as resp:
        json_data = await resp.json()

    # 검증
    assert json_data["items"][0]["title"] == "테스트 뉴스"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aiohttp_client_mock_example(mock_aiohttp_client):
    """aiohttp 클라이언트 모킹 예제"""
    # 특정 URL에 대한 응답 설정
    test_url = "https://api.example.com/news"
    test_data = {"items": [{"title": "커스텀 테스트 뉴스"}]}

    mock_aiohttp_client.set_response(test_url, test_data)

    # 요청 실행
    async with mock_aiohttp_client as session:
        async with session.get(test_url) as response:
            data = await response.json()

    # 검증
    assert data["items"][0]["title"] == "커스텀 테스트 뉴스"


###############################################
# 5. 크롤러 모킹 예제
###############################################


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_crawler_example():
    """모의 크롤러 예제"""
    # 테스트 기사 준비
    test_article = dummy_article_dto()

    # 모의 크롤러 생성
    mock_crawler = MockNewsCrawler(articles=[test_article])

    # 크롤러 실행
    result = await mock_crawler.fetch_articles()

    # 검증
    assert mock_crawler.fetch_called is True
    assert len(result) == 1
    assert result[0].title == test_article.title


###############################################
# 6. 통합 테스트 예제
###############################################


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crawler_to_db_integration(mock_aiohttp_client, mock_article_collection):
    """크롤러에서 DB까지의 통합 테스트 예제"""
    # 1. 크롤러 응답 설정
    test_url = "https://api.example.com/news"
    test_data = {
        "items": [
            {
                "title": "통합 테스트 뉴스",
                "link": "https://example.com/integration-test",
                "description": "통합 테스트를 위한 뉴스 데이터입니다.",
                "pubDate": "2023-01-01T00:00:00+09:00",
            }
        ]
    }

    mock_aiohttp_client.set_response(test_url, test_data)

    # 2. 크롤러 호출 (실제 로직은 구현에 따라 다를 수 있음)
    with patch("app.crawler.mock.MockCrawler.fetch_articles") as mock_fetch:
        # 모의 기사 생성
        article = dummy_article_dto(
            title="통합 테스트 뉴스", url="https://example.com/integration-test"
        )
        mock_fetch.return_value = [article]

        # 크롤러 호출 (이 부분은 실제 코드에 따라 달라짐)
        # crawler = MockCrawler()
        # articles = await crawler.fetch_articles()
        articles = [article]  # 임시로 직접 설정

    # 3. DB 저장 및 검증
    for article in articles:
        model = ArticleModel.from_article_dto(article)
        await mock_article_collection.insert_one(model.to_document())

    # 4. DB에서 조회 및 검증
    saved_article = await mock_article_collection.find_one(
        {"title": "통합 테스트 뉴스"}
    )
    assert saved_article is not None
    assert saved_article["url"] == "https://example.com/integration-test"


###############################################
# 7. 더미 기사 픽스처 사용 예제
###############################################


@pytest.mark.unit
def test_dummy_articles_fixture_example(dummy_articles):
    """더미 기사 픽스처 사용 예제"""
    # 3개의 기본 더미 기사 생성
    articles = dummy_articles()
    assert len(articles) == 3

    # 5개의 더미 기사 생성, 플랫폼 지정
    custom_articles = dummy_articles(5, "CUSTOM")
    assert len(custom_articles) == 5
    assert custom_articles[0].metadata.platform == "CUSTOM"
