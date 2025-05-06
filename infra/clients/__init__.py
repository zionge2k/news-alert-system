"""Client interfaces and implementations for external services."""

from .http import AioHttpClient, HttpClient
from .messaging import DiscordClient, Message, MessagingClient

__all__ = [
    "HttpClient",
    "AioHttpClient",
    "MessagingClient",
    "DiscordClient",
    "Message",
]
