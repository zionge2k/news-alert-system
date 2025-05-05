"""
Infrastructure layer for external services and data access.

This module provides abstractions and implementations for database access,
HTTP clients, messaging clients, and more.
"""

from infra.clients.http import AioHttpClient, HttpClient
from infra.clients.messaging import DiscordClient, Message, MessagingClient
from infra.database import (
    ArticleModel,
    ArticleRepository,
    Database,
    MongoDB,
    create_article_repository,
    create_mongodb_connection,
)

__all__ = [
    # Database
    "Database",
    "MongoDB",
    "create_mongodb_connection",
    # Repository
    "ArticleModel",
    "ArticleRepository",
    "create_article_repository",
    # HTTP Client
    "HttpClient",
    "AioHttpClient",
    # Messaging Client
    "MessagingClient",
    "DiscordClient",
    "Message",
]
