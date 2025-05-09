"""
Repository factory module for creating repository instances.
"""

from typing import Any, Dict, Optional, Type, TypeVar

from infra.database.base import Database
from infra.database.mongodb import MongoDB, global_mongodb_instance
from infra.database.repository.article import ArticleRepository
from infra.database.repository.mongodb.article import MongoArticleRepository

T = TypeVar("T")


def create_article_repository(
    database: Optional[Database] = None, collection_name: str = "articles"
) -> ArticleRepository:
    """
    Create an ArticleRepository instance based on the database type.

    Args:
        database: The database instance. If None, use global_mongodb_instance.
        collection_name: The name of the collection to use for articles

    Returns:
        An implementation of ArticleRepository appropriate for the database

    Raises:
        ValueError: If the database type is not supported
    """
    # database가 None이면 전역 인스턴스 사용
    if database is None:
        database = global_mongodb_instance

    if database is None:
        raise ValueError(
            "No database instance provided and global_mongodb_instance is None"
        )

    if isinstance(database, MongoDB):
        return MongoArticleRepository(database, collection_name)
    else:
        raise ValueError(f"Unsupported database type: {type(database).__name__}")
