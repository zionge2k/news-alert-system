"""
크롤러 테스트를 위한 유틸리티 모듈입니다.
"""

import json
import os
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, patch

from app.crawler.base import Article, BaseNewsCrawler
from app.schemas.article import ArticleDTO, ArticleMetadata


class MockNewsCrawler(BaseNewsCrawler):
    """
    테스트용 목 뉴스 크롤러 구현체입니다.

    BaseNewsCrawler를 상속받아 간단한 테스트 구현을 제공합니다.
    """

    def __init__(self, articles: Optional[List[ArticleDTO]] = None):
        """
        MockNewsCrawler를 초기화합니다.

        Args:
            articles: 반환할 뉴스 기사 목록 (기본값: 빈 목록)
        """
        self.articles = articles or []
        self.fetch_called = False

    async def fetch_articles(self) -> List[ArticleDTO]:
        """
        뉴스 기사 목록을 반환합니다.

        Returns:
            설정된 뉴스 기사 목록
        """
        self.fetch_called = True
        return self.articles


def mock_html_response(file_name: str) -> str:
    """
    테스트용 HTML 응답을 파일에서 로드합니다.

    Args:
        file_name: 로드할 HTML 파일 이름 (tests/data/ 디렉토리 내의 파일)

    Returns:
        HTML 콘텐츠 문자열

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
    """
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
    )
    file_path = os.path.join(data_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"테스트 HTML 파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


async def mock_crawler_execution(crawler: BaseNewsCrawler) -> List[ArticleDTO]:
    """
    크롤러를 실행하고 결과를 반환하는 헬퍼 함수입니다.

    Args:
        crawler: 실행할 크롤러 인스턴스

    Returns:
        크롤링 결과 기사 목록
    """
    articles = await crawler.fetch_articles()
    return articles


def create_mock_response_for_crawler(
    url_pattern: str, response_data: Dict[str, Any], client_mock
) -> None:
    """
    특정 URL 패턴에 대한 모의 응답을 설정합니다.

    Args:
        url_pattern: 응답을 설정할 URL 패턴
        response_data: 응답으로 반환할 데이터
        client_mock: aiohttp 클라이언트 목 객체 (mock_aiohttp_client 픽스처에서 가져온 것)
    """
    client_mock.set_response(url_pattern, response_data)
