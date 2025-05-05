"""
Repository adapter module for backward compatibility.

This module provides adapters for the new repository interfaces to be used with existing code.
It ensures a smooth transition from the old database layer to the new infrastructure layer.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from app.models.article import ArticleModel as AppArticleModel
from infra.database.mongodb import MongoDB
from infra.database.repository import ArticleModel, create_article_repository

logger = logging.getLogger(__name__)


class LegacyArticleRepository:
    """
    Adapter for the new ArticleRepository interface to maintain compatibility with existing code.
    This class emulates the old BaseArticleRepository interface while using the new infrastructure.
    """

    def __init__(self, mongodb_instance: Optional[MongoDB] = None):
        """
        Initialize the adapter with a MongoDB instance.

        Args:
            mongodb_instance: The MongoDB instance to use. If None, a new connection will be created.
        """
        if mongodb_instance is None:
            # Use default connection from env vars
            from infra.database.mongodb import create_mongodb_connection

            self._mongodb = create_mongodb_connection()
        else:
            self._mongodb = mongodb_instance

        # Create the actual repository
        self._repository = create_article_repository(self._mongodb)

    async def save_article(self, article: AppArticleModel) -> Any:
        """
        Save an article to the repository.

        Args:
            article: The article model to save

        Returns:
            The ID of the saved article
        """
        # Convert from app model to infrastructure model
        infra_article = ArticleModel(
            id=getattr(article, "id", None),
            url=article.url,
            title=article.title,
            content=article.content,
            unique_id=article.unique_id,
            metadata=article.metadata,
        )

        # Save using the new repository
        saved_article = await self._repository.save(infra_article)
        return saved_article.id

    async def find_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """
        Find articles by platform.

        Args:
            platform: The platform name to search for

        Returns:
            A list of articles from the specified platform
        """
        articles = await self._repository.find_by_platform(platform)
        # Convert to dict for compatibility with old code
        return [article.model_dump() for article in articles]

    async def find_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Find articles containing the keyword.

        Args:
            keyword: The keyword to search for

        Returns:
            A list of articles containing the keyword
        """
        articles = await self._repository.find_by_keyword(keyword)
        # Convert to dict for compatibility with old code
        return [article.model_dump() for article in articles]

    async def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Find an article by its URL.

        Args:
            url: The URL to search for

        Returns:
            The article with the specified URL or None if not found
        """
        article = await self._repository.find_by_url(url)
        return article.model_dump() if article else None

    async def find_by_unique_id(self, unique_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an article by its unique ID.

        Args:
            unique_id: The unique ID to search for

        Returns:
            The article with the specified unique ID or None if not found
        """
        article = await self._repository.find_by_unique_id(unique_id)
        return article.model_dump() if article else None

    async def find_by_platform_and_article_id(
        self, platform: str, article_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find an article by platform and article ID combination.

        Args:
            platform: The platform name
            article_id: The article ID within that platform

        Returns:
            The article matching the platform and article ID or None if not found
        """
        article = await self._repository.find_by_platform_and_article_id(
            platform, article_id
        )
        return article.model_dump() if article else None


# Create a singleton instance for backward compatibility
article_repository = LegacyArticleRepository()
