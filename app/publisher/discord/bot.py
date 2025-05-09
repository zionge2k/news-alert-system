import os
from typing import List, Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

from app.publisher.discord.interfaces import MessageFormatter
from app.publisher.discord.services import NewsEmbedFormatter
from app.schemas.article import ArticleDTO, ArticleMetadata
from common.utils.logger import get_logger

# 직접 서비스 계층 임포트
from services.notifier import NotifierFactory

# 환경 변수 로드
load_dotenv()

# 로거 설정
logger = get_logger(__name__)


class NewsAlertBot(commands.Bot):
    """
    뉴스 알림을 위한 Discord 봇 클래스

    비동기 초기화와 이벤트 핸들링을 지원하는 봇 클래스입니다.
    """

    def __init__(
        self, command_prefix: str = "!", formatter: MessageFormatter | None = None
    ):
        """
        Discord 봇 초기화

        Args:
            command_prefix: 명령어 접두사 (기본값: "!")
            formatter: 메시지 포맷터 (기본값: None, 자동 생성)
        """
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
        )

        # 봇 토큰 확인
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        if not self.token:
            raise ValueError("DISCORD_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")

        # 메시지 포맷터 설정
        self.formatter = formatter or NewsEmbedFormatter()

        # 서비스 어댑터 대신 직접 Discord 알림 서비스 생성
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            self.discord_notifier = NotifierFactory.create(
                "discord", webhook_url=webhook_url
            )
        else:
            self.discord_notifier = None
            logger.warning(
                "DISCORD_WEBHOOK_URL이 설정되지 않아 webhook 알림 기능이 비활성화됩니다."
            )

    async def on_ready(self):
        """봇이 준비되었을 때 호출되는 이벤트 핸들러"""
        logger.info(f"봇 '{self.user}'이(가) 로그인했습니다!")
        logger.info(f"봇이 {len(self.guilds)}개의 서버에 연결되어 있습니다.")

        # 봇 상태 설정
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="뉴스 속보"
            )
        )

    async def send_news_alert(
        self, article: ArticleDTO[ArticleMetadata], channel_id: int
    ) -> bool:
        """
        특정 채널에 뉴스 알림을 전송합니다.

        Args:
            article: 알림을 보낼 뉴스 기사
            channel_id: 알림을 보낼 채널 ID

        Returns:
            bool: 알림 전송 성공 여부
        """
        # 채널 검증
        channel = self.get_channel(channel_id)
        if not channel:
            logger.warning(f"채널을 찾을 수 없음: {channel_id}")
            return False

        try:
            # 임베드 생성
            embed = self.formatter.create_embed(article)

            # 알림 전송
            await channel.send(embed=embed)
            logger.info(f"채널 {channel_id}에 뉴스 알림 전송: {article.title}")
            return True
        except Exception as e:
            logger.error(f"알림 전송 중 오류 발생: {str(e)}")
            return False

    async def send_news_via_webhook(self, article: ArticleDTO[ArticleMetadata]) -> bool:
        """
        Discord webhook을 통해 뉴스 알림을 전송합니다.
        직접 Discord 알림 서비스를 사용합니다.

        Args:
            article: 알림을 보낼 뉴스 기사

        Returns:
            bool: 알림 전송 성공 여부
        """
        # Discord 알림 서비스 확인
        if not self.discord_notifier:
            logger.error("Discord 알림 서비스가 설정되지 않았습니다.")
            return False

        try:
            # ArticleDTO를 서비스 계층이 기대하는 형식으로 변환
            news_data = {
                "title": article.title,
                "content": article.content,
                "source": article.metadata.platform,
                "url": article.url,
                "published_at": (
                    article.metadata.published_at.isoformat()
                    if article.metadata.published_at
                    else None
                ),
                "category": article.metadata.category,
            }

            # 알림 서비스를 통해 알림 전송
            message = self.discord_notifier.format_message(news_data)
            success = await self.discord_notifier.send(message)

            if success:
                logger.info(f"Discord webhook을 통해 뉴스 알림 전송: {article.title}")
            else:
                logger.warning(f"Discord webhook 알림 전송 실패: {article.title}")

            return success
        except Exception as e:
            logger.error(f"Discord webhook 알림 전송 중 오류 발생: {str(e)}")
            return False


async def run_bot():
    """
    Discord 봇을 실행합니다.

    비동기 함수로 봇을 시작하고, 예외 처리를 수행합니다.
    """
    bot = NewsAlertBot()

    try:
        logger.info("Discord 봇 시작 중...")
        await bot.start(bot.token)
    except KeyboardInterrupt:
        logger.info("키보드 인터럽트로 봇 종료")
        await bot.close()
    except Exception as e:
        logger.error(f"봇 실행 중 오류 발생: {str(e)}")
        await bot.close()
