"""
인프라 계층 - 데이터베이스, 외부 API 클라이언트 등 인프라 관련 모듈.

이 패키지는 애플리케이션의 인프라 요소(데이터베이스, HTTP 클라이언트 등)에 대한
추상화 인터페이스와 구체적인 구현을 제공합니다.
"""

from infra.clients.http import AioHttpClient, HttpClient
from infra.clients.messaging import DiscordClient, Message, MessagingClient
from infra.database import (
    MongoDB,
    MongoRepository,
    Repository,
    create_mongodb_connection,
)

__all__ = [
    "MongoDB",
    "create_mongodb_connection",
    "Repository",
    "MongoRepository",
    "HttpClient",
    "AioHttpClient",
    "MessagingClient",
    "DiscordClient",
    "Message",
]
