import json
from datetime import datetime
from unittest import mock

import pytest
from aiohttp import ClientResponse

from app.crawler.sbs.api import SbsArticleMetadata, SbsNewsApiCrawler
from app.schemas.article import ArticleDTO


@pytest.fixture
def mock_sbs_response():
    """SBS 뉴스 API 응답을 모킹하는 픽스처"""
    return {
        "list": [
            {
                "news_id": "0001234567",
                "news_title": "테스트 뉴스 제목",
                "summary": "테스트 뉴스 요약",
                "catid": "01",
                "catname": "정치",
                "thumb": "//img.sbs.co.kr/news/test.jpg",
                "news_date": "2023-07-01 10:00:00",
            },
            {
                "news_id": "0001234568",
                "news_title": "두 번째 테스트 뉴스",
                "summary": "",
                "catid": "02",
                "catname": "경제",
                "thumb": "",
                "news_date": "2023-07-01 11:00:00",
            },
        ]
    }


@pytest.mark.asyncio
async def test_fetch_articles(mock_sbs_response):
    """SbsNewsApiCrawler.fetch_articles 메서드를 테스트합니다."""
    crawler = SbsNewsApiCrawler()

    # ClientSession.get 메서드를 모킹
    mock_response = mock.AsyncMock(spec=ClientResponse)
    mock_response.status = 200
    mock_response.text = mock.AsyncMock(return_value=json.dumps(mock_sbs_response))

    # aiohttp.ClientSession 모킹
    mock_session = mock.AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with mock.patch("aiohttp.ClientSession", return_value=mock_session):
        articles = await crawler.fetch_articles()

    # 결과 검증
    assert len(articles) == 2

    # 첫 번째 기사 검증
    article1 = articles[0]
    assert isinstance(article1, ArticleDTO)
    assert article1.title == "테스트 뉴스 제목"
    assert article1.url == "https://news.sbs.co.kr/news/endPage.do?news_id=0001234567"
    assert article1.content == "테스트 뉴스 요약"

    # 메타데이터 검증
    assert isinstance(article1.metadata, SbsArticleMetadata)
    assert article1.metadata.platform == "SBS"
    assert article1.metadata.category == "정치"
    assert article1.metadata.article_id == "0001234567"
    assert article1.metadata.category_code == "01"
    assert article1.metadata.image_url == "https://img.sbs.co.kr/news/test.jpg"

    # 두 번째 기사 검증
    article2 = articles[1]
    assert article2.title == "두 번째 테스트 뉴스"
    assert article2.content == ""  # 빈 요약
    assert article2.metadata.image_url is None  # 이미지 없음


@pytest.mark.asyncio
async def test_fetch_articles_http_error():
    """HTTP 오류 처리를 테스트합니다."""
    crawler = SbsNewsApiCrawler()

    # 실패하는 응답 모킹
    mock_response = mock.AsyncMock(spec=ClientResponse)
    mock_response.status = 404

    # aiohttp.ClientSession 모킹
    mock_session = mock.AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with mock.patch("aiohttp.ClientSession", return_value=mock_session):
        articles = await crawler.fetch_articles()

    # 오류 시 빈 리스트 반환 확인
    assert articles == []


@pytest.mark.asyncio
async def test_fetch_articles_json_error():
    """JSON 파싱 오류 처리를 테스트합니다."""
    crawler = SbsNewsApiCrawler()

    # 잘못된 JSON 응답 모킹
    mock_response = mock.AsyncMock(spec=ClientResponse)
    mock_response.status = 200
    mock_response.text = mock.AsyncMock(return_value="잘못된 JSON 형식")

    # aiohttp.ClientSession 모킹
    mock_session = mock.AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with mock.patch("aiohttp.ClientSession", return_value=mock_session):
        articles = await crawler.fetch_articles()

    # 오류 시 빈 리스트 반환 확인
    assert articles == []


@pytest.mark.asyncio
async def test_process_category_articles():
    """_process_category_articles 메서드를 테스트합니다."""
    crawler = SbsNewsApiCrawler()

    # 테스트 데이터
    test_data = {
        "list": [
            {
                "news_id": "0001234567",
                "news_title": "테스트 뉴스 제목",
                "summary": "테스트 뉴스 요약",
                "catid": "01",
                "catname": "정치",
                "thumb": "//img.sbs.co.kr/news/test.jpg",
                "news_date": "2023-07-01 10:00:00",
            }
        ]
    }
    category = {"code": "01", "name": "정치"}

    # 메서드 호출
    articles = await crawler._process_category_articles(test_data, category)

    # 결과 검증
    assert len(articles) == 1
    article = articles[0]
    assert article.title == "테스트 뉴스 제목"
    assert article.metadata.platform == "SBS"
    assert article.metadata.published_at.year == 2023
    assert article.metadata.published_at.month == 7
    assert article.metadata.published_at.day == 1
