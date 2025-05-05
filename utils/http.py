"""
HTTP 요청 및 응답 관련 유틸리티 함수를 제공합니다.
"""


def create_request_headers(
    user_agent=None, referer=None, accept_language="en-US,en;q=0.9"
):
    """표준화된 HTTP 헤더를 생성합니다.

    Args:
        user_agent: 사용자 정의 User-Agent 문자열
        referer: Referer URL
        accept_language: 언어 설정 헤더

    Returns:
        dict: requests 라이브러리와 함께 사용할 수 있는 헤더 딕셔너리
    """
    headers = {
        "User-Agent": user_agent
        or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": accept_language,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    return headers
