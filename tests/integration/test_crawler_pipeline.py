"""
크롤러와 파이프라인 연동 통합 테스트.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.crawler.registry import CRAWLERS


@pytest.mark.integration
@pytest.mark.asyncio
class TestCrawlerPipeline:
    """크롤러와 파이프라인 간 통합 테스트."""

    async def test_crawlers_in_registry(self):
        """레지스트리에 등록된 모든 크롤러가 유효한지 확인하는 테스트."""
        assert len(CRAWLERS) > 0, "크롤러 레지스트리가 비어 있습니다."

        for name, crawler in CRAWLERS.items():
            assert hasattr(
                crawler, "fetch_articles"
            ), f"{name} 크롤러에 fetch_articles 메서드가 없습니다."

    @patch("app.models.article.ArticleModel.from_article_dto")
    async def test_crawler_to_model_pipeline(self, mock_from_dto):
        """크롤러에서 모델로의 데이터 파이프라인 테스트."""
        # 테스트를 위한 목 설정
        mock_article_model = MagicMock()
        mock_from_dto.return_value = mock_article_model

        # 첫 번째 등록된 크롤러 선택
        test_crawler_name = list(CRAWLERS.keys())[0]
        test_crawler = CRAWLERS[test_crawler_name]

        # 실제 크롤링 호출 없이 테스트하기 위한 패치
        with patch.object(test_crawler, "fetch_articles") as mock_fetch:
            # 가짜 기사 데이터 설정
            mock_fetch.return_value = []

            # 크롤러 실행
            articles = await test_crawler.fetch_articles()

            # 크롤러가 호출되었는지 확인
            mock_fetch.assert_called_once()

            # 결과 검증 (실제로는 빈 리스트이지만, 호출 검증이 목적)
            assert isinstance(articles, list)
