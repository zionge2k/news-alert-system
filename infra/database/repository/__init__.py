"""Repository module for data access."""

from infra.database.repository.article import ArticleModel, ArticleRepository
from infra.database.repository.base import Repository
from infra.database.repository.factory import create_article_repository
from infra.database.repository.mongodb import MongoRepository

__all__ = [
    "Repository",
    "MongoRepository",
    "ArticleModel",
    "ArticleRepository",
    "create_article_repository",
]
