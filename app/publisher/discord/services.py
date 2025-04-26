from datetime import datetime

import discord

from app.publisher.discord.interfaces import MessageFormatter
from app.schemas.article import ArticleDTO, ArticleMetadata
from common.utils.logger import get_logger

# 로거 설정
logger = get_logger(__name__)


class NewsEmbedFormatter(MessageFormatter[ArticleMetadata]):
    """
    뉴스 기사를 Discord 임베드로 포맷팅하는 클래스
    """

    def create_embed(self, article: ArticleDTO[ArticleMetadata]) -> discord.Embed:
        """
        뉴스 기사 임베드를 생성합니다.

        Args:
            article: 뉴스 기사

        Returns:
            discord.Embed: 생성된 임베드
        """
        # 발행 시간 포맷팅
        published_at = "알 수 없음"
        if article.metadata.published_at:
            published_at = article.metadata.published_at.strftime("%Y-%m-%d %H:%M")

        # 카테고리
        category = article.metadata.category or "미분류"

        # 임베드 생성
        embed = discord.Embed(
            title=article.title,
            description=(
                f"{article.content[:200]}..."
                if article.content and len(article.content) > 200
                else article.content
            ),
            url=article.url,
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        # 필드 추가
        embed.add_field(name="언론사", value=article.metadata.platform, inline=True)
        embed.add_field(name="카테고리", value=category, inline=True)
        embed.add_field(name="발행 시간", value=published_at, inline=True)

        # 푸터
        embed.set_footer(text="실시간 뉴스 알림")

        return embed
