"""
Discord 발행 설정 모듈

이 모듈은 Discord 봇 설정 및 환경 변수를 관리합니다.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DiscordSettings(BaseSettings):
    """
    Discord 봇 설정
    """

    # Pydantic v2에서는 model_config를 클래스 변수로 정의
    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix="DISCORD_",  # 환경 변수 접두사 설정
    )

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


# 설정 인스턴스 생성
discord_settings = DiscordSettings()
