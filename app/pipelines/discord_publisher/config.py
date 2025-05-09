"""
Discord 발행 서비스 설정 모듈

이 모듈은 Discord 봇 설정 및 환경 변수를 관리합니다.
"""

import os
from typing import Dict, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 환경 변수 로드
load_dotenv()


class DiscordSettings(BaseSettings):
    """Discord 발행 서비스 설정"""

    # 환경 변수 설정
    model_config = SettingsConfigDict(env_prefix="DISCORD_")

    # 봇 설정
    BOT_TOKEN: str = Field(default="", description="Discord 봇 토큰")
    WEBHOOK_URL: str = Field(default="", description="Discord webhook URL")
    DEFAULT_CHANNEL_ID: str = Field(default="", description="기본 채널 ID")
    ERROR_CHANNEL_ID: str = Field(default="", description="오류 알림 채널 ID")

    # 카테고리별 채널 매핑
    POLITICS_CHANNEL_ID: str = Field(default="", description="정치 뉴스 채널 ID")
    ECONOMY_CHANNEL_ID: str = Field(default="", description="경제 뉴스 채널 ID")
    SOCIETY_CHANNEL_ID: str = Field(default="", description="사회 뉴스 채널 ID")
    TECHNOLOGY_CHANNEL_ID: str = Field(default="", description="기술 뉴스 채널 ID")
    CULTURE_CHANNEL_ID: str = Field(default="", description="문화 뉴스 채널 ID")
    SPORTS_CHANNEL_ID: str = Field(default="", description="스포츠 뉴스 채널 ID")
    WORLD_CHANNEL_ID: str = Field(default="", description="국제 뉴스 채널 ID")

    # 발행 관련 설정
    PUBLISH_INTERVAL: int = Field(default=60, description="발행 주기 (초)")
    BATCH_SIZE: int = Field(default=5, description="한 번에 처리할 기사 수")
    RETRY_BATCH_SIZE: int = Field(default=3, description="재시도할 실패 기사 수")
    MAX_RETRIES: int = Field(default=3, description="최대 재시도 횟수")

    # 임베드 설정
    EMBED_COLOR: int = Field(default=0x3498DB, description="임베드 색상 (16진수)")
    FOOTER_TEXT: str = Field(default="뉴스 알리미", description="임베드 푸터 텍스트")

    # 서비스 어댑터 사용 설정
    USE_SERVICE_ADAPTER: bool = Field(
        default=False, description="서비스 어댑터 사용 설정"
    )
    USE_SERVICE_ADAPTER_FOR_RETRY: bool = Field(
        default=False, description="서비스 어댑터 재시도 사용 설정"
    )

    def get_channel_for_category(self, category: Optional[str]) -> str:
        """
        카테고리에 해당하는 채널 ID를 반환합니다.
        등록되지 않은 카테고리는 기본 채널을 사용합니다.

        Args:
            category: 뉴스 카테고리

        Returns:
            str: Discord 채널 ID
        """
        if not category:
            return self.DEFAULT_CHANNEL_ID

        category = category.lower()
        channel_id = ""

        if category == "politics":
            channel_id = self.POLITICS_CHANNEL_ID
        elif category == "economy":
            channel_id = self.ECONOMY_CHANNEL_ID
        elif category == "society":
            channel_id = self.SOCIETY_CHANNEL_ID
        elif category == "technology":
            channel_id = self.TECHNOLOGY_CHANNEL_ID
        elif category == "culture":
            channel_id = self.CULTURE_CHANNEL_ID
        elif category == "sports":
            channel_id = self.SPORTS_CHANNEL_ID
        elif category == "world":
            channel_id = self.WORLD_CHANNEL_ID

        # 채널 ID가 비어있으면 기본 채널 사용
        return channel_id if channel_id else self.DEFAULT_CHANNEL_ID


# 설정 싱글톤 인스턴스
discord_settings = DiscordSettings()
