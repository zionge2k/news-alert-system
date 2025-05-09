import pytest

from services.crawler.base import BaseCrawler
from services.crawler.registry import CrawlerRegistry


def test_registry_register_and_get():
    """레지스트리에 크롤러를 등록하고 가져오는 기능 테스트"""
    registry = CrawlerRegistry()

    class DummyCrawler(BaseCrawler):
        def fetch(self):
            return "<html></html>"

        def parse(self, html):
            return {"title": "테스트"}

    registry.register("JTBC", DummyCrawler)
    crawler = registry.get("JTBC")
    assert isinstance(crawler, DummyCrawler)


def test_registry_unknown_source():
    """등록되지 않은 소스에 대해 예외가 발생하는지 테스트"""
    registry = CrawlerRegistry()
    with pytest.raises(ValueError):
        registry.get("MBC")
