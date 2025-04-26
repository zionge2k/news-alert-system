from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import discord

from app.schemas.article import ArticleDTO, ArticleMetadata

# 타입 변수 정의
T = TypeVar("T", bound=ArticleMetadata)


class MessageFormatter(ABC, Generic[T]):
    """
    메시지 포맷팅 인터페이스

    뉴스 알림 메시지를 포맷팅하는 기능을 제공합니다.
    """

    @abstractmethod
    def create_embed(self, article: ArticleDTO[T]) -> discord.Embed:
        """
        임베드 메시지를 생성합니다.

        Args:
            article: 뉴스 기사

        Returns:
            discord.Embed: 생성된 임베드
        """
        pass
