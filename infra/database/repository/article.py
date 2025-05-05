"""
Article repository interface.

This module defines the interface for article data repositories.
All article repository implementations must adhere to this interface.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from infra.database.repository import Repository


class ArticleModel(BaseModel):
    """Base article model with common fields."""

    id: Optional[str] = None
    url: str
    title: str
    content: str
    unique_id: str
    metadata: Dict[str, Any]


class ArticleRepository(Repository[ArticleModel, str]):
    """
    Interface for article repositories.
    Extends the generic Repository interface with article-specific methods.
    """

    @abstractmethod
    async def find_by_platform(self, platform: str) -> List[ArticleModel]:
        """
        Find articles by platform.

        Args:
            platform: The platform name to search for

        Returns:
            A list of articles from the specified platform
        """
        pass

    @abstractmethod
    async def find_by_keyword(self, keyword: str) -> List[ArticleModel]:
        """
        Find articles containing the keyword.

        Args:
            keyword: The keyword to search for

        Returns:
            A list of articles containing the keyword
        """
        pass

    @abstractmethod
    async def find_by_url(self, url: str) -> Optional[ArticleModel]:
        """
        Find an article by its URL.

        Args:
            url: The URL to search for

        Returns:
            The article with the specified URL or None if not found
        """
        pass

    @abstractmethod
    async def find_by_unique_id(self, unique_id: str) -> Optional[ArticleModel]:
        """
        Find an article by its unique ID.

        Args:
            unique_id: The unique ID to search for (typically in format "platform_article_id")

        Returns:
            The article with the specified unique ID or None if not found
        """
        pass

    @abstractmethod
    async def find_by_platform_and_article_id(
        self, platform: str, article_id: str
    ) -> Optional[ArticleModel]:
        """
        Find an article by platform and article ID combination.

        Args:
            platform: The platform name
            article_id: The article ID within that platform

        Returns:
            The article matching the platform and article ID or None if not found
        """
        pass
