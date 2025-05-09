from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from services.notifier.discord import DiscordNotifier


class TestDiscordNotifier:
    """Discord 알림 서비스 테스트"""

    @pytest.fixture
    def notifier(self):
        """테스트용 DiscordNotifier 인스턴스 생성"""
        return DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")

    @pytest.fixture
    def mock_news(self):
        """테스트용 뉴스 데이터"""
        return {
            "title": "테스트 뉴스 제목",
            "content": "테스트 뉴스 내용입니다. " * 10,  # 긴 내용 테스트용
            "source": "테스트 소스",
            "url": "https://example.com/news/1",
        }

    def test_init(self, notifier):
        """초기화 테스트"""
        assert notifier.webhook_url == "https://discord.com/api/webhooks/test"

    def test_format_message(self, notifier, mock_news):
        """메시지 포맷팅 테스트"""
        message = notifier.format_message(mock_news)

        # 필수 요소가 포함되어 있는지 확인
        assert "📰" in message  # 이모지 포함
        assert mock_news["title"] in message
        assert mock_news["content"][:20] in message
        assert mock_news["source"] in message
        assert mock_news["url"] in message
        assert "뉴스 원문 보기" in message

    def test_format_message_with_missing_fields(self, notifier):
        """필드가 누락된 경우의 메시지 포맷팅 테스트"""
        incomplete_news = {"title": "제목만 있는 뉴스"}
        message = notifier.format_message(incomplete_news)

        assert "제목만 있는 뉴스" in message
        assert "내용 없음" in message
        assert "출처 미상" in message

    @pytest.mark.asyncio
    async def test_send_success(self, notifier):
        """메시지 전송 성공 테스트"""
        # aiohttp.ClientSession 모킹
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 204  # Discord API 성공 응답

        # context manager를 시뮬레이션하는 __aenter__와 __aexit__ 설정
        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await notifier.send("테스트 메시지")

            assert result is True
            mock_session.post.assert_called_once()
            # webhook URL과 payload 확인
            args, kwargs = mock_session.post.call_args
            assert args[0] == notifier.webhook_url
            assert kwargs["json"] == {"content": "테스트 메시지"}

            # session이 닫혔는지 확인
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_failure_response(self, notifier):
        """메시지 전송 실패(응답 오류) 테스트"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 400  # 실패 응답

        mock_session.post.return_value.__aenter__.return_value = mock_response

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await notifier.send("테스트 메시지")

            assert result is False
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_exception(self, notifier):
        """메시지 전송 중 예외 발생 테스트"""
        mock_session = AsyncMock()
        mock_session.post.side_effect = Exception("네트워크 오류")

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await notifier.send("테스트 메시지")

            assert result is False
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_integration(self, notifier, mock_news):
        """notify 메서드 통합 테스트"""
        # send 메서드 모킹
        with patch.object(notifier, "send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await notifier.notify(mock_news)

            assert result is True
            mock_send.assert_called_once()
            # format_message의 결과가 send에 전달되는지 확인
            expected_message = notifier.format_message(mock_news)
            mock_send.assert_called_with(expected_message)
