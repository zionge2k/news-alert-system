import logging
from typing import Any, Dict, Optional

import aiohttp

from services.notifier.base import BaseNotifier

logger = logging.getLogger(__name__)


class DiscordNotifier(BaseNotifier):
    """
    Discord 알림 서비스
    Discord webhook을 통해 뉴스 알림을 전송
    """

    def __init__(self, webhook_url: str):
        """
        Discord 알림 서비스 초기화

        Args:
            webhook_url (str): Discord webhook URL
        """
        self.webhook_url = webhook_url

    async def send(self, message: str) -> bool:
        """
        Discord webhook을 통해 메시지 전송

        Args:
            message (str): 전송할 메시지

        Returns:
            bool: 전송 성공 여부
        """
        try:
            session = aiohttp.ClientSession()
            try:
                payload = {"content": message}
                async with session.post(self.webhook_url, json=payload) as response:
                    if (
                        response.status != 204
                    ):  # Discord API는 성공 시 204 No Content 반환
                        logger.error(f"Discord 메시지 전송 실패: {response.status}")
                        return False
                    return True
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"Discord 메시지 전송 중 오류 발생: {e}")
            return False

    def format_message(self, news: Dict[str, Any]) -> str:
        """
        뉴스 데이터를 Discord 메시지 형식으로 변환

        Args:
            news (Dict[str, Any]): 뉴스 데이터

        Returns:
            str: 포맷팅된 Discord 메시지
        """
        title = news.get("title", "제목 없음")
        content = news.get("content", "내용 없음")
        source = news.get("source", "출처 미상")
        url = news.get("url", "")

        message = f"📰 **{title}**\n\n"
        message += f"{content[:200]}...\n\n" if len(content) > 200 else f"{content}\n\n"
        message += f"🔍 출처: {source}"

        if url:
            message += f"\n🔗 [뉴스 원문 보기]({url})"

        return message
