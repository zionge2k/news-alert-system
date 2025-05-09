from typing import Any, Dict, Type

from services.crawler.base import BaseCrawler


class CrawlerRegistry:
    """
    뉴스 크롤러 레지스트리
    다양한 뉴스 소스에 대한 크롤러 클래스를 등록하고 관리
    """

    def __init__(self):
        """
        크롤러 레지스트리 초기화
        """
        self._registry: Dict[str, Type[BaseCrawler]] = {}

    def register(self, source: str, crawler_cls: Type[BaseCrawler]) -> None:
        """
        뉴스 소스에 대한 크롤러 클래스 등록

        Args:
            source (str): 뉴스 소스 식별자 (예: 'JTBC', 'MBC')
            crawler_cls (Type[BaseCrawler]): BaseCrawler를 상속한 크롤러 클래스
        """
        self._registry[source] = crawler_cls

    def get(self, source: str) -> BaseCrawler:
        """
        뉴스 소스에 대한 크롤러 인스턴스 반환

        Args:
            source (str): 뉴스 소스 식별자

        Returns:
            BaseCrawler: 해당 뉴스 소스의 크롤러 인스턴스

        Raises:
            ValueError: 등록되지 않은 뉴스 소스인 경우
        """
        if source not in self._registry:
            raise ValueError(f"Unknown source: {source}")
        return self._registry[source]()
