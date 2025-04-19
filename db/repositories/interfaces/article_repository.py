"""
기사 저장소 인터페이스

이 모듈은 기사 데이터 저장소의 인터페이스를 정의합니다.
모든 기사 저장소 구현체는 이 인터페이스를 준수해야 합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.models.article import ArticleModel


class BaseArticleRepository(ABC):
    """
    기사 저장소의 인터페이스를 정의하는 추상 기본 클래스
    """

    @abstractmethod
    async def save_article(self, article: ArticleModel) -> Any:
        """
        기사를 저장소에 저장합니다.

        Args:
            article: 저장할 기사 모델

        Returns:
            저장된 기사의 식별자
        """
        pass

    @abstractmethod
    async def find_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """
        특정 플랫폼의 기사를 조회합니다.

        Args:
            platform: 조회할 플랫폼 이름

        Returns:
            해당 플랫폼의 기사 목록
        """
        pass

    @abstractmethod
    async def find_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        키워드가 포함된 기사를 조회합니다.

        Args:
            keyword: 검색할 키워드

        Returns:
            키워드를 포함하는 기사 목록
        """
        pass

    @abstractmethod
    async def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        URL로 기사를 조회합니다.

        Args:
            url: 검색할 기사의 URL

        Returns:
            URL에 해당하는 기사 또는 None
        """
        pass

    @abstractmethod
    async def find_by_unique_id(self, unique_id: str) -> Optional[Dict[str, Any]]:
        """
        복합키(unique_id)로 기사를 조회합니다.

        Args:
            unique_id: 검색할 기사의 unique_id (platform_article_id 형식)

        Returns:
            unique_id에 해당하는 기사 또는 None
        """
        pass

    @abstractmethod
    async def find_by_platform_and_article_id(
        self, platform: str, article_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        플랫폼과 기사ID 조합으로 기사를 조회합니다.

        Args:
            platform: 검색할 플랫폼 이름
            article_id: 검색할 기사의 ID

        Returns:
            해당 조합에 맞는 기사 또는 None
        """
        pass
