"""
Article repository interface.

This module defines the interface for article data repositories.
All article repository implementations must adhere to this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class ArticleModel(BaseModel):
    """Base article model with common fields."""

    id: Optional[str] = None
    url: str
    title: str
    content: str
    unique_id: str
    metadata: Dict[str, Any]


class ArticleRepository(ABC):
    """
    Interface for article repositories.
    Defines the specific methods for article-related operations.
    """

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[ArticleModel]:
        """
        Find an article by its ID.

        Args:
            id: The ID of the article to find

        Returns:
            The article if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_all(self) -> List[ArticleModel]:
        """
        Find all articles.

        Returns:
            A list of all articles
        """
        pass

    @abstractmethod
    async def find_by(self, criteria: Dict[str, Any]) -> List[ArticleModel]:
        """
        Find articles matching the given criteria.

        Args:
            criteria: Dictionary of field name to value mappings to match

        Returns:
            A list of articles matching the criteria
        """
        pass

    @abstractmethod
    async def save(self, article: ArticleModel) -> ArticleModel:
        """
        Save an article (create or update).

        Args:
            article: The article to save

        Returns:
            The saved article with any updates (e.g., generated ID)
        """
        pass

    @abstractmethod
    async def save_all(self, articles: List[ArticleModel]) -> List[ArticleModel]:
        """
        Save multiple articles.

        Args:
            articles: The articles to save

        Returns:
            The saved articles with any updates
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        """
        Delete an article by its ID.

        Args:
            id: The ID of the article to delete
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Count all articles.

        Returns:
            The number of articles
        """
        pass

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
