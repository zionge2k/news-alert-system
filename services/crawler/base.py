from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseCrawler(ABC):
    """
    뉴스 크롤러 기본 인터페이스
    모든 뉴스 크롤러는 이 클래스를 상속해야 함
    """

    @abstractmethod
    def fetch(self) -> str:
        """
        뉴스 소스에서 HTML 콘텐츠를 가져옴

        Returns:
            str: HTML 콘텐츠
        """
        pass

    @abstractmethod
    def parse(self, html: str) -> Dict[str, Any]:
        """
        HTML에서 뉴스 정보를 추출

        Args:
            html (str): 파싱할 HTML 콘텐츠

        Returns:
            Dict[str, Any]: 추출된 뉴스 정보 (제목, 내용, 출처, 게시일 등)
        """
        pass

    def crawl(self) -> Dict[str, Any]:
        """
        뉴스를 크롤링하는 기본 워크플로우

        Returns:
            Dict[str, Any]: 추출된 뉴스 정보
        """
        html = self.fetch()
        return self.parse(html)
