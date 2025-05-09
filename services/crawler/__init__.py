"""
뉴스 크롤러 모듈
다양한 뉴스 소스에서 뉴스를 수집하는 크롤러 구현
"""

from services.crawler.base import BaseCrawler
from services.crawler.factory import create_crawler_registry, default_registry
from services.crawler.registry import CrawlerRegistry

__all__ = [
    "BaseCrawler",
    "CrawlerRegistry",
    "default_registry",
    "create_crawler_registry",
]
