"""
MongoDB implementation of ArticleRepository.
"""

from typing import Any, Dict, List, Optional, Type

from infra.database.mongodb import MongoDB
from infra.database.repository.article import ArticleModel, ArticleRepository


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
        self.db = database
        self.collection_name = collection_name

    async def find_by_id(self, id: str) -> Optional[ArticleModel]:
        """
        Find an article by its ID.

        Args:
            id: The ID of the article to find

        Returns:
            The article if found, None otherwise
        """
        doc = await self.db.find_one(self.collection_name, {"_id": id})
        if doc:
            return ArticleModel.model_validate(doc)
        return None

    async def find_all(self) -> List[ArticleModel]:
        """
        Find all articles.

        Returns:
            A list of all articles
        """
        docs = await self.db.find(self.collection_name, {})
        return [ArticleModel.model_validate(doc) for doc in docs]

    async def find_by(self, criteria: Dict[str, Any]) -> List[ArticleModel]:
        """
        Find articles matching the given criteria.

        Args:
            criteria: Dictionary of field name to value mappings to match

        Returns:
            A list of articles matching the criteria
        """
        docs = await self.db.find(self.collection_name, criteria)
        return [ArticleModel.model_validate(doc) for doc in docs]

    async def save(self, article: ArticleModel) -> ArticleModel:
        """
        Save an article (create or update).

        Args:
            article: The article to save

        Returns:
            The saved article with any updates (e.g., generated ID)
        """
        data = article.model_dump(exclude_unset=True)
        article_id = data.get("id") or data.get("_id")

        if article_id:
            # Update existing article
            await self.db.update(
                self.collection_name, {"_id": article_id}, {"$set": data}, upsert=True
            )
            data["id"] = article_id
        else:
            # Create new article
            result = await self.db.insert(self.collection_name, data)
            # Set the ID on the article if it's a string result
            if isinstance(result, str):
                data["id"] = result

        return ArticleModel.model_validate(data)

    async def save_all(self, articles: List[ArticleModel]) -> List[ArticleModel]:
        """
        Save multiple articles.

        Args:
            articles: The articles to save

        Returns:
            The saved articles with any updates
        """
        saved_articles = []
        for article in articles:
            saved_article = await self.save(article)
            saved_articles.append(saved_article)
        return saved_articles

    async def delete(self, id: str) -> None:
        """
        Delete an article by its ID.

        Args:
            id: The ID of the article to delete
        """
        await self.db.delete(self.collection_name, {"_id": id})

    async def count(self) -> int:
        """
        Count all articles.

        Returns:
            The number of articles
        """
        return await self.db.count(self.collection_name, {})

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
