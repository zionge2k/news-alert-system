"""
Discord 클라이언트 모듈

이 모듈은 Discord API와의 통신을 처리하는 클라이언트를 제공합니다.
discord.py 라이브러리를 사용하여 메시지 전송 및 봇 관리를 구현합니다.
"""

import asyncio
from typing import Dict, List, Optional

from discord import Embed, Intents, Message, TextChannel
from discord.ext import commands

from app.pipelines.discord_publisher.config import discord_settings
from common.utils.logger import get_logger

logger = get_logger(__name__)


class DiscordClient:
    """
    Discord 봇 클라이언트

    Discord API와 통신하여 채널에 메시지를 보내는 기능을 제공합니다.
    """

    def __init__(self, settings=discord_settings):
        """
        Discord 클라이언트 초기화

        Args:
            settings: Discord 설정
        """
        self.settings = settings
        self.intents = Intents.default()
        self.intents.message_content = True

        # 봇 클라이언트 생성
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)
        self._setup_events()

        # 채널 캐시
        self.channels: Dict[str, TextChannel] = {}
        self._ready = asyncio.Event()
        self._closed = False

    def _setup_events(self):
        """봇 이벤트 핸들러 설정"""

        @self.bot.event
        async def on_ready():
            """봇이 준비되었을 때 호출"""
            if not self.bot.user:
                logger.exception("<bot: %s> 봇이 준비되지 않았습니다.", self.bot)
                raise RuntimeError("봇이 준비되지 않았습니다.")
            logger.info(f"{self.bot.user.name} 봇이 연결되었습니다.")

            # 채널 캐시 구성
            await self._cache_channels()

            # ready 이벤트 설정
            self._ready.set()

    async def start(self):
        """
        봇 클라이언트를 시작합니다.

        이 메서드는 비동기적으로 봇을 실행합니다.
        """
        if self._closed:
            raise RuntimeError("이미 종료된 클라이언트를 재시작할 수 없습니다.")

        # 비동기로 봇 시작
        self._task = asyncio.create_task(self._run())

        # 봇이 준비될 때까지 대기
        await self._ready.wait()
        logger.info("Discord 봇 클라이언트가 준비되었습니다.")

    async def _run(self):
        """봇 실행 내부 메서드"""
        try:
            await self.bot.start(self.settings.BOT_TOKEN)
        except Exception as e:
            logger.error(f"봇 실행 중 오류 발생: {str(e)}")
            self._ready.set()  # 오류 발생 시에도 이벤트 설정

    async def stop(self):
        """
        봇 클라이언트를 정상적으로 종료합니다.
        """
        if not self._closed:
            self._closed = True
            try:
                await self.bot.close()
            except Exception as e:
                logger.error(f"봇 종료 중 오류 발생: {str(e)}")

    async def _cache_channels(self):
        """
        자주 사용하는 채널을 캐시합니다.
        """
        try:
            # 기본 뉴스 채널
            default_channel_id = int(self.settings.CHANNEL_DEFAULT)
            self.channels["default"] = await self.bot.fetch_channel(default_channel_id)

            # 오류 로깅 채널 (설정된 경우)
            if self.settings.ERROR_CHANNEL_ID:
                error_channel_id = int(self.settings.ERROR_CHANNEL_ID)
                self.channels["error"] = await self.bot.fetch_channel(error_channel_id)

            logger.info(f"{len(self.channels)}개 채널이 캐시됨")

        except Exception as e:
            logger.error(f"채널 캐싱 중 오류 발생: {str(e)}")

    async def get_channel(self, channel_id: str) -> Optional[TextChannel]:
        """
        채널 ID로 채널 객체를 가져옵니다.

        Args:
            channel_id: 채널 ID

        Returns:
            TextChannel: 채널 객체 또는 None
        """
        # 이미 캐시된 경우
        if channel_id in self.channels:
            return self.channels[channel_id]

        try:
            # 캐시되지 않은 경우 API로 조회
            channel = await self.bot.fetch_channel(int(channel_id))

            # 텍스트 채널인지 확인
            if not isinstance(channel, TextChannel):
                logger.warning(f"ID {channel_id}는 텍스트 채널이 아닙니다.")
                return None

            # 캐시에 추가
            self.channels[channel_id] = channel
            return channel

        except Exception as e:
            logger.error(f"채널 조회 중 오류 발생: {str(e)}")
            return None

    async def send_message(
        self,
        channel_id: str,
        content: Optional[str] = None,
        embed: Optional[Embed] = None,
    ) -> Optional[Message]:
        """
        지정된 채널에 메시지를 전송합니다.

        Args:
            channel_id: 채널 ID
            content: 텍스트 내용 (선택)
            embed: 임베드 객체 (선택)

        Returns:
            Message: 전송된 메시지 객체 또는 None
        """
        channel = None

        # 채널 ID로 채널 찾기
        if channel_id in self.channels:
            channel = self.channels[channel_id]
        else:
            # 채널 ID로 직접 조회
            try:
                channel = await self.get_channel(channel_id)
            except:
                logger.error(f"채널 ID {channel_id}를 찾을 수 없습니다.")
                return None

        # 채널이 없으면 기본 채널 사용
        if not channel:
            logger.warning(f"채널 {channel_id}를 찾을 수 없어 기본 채널로 대체합니다.")
            if "default" in self.channels:
                channel = self.channels["default"]
            else:
                logger.error("기본 채널도 찾을 수 없습니다.")
                return None

        try:
            # 메시지 전송
            return await channel.send(content=content, embed=embed)
        except Exception as e:
            logger.error(f"메시지 전송 중 오류 발생: {str(e)}")
            return None

    async def send_error_message(self, error_embed: Embed) -> Optional[Message]:
        """
        오류 채널에 오류 메시지를 전송합니다.

        Args:
            error_embed: 오류 임베드

        Returns:
            Message: 전송된 메시지 객체 또는 None
        """
        # 오류 채널이 설정되어 있는 경우
        if "error" in self.channels:
            try:
                return await self.channels["error"].send(embed=error_embed)
            except Exception as e:
                logger.error(f"오류 메시지 전송 중 오류 발생: {str(e)}")

        # 오류 채널이 없으면 기본 채널에 전송
        logger.warning("오류 채널이 없어 기본 채널에 오류 메시지를 전송합니다.")
        if "default" in self.channels:
            try:
                return await self.channels["default"].send(embed=error_embed)
            except Exception as e:
                logger.error(f"기본 채널에 오류 메시지 전송 중 오류 발생: {str(e)}")

        return None


# 싱글톤 인스턴스 (lazy initialization)
_discord_client = None


async def get_discord_client() -> DiscordClient:
    """
    Discord 클라이언트 싱글톤 인스턴스를 반환합니다.

    Returns:
        DiscordClient: 클라이언트 인스턴스
    """
    global _discord_client

    if _discord_client is None:
        _discord_client = DiscordClient()
        await _discord_client.start()

    return _discord_client
