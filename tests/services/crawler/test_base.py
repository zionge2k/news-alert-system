from unittest.mock import MagicMock

import pytest

from services.crawler.base import BaseCrawler


class TestCrawler(BaseCrawler):
    """테스트용 크롤러 구현체"""

    def fetch(self):
        raise NotImplementedError

    def parse(self, html):
        raise NotImplementedError


def test_basecrawler_abstract_methods():
    """BaseCrawler의 추상 메서드가 구현되지 않으면 에러가 발생하는지 테스트"""
    crawler = TestCrawler()
    with pytest.raises(NotImplementedError):
        crawler.fetch()
    with pytest.raises(NotImplementedError):
        crawler.parse("")


def test_basecrawler_workflow(monkeypatch):
    """BaseCrawler의 기본 워크플로우가 올바르게 동작하는지 테스트"""
    crawler = TestCrawler()
    monkeypatch.setattr(crawler, "fetch", lambda: "<html>data</html>")
    monkeypatch.setattr(crawler, "parse", lambda html: {"title": "테스트"})
    result = crawler.crawl()
    assert result == {"title": "테스트"}
