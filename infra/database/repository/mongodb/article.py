"""
MongoDB implementation of ArticleRepository.
"""

from typing import Any, Dict, List, Optional, Type

from infra.database.mongodb import MongoDB
from infra.database.repository import ArticleModel, ArticleRepository
from infra.database.repository.article import ArticleModel


class MongoArticleRepository(ArticleRepository):
    """
    MongoDB implementation of ArticleRepository.
    Uses the MongoDB client to store and retrieve article data.
    """

    def __init__(self, database: MongoDB, collection_name: str = "articles"):
        """
        Initialize the repository with a MongoDB connection.

        Args:
            database: MongoDB database instance
            collection_name: The name of the collection to use for articles
        """
        super().__init__(database, collection_name, ArticleModel)

    async def find_by_platform(self, platform: str) -> List[ArticleModel]:
        """
        Find articles by platform.

        Args:
            platform: The platform name to search for

        Returns:
            A list of articles from the specified platform
        """
        docs = await self.db.find(self.collection_name, {"metadata.platform": platform})
        return [ArticleModel.model_validate(doc) for doc in docs]

    async def find_by_keyword(self, keyword: str) -> List[ArticleModel]:
        """
        Find articles containing the keyword.

        Args:
            keyword: The keyword to search for

        Returns:
            A list of articles containing the keyword
        """
        docs = await self.db.find(self.collection_name, {"$text": {"$search": keyword}})
        return [ArticleModel.model_validate(doc) for doc in docs]

    async def find_by_url(self, url: str) -> Optional[ArticleModel]:
        """
        Find an article by its URL.

        Args:
            url: The URL to search for

        Returns:
            The article with the specified URL or None if not found
        """
        doc = await self.db.find_one(self.collection_name, {"url": url})
        return ArticleModel.model_validate(doc) if doc else None

    async def find_by_unique_id(self, unique_id: str) -> Optional[ArticleModel]:
        """
        Find an article by its unique ID.

        Args:
            unique_id: The unique ID to search for (typically in format "platform_article_id")

        Returns:
            The article with the specified unique ID or None if not found
        """
        doc = await self.db.find_one(self.collection_name, {"unique_id": unique_id})
        return ArticleModel.model_validate(doc) if doc else None

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
        unique_id = f"{platform}_{article_id}"
        return await self.find_by_unique_id(unique_id)
