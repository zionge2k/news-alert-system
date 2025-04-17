from abc import ABC, abstractmethod
from typing import Any, List, TypeVar

from app.schemas.article import ArticleDTO, ArticleMetadata

# ArticleMetadata를 상속받는 타입을 위한 타입 변수
T = TypeVar("T", bound=ArticleMetadata)


class Article(dict):
    """단순한 딕셔너리지만 명시적으로 타입 이름 부여"""

    title: str
    link: str


class BaseNewsCrawler(ABC):
    """
    모든 뉴스 크롤러가 반드시 구현해야 하는 기본 구조
    """

    @abstractmethod
    async def fetch_articles(self) -> List[ArticleDTO[Any]]:
        """
        뉴스 기사 목록을 수집
        """
        pass
