from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseNotifier(ABC):
    """
    알림 서비스 기본 인터페이스
    모든 알림 서비스는 이 클래스를 상속해야 함
    """

    @abstractmethod
    async def send(self, message: str) -> bool:
        """
        알림 메시지를 전송

        Args:
            message (str): 전송할 메시지

        Returns:
            bool: 전송 성공 여부
        """
        pass

    def format_message(self, news: Dict[str, Any]) -> str:
        """
        뉴스 데이터를 알림 메시지 형식으로 변환

        Args:
            news (Dict[str, Any]): 뉴스 데이터

        Returns:
            str: 포맷팅된 알림 메시지
        """
        return f"{news['title']}: {news['content']}"

    async def notify(self, news: Dict[str, Any]) -> bool:
        """
        뉴스 알림을 전송하는 기본 워크플로우

        Args:
            news (Dict[str, Any]): 알림을 보낼 뉴스 데이터

        Returns:
            bool: 알림 전송 성공 여부
        """
        message = self.format_message(news)
        return await self.send(message)
