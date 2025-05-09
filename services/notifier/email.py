import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from services.notifier.base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """
    이메일 알림 서비스
    SMTP를 통해 뉴스 알림을 이메일로 전송
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True,
    ):
        """
        이메일 알림 서비스 초기화

        Args:
            smtp_server (str): SMTP 서버 주소
            smtp_port (int): SMTP 서버 포트
            username (str): SMTP 사용자 이름
            password (str): SMTP 비밀번호
            from_email (str): 발신자 이메일 주소
            to_emails (List[str]): 수신자 이메일 주소 목록
            use_tls (bool): TLS 사용 여부 (기본값: True)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls

    async def send(self, message: str) -> bool:
        """
        이메일을 통해 메시지 전송

        Args:
            message (str): 전송할 메시지

        Returns:
            bool: 전송 성공 여부
        """
        try:
            # 이메일 메시지 생성
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = "뉴스 알림"

            # 메시지 본문 추가
            msg.attach(MIMEText(message, "html"))

            # SMTP 서버에 연결
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            if self.use_tls:
                server.starttls()

            # 로그인
            server.login(self.username, self.password)

            # 이메일 전송
            server.send_message(msg)

            # 연결 종료
            server.quit()

            logger.info(f"이메일 알림 전송 성공: {len(self.to_emails)}명의 수신자")
            return True
        except Exception as e:
            logger.error(f"이메일 전송 중 오류 발생: {e}")
            return False

    def format_message(self, news: Dict[str, Any]) -> str:
        """
        뉴스 데이터를 HTML 이메일 메시지 형식으로 변환

        Args:
            news (Dict[str, Any]): 뉴스 데이터

        Returns:
            str: 포맷팅된 HTML 이메일 메시지
        """
        title = news.get("title", "제목 없음")
        content = news.get("content", "내용 없음")
        source = news.get("source", "출처 미상")
        url = news.get("url", "")

        html = f"""
        <html>
            <body>
                <h2>📰 {title}</h2>
                <p>{content}</p>
                <p><b>🔍 출처:</b> {source}</p>
        """

        if url:
            html += f'<p><a href="{url}">🔗 뉴스 원문 보기</a></p>'

        html += """
            </body>
        </html>
        """

        return html
