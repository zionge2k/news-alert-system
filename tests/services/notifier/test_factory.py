from unittest.mock import patch

import pytest

from services.notifier.base import BaseNotifier
from services.notifier.discord import DiscordNotifier
from services.notifier.email import EmailNotifier
from services.notifier.factory import (
    NotifierFactory,
    create_discord_notifier,
    create_email_notifier,
    create_slack_notifier,
)
from services.notifier.slack import SlackNotifier


class TestNotifierFactory:
    """NotifierFactory 테스트"""

    def test_create_discord_notifier(self):
        """Discord 알림 서비스 생성 테스트"""
        notifier = NotifierFactory.create(
            "discord", webhook_url="https://discord.example.com/webhook"
        )

        assert isinstance(notifier, DiscordNotifier)
        assert notifier.webhook_url == "https://discord.example.com/webhook"

    def test_create_slack_notifier(self):
        """Slack 알림 서비스 생성 테스트"""
        notifier = NotifierFactory.create(
            "slack", webhook_url="https://slack.example.com/webhook"
        )

        assert isinstance(notifier, SlackNotifier)
        assert notifier.webhook_url == "https://slack.example.com/webhook"

    def test_create_email_notifier(self):
        """Email 알림 서비스 생성 테스트"""
        email_config = {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "from_email": "news@example.com",
            "to_emails": ["user@example.com"],
            "use_tls": True,
        }

        notifier = NotifierFactory.create("email", **email_config)

        assert isinstance(notifier, EmailNotifier)
        assert notifier.smtp_server == email_config["smtp_server"]
        assert notifier.smtp_port == email_config["smtp_port"]

    def test_create_invalid_notifier(self):
        """지원하지 않는 알림 서비스 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError) as excinfo:
            NotifierFactory.create("invalid_type")

        assert "지원하지 않는 알림 채널 타입" in str(excinfo.value)

    def test_register_notifier(self):
        """새로운 알림 서비스 등록 테스트"""

        # 테스트용 알림 서비스 클래스
        class TestNotifier(BaseNotifier):
            def __init__(self, test_param):
                self.test_param = test_param

            async def send(self, message: str) -> bool:
                return True

        # 새로운 알림 서비스 등록
        NotifierFactory.register_notifier("test", TestNotifier)

        # 등록된 알림 서비스 생성
        notifier = NotifierFactory.create("test", test_param="test_value")

        assert isinstance(notifier, TestNotifier)
        assert notifier.test_param == "test_value"

        # 테스트 후 등록된 알림 서비스 제거
        NotifierFactory._notifiers.pop("test", None)


class TestHelperFunctions:
    """헬퍼 함수 테스트"""

    def test_create_discord_notifier(self):
        """create_discord_notifier 헬퍼 함수 테스트"""
        webhook_url = "https://discord.example.com/webhook"
        notifier = create_discord_notifier(webhook_url)

        assert isinstance(notifier, DiscordNotifier)
        assert notifier.webhook_url == webhook_url

    def test_create_slack_notifier(self):
        """create_slack_notifier 헬퍼 함수 테스트"""
        webhook_url = "https://slack.example.com/webhook"
        notifier = create_slack_notifier(webhook_url)

        assert isinstance(notifier, SlackNotifier)
        assert notifier.webhook_url == webhook_url

    def test_create_email_notifier(self):
        """create_email_notifier 헬퍼 함수 테스트"""
        smtp_server = "smtp.example.com"
        smtp_port = 587
        username = "test@example.com"
        password = "password123"
        from_email = "news@example.com"
        to_emails = ["user@example.com"]

        notifier = create_email_notifier(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            from_email=from_email,
            to_emails=to_emails,
        )

        assert isinstance(notifier, EmailNotifier)
        assert notifier.smtp_server == smtp_server
        assert notifier.smtp_port == smtp_port
        assert notifier.username == username
        assert notifier.from_email == from_email
        assert notifier.to_emails == to_emails
        assert notifier.use_tls is True  # 기본값
