"""Repository module for data access."""

from infra.database.repository.article import ArticleModel, ArticleRepository
from infra.database.repository.factory import create_article_repository

__all__ = ["ArticleModel", "ArticleRepository", "create_article_repository"]
