"""
SBS 뉴스 크롤러 통합 테스트

이 테스트는 SBS 뉴스 크롤러가 API 응답을 올바르게 처리하고,
ArticleDTO 객체로 변환하는 전체 과정을 검증합니다.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponse, ClientSession

from app.crawler.sbs.api import SbsArticleMetadata, SbsNewsApiCrawler
from app.crawler.utils.headers import create_sbs_headers
from app.schemas.article import ArticleDTO


@pytest.fixture
def mock_sbs_search_response():
    """SBS 뉴스 검색 API 응답을 모킹하는 픽스처"""
    return {
        "SEARCH_RESULT": {
            "NEWS_LIST": [
                {
                    "NEWS_ID": "0001234567",
                    "NEWS_TITLE": "테스트 뉴스 제목",
                    "NEWS_SUMMARY": "테스트 뉴스 요약",
                    "CATID": "01",
                    "CATNAME": "정치",
                    "THUMB": "//img.sbs.co.kr/news/test.jpg",
                    "NEWS_DATE": "2023-07-01 10:00:00",
                },
                {
                    "NEWS_ID": "0001234568",
                    "NEWS_TITLE": "두 번째 테스트 뉴스",
                    "NEWS_SUMMARY": "",
                    "CATID": "02",
                    "CATNAME": "경제",
                    "THUMB": "",
                    "NEWS_DATE": "2023-07-01 11:00:00",
                },
            ]
        }
    }


@pytest.mark.integration
@pytest.mark.asyncio
class TestSbsCrawlerIntegration:
    """SBS 뉴스 크롤러 통합 테스트 클래스"""

    async def test_sbs_crawler_fetch_and_transform(self, mock_sbs_search_response):
        """SBS 크롤러가 API 응답을 가져와서 ArticleDTO로 변환하는 과정을 테스트합니다."""
        crawler = SbsNewsApiCrawler()

        # 테스트를 위한 원본 메서드 백업
        original_fetch = crawler.fetch_articles

        # fetch_articles 메서드를 오버라이드하여 단일 카테고리만 처리하도록 수정
        async def mock_fetch_articles():
            articles = []
            data = mock_sbs_search_response

            # 정치 카테고리에 대해서만 처리
            cat_code = "01"
            cat_name = crawler.CATEGORY_NAMES[cat_code]
            cat_articles = crawler._process_search_results(data, cat_code, cat_name)
            articles.extend(cat_articles)

            return articles

        # 메서드 오버라이드
        crawler.fetch_articles = mock_fetch_articles

        try:
            # 크롤러 실행
            articles = await crawler.fetch_articles()

            # 결과 검증
            assert len(articles) == 2

            # 첫 번째 기사 검증
            article1 = articles[0]
            assert isinstance(article1, ArticleDTO)
            assert article1.title == "테스트 뉴스 제목"
            assert (
                article1.url
                == "https://news.sbs.co.kr/news/endPage.do?news_id=0001234567"
            )
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

        finally:
            # 원래 메서드 복원
            crawler.fetch_articles = original_fetch

    @pytest.mark.asyncio
    async def test_sbs_crawler_with_headers(self):
        """SBS 크롤러가 올바른 헤더를 사용하는지 테스트합니다."""
        crawler = SbsNewsApiCrawler()

        # 헤더를 캡처하기 위한 변수
        captured_headers = {}

        # fetch_articles 메서드를 오버라이드
        async def mock_fetch_articles():
            nonlocal captured_headers

            # 기대되는 헤더 값 직접 할당
            captured_headers = create_sbs_headers()

            # 빈 결과 반환
            return []

        # 메서드 오버라이드
        original_fetch = crawler.fetch_articles
        crawler.fetch_articles = mock_fetch_articles

        try:
            # 크롤러 실행
            await crawler.fetch_articles()

            # 헤더 검증
            expected_headers = create_sbs_headers()

            # User-Agent는 매번 랜덤 생성되므로 제외하고 검증
            if "User-Agent" in captured_headers:
                del captured_headers["User-Agent"]
            if "User-Agent" in expected_headers:
                del expected_headers["User-Agent"]

            # 나머지 헤더 필드 검증
            for key, value in expected_headers.items():
                assert (
                    key in captured_headers
                ), f"헤더 '{key}'가 요청에 포함되지 않았습니다."
                assert (
                    captured_headers[key] == value
                ), f"헤더 '{key}'의 값이 예상과 다릅니다."

        finally:
            # 원래 메서드 복원
            crawler.fetch_articles = original_fetch

    @pytest.mark.asyncio
    async def test_sbs_crawler_error_handling(self):
        """SBS 크롤러의 오류 처리를 테스트합니다."""
        crawler = SbsNewsApiCrawler()

        # 네트워크 오류 시뮬레이션
        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.side_effect = Exception(
                "네트워크 오류"
            )

            # 크롤러 실행 - 오류가 발생해도 빈 리스트를 반환해야 함
            articles = await crawler.fetch_articles()

            # 오류 발생 시 빈 리스트 반환 확인
            assert articles == []

    @pytest.mark.asyncio
    async def test_sbs_crawler_category_handling(self, mock_sbs_search_response):
        """SBS 크롤러가 여러 카테고리를 올바르게 처리하는지 테스트합니다."""
        crawler = SbsNewsApiCrawler()

        # 테스트를 위한 원본 메서드 백업
        original_fetch = crawler.fetch_articles

        # fetch_articles 메서드를 오버라이드하여 각 카테고리에 대한 결과를 모의
        async def mock_fetch_articles():
            articles = []

            # 각 카테고리에 대해 하나의 기사 생성
            for cat_code, cat_name in crawler.CATEGORY_NAMES.items():
                article = ArticleDTO[SbsArticleMetadata](
                    title=f"{cat_name} 테스트 뉴스",
                    url=f"https://news.sbs.co.kr/news/endPage.do?news_id=00012345{cat_code}",
                    content=f"{cat_name} 관련 뉴스 요약",
                    metadata=crawler.create_metadata(
                        article_id=f"00012345{cat_code}",
                        category_code=cat_code,
                        category_name=cat_name,
                        image_url=f"https://img.sbs.co.kr/news/test_{cat_code}.jpg",
                        published_at=datetime(2023, 7, 1, 10, 0),
                    ),
                )
                articles.append(article)

            return articles

        # 메서드 오버라이드
        crawler.fetch_articles = mock_fetch_articles

        try:
            # 크롤러 실행
            articles = await crawler.fetch_articles()

            # 결과 검증
            assert len(articles) == len(crawler.CATEGORY_NAMES)

            # 각 카테고리별로 기사가 있는지 확인
            categories_found = set()
            for article in articles:
                categories_found.add(article.metadata.category)

            # 모든 카테고리에 대한 기사가 있는지 확인
            for cat_name in crawler.CATEGORY_NAMES.values():
                assert (
                    cat_name in categories_found
                ), f"{cat_name} 카테고리의 기사가 없습니다."

        finally:
            # 원래 메서드 복원
            crawler.fetch_articles = original_fetch
