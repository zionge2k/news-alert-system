"""
크롤러 워크플로우 기능 테스트.
"""

import json
import os
from unittest.mock import patch

import pytest

from app.crawler.registry import CRAWLERS


@pytest.mark.functional
@pytest.mark.slow
class TestCrawlerWorkflow:
    """크롤러 전체 워크플로우 기능 테스트."""

    @pytest.fixture
    def mock_http_client(self, mock_http_response):
        """HTTP 클라이언트를 모킹하는 픽스처."""
        # 테스트 데이터 디렉토리에서 샘플 응답 불러오기
        sample_file = os.path.join(
            os.path.dirname(__file__), "../data/sample_news_response.json"
        )

        # 샘플 파일이 없으면 더미 데이터 사용
        if not os.path.exists(sample_file):
            response_data = {
                "items": [
                    {
                        "title": "테스트 뉴스 제목",
                        "link": "https://example.com/news/123",
                        "description": "테스트 뉴스 내용",
                        "pubDate": "2023-08-01T12:00:00+09:00",
                    }
                ]
            }
        else:
            with open(sample_file, "r", encoding="utf-8") as f:
                response_data = json.load(f)

        # 모킹된 응답 생성
        mock_response = mock_http_response(json_data=response_data, status=200)

        # ClientSession의 get, post 메서드를 모킹
        with (
            patch("aiohttp.ClientSession.get", return_value=mock_response),
            patch("aiohttp.ClientSession.post", return_value=mock_response),
        ):
            yield

    @pytest.mark.asyncio
    async def test_full_crawler_workflow(self, mock_http_client, mock_mongodb):
        """크롤링부터 저장까지 전체 워크플로우 테스트."""
        # 특정 크롤러 선택 (첫 번째 등록된 크롤러)
        test_crawler_name = list(CRAWLERS.keys())[0]
        test_crawler = CRAWLERS[test_crawler_name]

        # 크롤러 실행
        articles = await test_crawler.fetch_articles()

        # 결과 검증
        assert isinstance(articles, list), "크롤링 결과가 리스트가 아닙니다."

        # 크롤링 결과가 있는 경우만 추가 검증
        if articles:
            article = articles[0]
            assert hasattr(article, "title"), "기사에 제목이 없습니다."
            assert hasattr(article, "url"), "기사에 URL이 없습니다."
            assert hasattr(article, "metadata"), "기사에 메타데이터가 없습니다."
