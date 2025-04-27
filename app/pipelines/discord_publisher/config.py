"""
Discord 발행 설정 모듈

이 모듈은 Discord 봇 설정 및 환경 변수를 관리합니다.
"""

import os
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field


class DiscordSettings(BaseModel):
    """
    Discord 봇 설정

    환경 변수에서 설정을 로드합니다.
    """

    # Pydantic v2에서는 model_config를 클래스 변수로 정의
    model_config: ClassVar[Dict[str, Any]] = {
        "extra": "ignore",
    }

    # 필수 설정
    BOT_TOKEN: str = Field(default="", description="Discord 봇 토큰")

    # 채널 설정
    CHANNEL_DEFAULT: str = Field(default="", description="뉴스를 발행할 기본 채널 ID")
    ERROR_CHANNEL_ID: Optional[str] = Field(
        default=None, description="오류 로깅 채널 ID"
    )

    # 발행 설정
    PUBLISH_INTERVAL: int = Field(default=60, description="발행 주기(초)")
    BATCH_SIZE: int = Field(default=20, description="한 번에 처리할 기사 수")
    MAX_RETRIES: int = Field(default=3, description="실패 시 최대 재시도 횟수")

    # 메시지 커스터마이징
    EMBED_COLOR: int = Field(default=0x3498DB, description="임베드 색상 (16진수)")
    FOOTER_TEXT: str = Field(default="뉴스 알리미", description="임베드 푸터 텍스트")

    def get_channel_for_category(self, category: Optional[str]) -> str:
        """
        카테고리에 해당하는 채널 ID를 반환합니다.
        현재는 항상 기본 채널을 반환합니다.

        Args:
            category: 기사 카테고리 (현재 사용하지 않음)

        Returns:
            str: 기본 채널 ID
        """
        return self.CHANNEL_DEFAULT

    @classmethod
    def from_env(cls) -> "DiscordSettings":
        """
        환경 변수에서 설정을 로드합니다.

        Returns:
            DiscordSettings: 설정 인스턴스
        """
        # 환경 변수에서 값 가져오기
        bot_token = os.environ.get("DISCORD_BOT_TOKEN", "")
        channel_default = os.environ.get("DISCORD_CHANNEL_DEFAULT", "")
        error_channel_id = os.environ.get("DISCORD_ERROR_CHANNEL_ID")

        # 발행 설정
        publish_interval = int(os.environ.get("DISCORD_PUBLISH_INTERVAL", "60"))
        batch_size = int(os.environ.get("DISCORD_BATCH_SIZE", "20"))
        max_retries = int(os.environ.get("DISCORD_MAX_RETRIES", "3"))

        # 메시지 설정
        try:
            embed_color = int(os.environ.get("DISCORD_EMBED_COLOR", "0x3498db"), 0)
        except ValueError:
            embed_color = 0x3498DB

        footer_text = os.environ.get("DISCORD_FOOTER_TEXT", "뉴스 알리미")

        return cls(
            BOT_TOKEN=bot_token,
            CHANNEL_DEFAULT=channel_default,
            ERROR_CHANNEL_ID=error_channel_id,
            PUBLISH_INTERVAL=publish_interval,
            BATCH_SIZE=batch_size,
            MAX_RETRIES=max_retries,
            EMBED_COLOR=embed_color,
            FOOTER_TEXT=footer_text,
        )


# 설정 인스턴스 생성
discord_settings = DiscordSettings.from_env()
