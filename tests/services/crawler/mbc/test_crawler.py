import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from services.crawler.mbc.crawler import MBCCrawler


@pytest.fixture
def sample_html():
    """샘플 HTML 생성"""
    return """
    <html><body>
    <div class="news-list">
        <li>
            <strong class="title">MBC 뉴스 제목</strong>
            <p class="text">MBC 본문 내용</p>
            <span class="time">2024-06-01 12:00</span>
            <a href="/news/article/2024060101.html">기사 링크</a>
        </li>
    </div>
    </body></html>
    """


@pytest.fixture
def crawler():
    """MBC 크롤러 인스턴스"""
    return MBCCrawler()


@patch("aiohttp.ClientSession.get")
async def test_fetch(mock_get, crawler):
    """fetch 메서드 테스트"""
    # Mock response 설정
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="<html>테스트 HTML</html>")
    mock_response.__aenter__.return_value = mock_response
    mock_get.return_value = mock_response

    # 테스트 실행
    html = await crawler.fetch()

    # 검증
    assert html == "<html>테스트 HTML</html>"
    mock_get.assert_called_once()


def test_parse(crawler, sample_html):
    """parse 메서드 테스트"""
    # 테스트 실행
    news = crawler.parse(sample_html)

    # 검증
    assert news.get("source") == "MBC"
    assert news.get("title") == "MBC 뉴스 제목"
    assert news.get("content") == "MBC 본문 내용"
    assert news.get("published_at") == "2024-06-01 12:00"
    assert "url" in news


@patch("services.crawler.mbc.crawler.MBCCrawler.fetch")
async def test_crawl(mock_fetch, crawler, sample_html):
    """crawl 메서드 테스트"""
    # Mock 설정
    mock_fetch.return_value = sample_html

    # 테스트 실행
    news = await crawler.crawl()

    # 검증
    assert news.get("source") == "MBC"
    assert news.get("title") == "MBC 뉴스 제목"
    assert news.get("content") == "MBC 본문 내용"
    mock_fetch.assert_called_once()


def test_extract_article_url(crawler):
    """_extract_article_url 메서드 테스트"""
    # 테스트 HTML 생성
    html = '<a href="/news/123"></a>'
    soup = BeautifulSoup(html, "html.parser")

    # 테스트 실행
    url = crawler._extract_article_url(soup)

    # 검증
    assert url == f"{crawler.base_url}/news/123"
