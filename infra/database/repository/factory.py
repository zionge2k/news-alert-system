"""
Repository factory module for creating repository instances.
"""

from typing import Any, Dict, Optional, Type, TypeVar

from infra.database.base import Database
from infra.database.mongodb import MongoDB
from infra.database.repository import ArticleRepository
from infra.database.repository.mongodb import MongoArticleRepository

T = TypeVar("T")


def create_article_repository(
    database: Database, collection_name: str = "articles"
) -> ArticleRepository:
    """
    Create an ArticleRepository instance based on the database type.

    Args:
        database: The database instance
        collection_name: The name of the collection to use for articles

    Returns:
        An implementation of ArticleRepository appropriate for the database

    Raises:
        ValueError: If the database type is not supported
    """
    if isinstance(database, MongoDB):
        return MongoArticleRepository(database, collection_name)
    else:
        raise ValueError(f"Unsupported database type: {type(database).__name__}")
