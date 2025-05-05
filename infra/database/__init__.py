"""Database module for data storage and retrieval."""

from infra.database.base import Database
from infra.database.mongodb import MongoDB, create_mongodb_connection
from infra.database.repository import (
    ArticleModel,
    ArticleRepository,
    create_article_repository,
)

__all__ = [
    "Database",
    "MongoDB",
    "create_mongodb_connection",
    "ArticleModel",
    "ArticleRepository",
    "create_article_repository",
]
