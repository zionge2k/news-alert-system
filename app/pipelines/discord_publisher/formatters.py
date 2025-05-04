"""
Discord 메시지 포맷팅 모듈

이 모듈은 뉴스 기사를 Discord 메시지 형식으로 변환하는 기능을 제공합니다.
QueueItem에서 Discord Embed 객체를 생성하여 시각적으로 보기 좋은 메시지를 만듭니다.
"""

import datetime
from typing import Dict, List, Optional, Tuple, Union

import discord
from discord import Embed

from app.models.queue import QueueItem
from app.pipelines.discord_publisher.config import discord_settings
from common.utils.logger import get_logger

logger = get_logger(__name__)


class ArticleFormatter:
    """
    기사를 Discord 메시지로 포맷팅하는 클래스

    QueueItem을 Discord Embed 객체로 변환합니다.
    """

    @staticmethod
    def create_article_embed(queue_item: QueueItem) -> Embed:
        """
        기사 정보로 Discord Embed 객체를 생성합니다.

        Args:
            queue_item: 발행할 큐 아이템

        Returns:
            discord.Embed: 생성된 임베드 객체
        """
        try:
            # 기본 임베드 생성
            embed = Embed(
                title=queue_item.title,
                url=queue_item.url,
                description=ArticleFormatter._format_content(queue_item.content),
                color=discord_settings.EMBED_COLOR,
                timestamp=datetime.datetime.now(),
            )

            # 카테고리 추가
            if queue_item.category:
                embed.add_field(name="카테고리", value=queue_item.category, inline=True)

            # 플랫폼 추가
            if queue_item.platform:
                embed.add_field(name="출처", value=queue_item.platform, inline=True)

            # 썸네일 추가 (있는 경우)
            if getattr(queue_item, "thumbnail_url", None):
                embed.set_thumbnail(url=queue_item.thumbnail_url)

            # 푸터 추가
            embed.set_footer(text=discord_settings.FOOTER_TEXT)

            return embed

        except Exception as e:
            logger.error(f"임베드 생성 중 오류: {str(e)}")
            # 오류 발생 시 간단한 임베드 반환
            return Embed(
                title=queue_item.title,
                url=queue_item.url,
                description="[내용 로드 중 오류 발생]",
                color=0xFF0000,
            )

    @staticmethod
    def _format_content(content: Optional[str]) -> str:
        """
        기사 본문을 Discord 메시지에 맞게 포맷팅합니다.

        Args:
            content: 기사 본문

        Returns:
            str: 포맷팅된 본문
        """
        if not content:
            return "내용 없음"

        # 본문이 너무 길면 자르기
        max_length = 500
        if len(content) > max_length:
            return content[:max_length] + "..."

        return content

    @staticmethod
    def create_error_embed(
        error_message: str, queue_item: Optional[QueueItem] = None
    ) -> Embed:
        """
        오류 메시지 임베드를 생성합니다.

        Args:
            error_message: 오류 메시지
            queue_item: 관련 큐 아이템 (선택)

        Returns:
            discord.Embed: 오류 임베드
        """
        embed = Embed(
            title="⚠️ 발행 오류 발생",
            description=error_message,
            color=0xFF0000,
            timestamp=datetime.datetime.now(),
        )

        if queue_item:
            embed.add_field(name="기사 제목", value=queue_item.title, inline=False)
            embed.add_field(name="기사 URL", value=queue_item.url, inline=False)

        embed.set_footer(text=f"{discord_settings.FOOTER_TEXT} - 오류 로그")

        return embed
