from services.crawler.jtbc.crawler import JTBCCrawler
from services.crawler.mbc.crawler import MBCCrawler
from services.crawler.registry import CrawlerRegistry
from services.crawler.ytn.crawler import YTNCrawler


def create_crawler_registry() -> CrawlerRegistry:
    """
    크롤러 레지스트리를 생성하고 기본 크롤러를 등록

    Returns:
        CrawlerRegistry: 초기화된 크롤러 레지스트리
    """
    registry = CrawlerRegistry()

    # 크롤러 등록
    registry.register("JTBC", JTBCCrawler)
    registry.register("MBC", MBCCrawler)
    registry.register("YTN", YTNCrawler)

    return registry


# 기본 크롤러 레지스트리 인스턴스
default_registry = create_crawler_registry()
