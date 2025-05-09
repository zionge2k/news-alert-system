import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, call, patch

import pytest

from services.notifier.email import EmailNotifier


class TestEmailNotifier:
    """Email 알림 서비스 테스트"""

    @pytest.fixture
    def email_config(self):
        """테스트용 이메일 설정"""
        return {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "from_email": "news@example.com",
            "to_emails": ["user1@example.com", "user2@example.com"],
            "use_tls": True,
        }

    @pytest.fixture
    def notifier(self, email_config):
        """테스트용 EmailNotifier 인스턴스 생성"""
        return EmailNotifier(**email_config)

    @pytest.fixture
    def mock_news(self):
        """테스트용 뉴스 데이터"""
        return {
            "title": "테스트 뉴스 제목",
            "content": "테스트 뉴스 내용입니다.",
            "source": "테스트 소스",
            "url": "https://example.com/news/1",
        }

    def test_init(self, notifier, email_config):
        """초기화 테스트"""
        assert notifier.smtp_server == email_config["smtp_server"]
        assert notifier.smtp_port == email_config["smtp_port"]
        assert notifier.username == email_config["username"]
        assert notifier.password == email_config["password"]
        assert notifier.from_email == email_config["from_email"]
        assert notifier.to_emails == email_config["to_emails"]
        assert notifier.use_tls == email_config["use_tls"]

    def test_format_message(self, notifier, mock_news):
        """메시지 포맷팅 테스트"""
        message = notifier.format_message(mock_news)

        # HTML 형식으로 포맷팅되었는지 확인
        assert "<html>" in message
        assert "<body>" in message
        assert "<h2>" in message

        # 필수 요소가 포함되어 있는지 확인
        assert mock_news["title"] in message
        assert mock_news["content"] in message
        assert mock_news["source"] in message
        assert mock_news["url"] in message
        assert "뉴스 원문 보기" in message

        # URL이 링크로 포함되어 있는지 확인
        assert f'<a href="{mock_news["url"]}">' in message

    def test_format_message_with_missing_fields(self, notifier):
        """필드가 누락된 경우의 메시지 포맷팅 테스트"""
        incomplete_news = {"title": "제목만 있는 뉴스"}
        message = notifier.format_message(incomplete_news)

        assert "제목만 있는 뉴스" in message
        assert "내용 없음" in message
        assert "출처 미상" in message
        assert "뉴스 원문 보기" not in message  # URL이 없으므로 링크가 없어야 함

    @pytest.mark.asyncio
    async def test_send_success(self, notifier):
        """이메일 전송 성공 테스트"""
        # SMTP 서버 모킹
        mock_smtp = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
            result = await notifier.send("테스트 메시지")

            # SMTP 서버 연결 확인
            mock_smtp_class.assert_called_once_with(
                notifier.smtp_server, notifier.smtp_port
            )

            # TLS 사용 확인
            mock_smtp.starttls.assert_called_once()

            # 로그인 확인
            mock_smtp.login.assert_called_once_with(
                notifier.username, notifier.password
            )

            # 메시지 전송 확인
            mock_smtp.send_message.assert_called_once()

            # 연결 종료 확인
            mock_smtp.quit.assert_called_once()

            assert result is True

    @pytest.mark.asyncio
    async def test_send_without_tls(self):
        """TLS를 사용하지 않는 이메일 전송 테스트"""
        # TLS를 사용하지 않는 설정으로 인스턴스 생성
        notifier = EmailNotifier(
            smtp_server="smtp.example.com",
            smtp_port=25,
            username="test@example.com",
            password="password123",
            from_email="news@example.com",
            to_emails=["user@example.com"],
            use_tls=False,
        )

        mock_smtp = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            await notifier.send("테스트 메시지")

            # TLS가 호출되지 않아야 함
            mock_smtp.starttls.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_exception(self, notifier):
        """이메일 전송 중 예외 발생 테스트"""
        with patch("smtplib.SMTP", side_effect=Exception("SMTP 연결 오류")):
            result = await notifier.send("테스트 메시지")
            assert result is False

    @pytest.mark.asyncio
    async def test_notify_integration(self, notifier, mock_news):
        """notify 메서드 통합 테스트"""
        # send 메서드 모킹
        with patch.object(notifier, "send", return_value=True) as mock_send:
            result = await notifier.notify(mock_news)

            assert result is True
            mock_send.assert_called_once()

            # format_message의 결과가 send에 전달되는지 확인
            expected_message = notifier.format_message(mock_news)
            mock_send.assert_called_with(expected_message)


def test_email_format_message(mock_news):
    """이메일 메시지 포맷팅 테스트"""
    notifier = EmailNotifier(
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="test@example.com",
        password="password",
        from_email="news@example.com",
        to_emails=["user@example.com"],
        use_tls=True,
    )

    # URL이 있는 경우
    mock_news["url"] = "https://example.com/news/1"
    message = notifier.format_message(mock_news)

    assert "<h2>📰 테스트 뉴스 제목</h2>" in message
    assert "<p>테스트 본문 내용</p>" in message
    assert "<b>🔍 출처:</b> JTBC" in message
    assert "뉴스 원문 보기" in message
    assert "https://example.com/news/1" in message

    # URL이 없는 경우
    mock_news.pop("url")
    message = notifier.format_message(mock_news)

    assert "<h2>📰 테스트 뉴스 제목</h2>" in message
    assert "<p>테스트 본문 내용</p>" in message
    assert "<b>🔍 출처:</b> JTBC" in message
    assert "뉴스 원문 보기" not in message
