"""
BaseNewsCrawler 추상 클래스 테스트.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.crawler.base import Article, BaseNewsCrawler


@pytest.mark.unit
class TestBaseNewsCrawler:
    """BaseNewsCrawler 클래스 테스트."""

    def test_base_crawler_is_abstract(self):
        """BaseNewsCrawler가 추상 클래스인지 확인하는 테스트."""
        # 추상 클래스는 직접 인스턴스화할 수 없음
        with pytest.raises(TypeError):
            BaseNewsCrawler()

    def test_article_dictionary(self):
        """Article 클래스가 딕셔너리로 동작하는지 확인하는 테스트."""
        article = Article()
        article["title"] = "테스트 제목"
        article["link"] = "https://example.com/test"

        assert article["title"] == "테스트 제목"
        assert article["link"] == "https://example.com/test"
