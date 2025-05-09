import logging
from typing import Dict, List, Optional, Type

from services.notifier.base import BaseNotifier
from services.notifier.discord import DiscordNotifier
from services.notifier.email import EmailNotifier
from services.notifier.slack import SlackNotifier

logger = logging.getLogger(__name__)


class NotifierFactory:
    """
    알림 서비스 팩토리
    알림 채널 타입에 따라 적절한 Notifier 인스턴스를 생성
    """

    _notifiers: Dict[str, Type[BaseNotifier]] = {
        "discord": DiscordNotifier,
        "slack": SlackNotifier,
        "email": EmailNotifier,
        # 추가 알림 채널은 여기에 등록
    }

    @classmethod
    def create(cls, channel_type: str, **kwargs) -> Optional[BaseNotifier]:
        """
        알림 채널 타입에 따라 적절한 Notifier 인스턴스를 생성

        Args:
            channel_type (str): 알림 채널 타입 (예: "discord", "slack", "email")
            **kwargs: 각 Notifier 클래스의 초기화에 필요한 추가 인자

        Returns:
            Optional[BaseNotifier]: 생성된 Notifier 인스턴스 또는 None

        Raises:
            ValueError: 지원하지 않는 채널 타입인 경우
        """
        if channel_type not in cls._notifiers:
            logger.error(f"지원하지 않는 알림 채널 타입: {channel_type}")
            raise ValueError(f"지원하지 않는 알림 채널 타입: {channel_type}")

        notifier_cls = cls._notifiers[channel_type]
        return notifier_cls(**kwargs)

    @classmethod
    def register_notifier(
        cls, channel_type: str, notifier_cls: Type[BaseNotifier]
    ) -> None:
        """
        새로운 알림 채널 타입 등록

        Args:
            channel_type (str): 알림 채널 타입 식별자
            notifier_cls (Type[BaseNotifier]): BaseNotifier를 상속한 Notifier 클래스
        """
        cls._notifiers[channel_type] = notifier_cls
        logger.info(f"알림 채널 등록 완료: {channel_type}")


# 기본 Discord 알림 서비스 생성 헬퍼 함수
def create_discord_notifier(webhook_url: str) -> DiscordNotifier:
    """
    Discord 알림 서비스 인스턴스 생성

    Args:
        webhook_url (str): Discord webhook URL

    Returns:
        DiscordNotifier: 생성된 Discord 알림 서비스 인스턴스
    """
    return DiscordNotifier(webhook_url)


# 기본 Slack 알림 서비스 생성 헬퍼 함수
def create_slack_notifier(webhook_url: str) -> SlackNotifier:
    """
    Slack 알림 서비스 인스턴스 생성

    Args:
        webhook_url (str): Slack webhook URL

    Returns:
        SlackNotifier: 생성된 Slack 알림 서비스 인스턴스
    """
    return SlackNotifier(webhook_url)


# 기본 Email 알림 서비스 생성 헬퍼 함수
def create_email_notifier(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    from_email: str,
    to_emails: List[str],
    use_tls: bool = True,
) -> EmailNotifier:
    """
    Email 알림 서비스 인스턴스 생성

    Args:
        smtp_server (str): SMTP 서버 주소
        smtp_port (int): SMTP 서버 포트
        username (str): SMTP 사용자 이름
        password (str): SMTP 비밀번호
        from_email (str): 발신자 이메일 주소
        to_emails (List[str]): 수신자 이메일 주소 목록
        use_tls (bool): TLS 사용 여부 (기본값: True)

    Returns:
        EmailNotifier: 생성된 Email 알림 서비스 인스턴스
    """
    return EmailNotifier(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=username,
        password=password,
        from_email=from_email,
        to_emails=to_emails,
        use_tls=use_tls,
    )
