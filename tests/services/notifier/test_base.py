import asyncio
from unittest.mock import AsyncMock

import pytest

from services.notifier.base import BaseNotifier


class TestBaseNotifier:
    """BaseNotifier 인터페이스 테스트"""

    class ConcreteNotifier(BaseNotifier):
        """테스트용 BaseNotifier 구현체"""

        def __init__(self):
            self.send_mock = AsyncMock(return_value=True)

        async def send(self, message: str) -> bool:
            return await self.send_mock(message)

    @pytest.fixture
    def notifier(self):
        """테스트용 Notifier 인스턴스 생성"""
        return self.ConcreteNotifier()

    @pytest.mark.asyncio
    async def test_send_abstract_method(self, notifier):
        """send 메서드가 구현되어 있는지 확인"""
        message = "테스트 메시지"
        result = await notifier.send(message)

        assert result is True
        notifier.send_mock.assert_called_once_with(message)

    def test_format_message(self, notifier):
        """format_message 메서드 테스트"""
        news = {
            "title": "테스트 제목",
            "content": "테스트 내용",
            "source": "테스트 소스",
            "url": "https://example.com",
        }

        message = notifier.format_message(news)
        assert "테스트 제목" in message
        assert "테스트 내용" in message

    @pytest.mark.asyncio
    async def test_notify_workflow(self, notifier):
        """notify 메서드 워크플로우 테스트"""
        news = {"title": "테스트 제목", "content": "테스트 내용"}

        # format_message 메서드를 모킹하여 테스트
        original_format = notifier.format_message
        notifier.format_message = lambda n: f"포맷된 메시지: {n['title']}"

        try:
            result = await notifier.notify(news)

            assert result is True
            notifier.send_mock.assert_called_once_with("포맷된 메시지: 테스트 제목")
        finally:
            # 원래 메서드로 복원
            notifier.format_message = original_format
