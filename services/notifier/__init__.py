"""
알림 서비스 모듈
다양한 채널(Discord, Slack, Email 등)을 통해 뉴스 알림을 전송하는 서비스 구현
"""

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

__all__ = [
    "BaseNotifier",
    "DiscordNotifier",
    "SlackNotifier",
    "EmailNotifier",
    "NotifierFactory",
    "create_discord_notifier",
    "create_slack_notifier",
    "create_email_notifier",
]
