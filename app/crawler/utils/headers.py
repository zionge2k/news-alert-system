"""
뉴스 크롤러에서 공통으로 사용하는 HTTP 헤더 생성 유틸리티
"""

from typing import Dict

import fake_useragent


def create_news_headers(
    referer: str | None = None,
    accept: str = "application/json, */*",
    accept_language: str = "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    content_type: str | None = None,
) -> Dict[str, str]:
    """
    뉴스 API 요청에 사용할 기본 헤더를 생성합니다.

    Args:
        referer: 요청 출처 URL. 없으면 생략됩니다.
        accept: Accept 헤더 값. 기본값은 JSON과 모든 타입 허용.
        accept_language: Accept-Language 헤더 값. 기본값은 한국어 우선.
        content_type: Content-Type 헤더 값. 없으면 생략됩니다.

    Returns:
        생성된 헤더 딕셔너리
    """
    headers = {
        "Accept": accept,
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": accept_language,
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "User-Agent": fake_useragent.UserAgent().random,
    }

    if referer:
        headers["Referer"] = referer

    if content_type:
        headers["Content-Type"] = content_type

    return headers


# 각 언론사별 기본 헤더 생성 함수
def create_mbc_headers() -> Dict[str, str]:
    """MBC 뉴스 API 요청에 사용할 헤더를 생성합니다."""
    return create_news_headers(
        referer="https://imnews.imbc.com/",
    )


def create_jtbc_headers() -> Dict[str, str]:
    """JTBC 뉴스 API 요청에 사용할 헤더를 생성합니다."""
    return create_news_headers(
        referer="https://news.jtbc.co.kr/",
        accept="application/json, text/plain, */*",  # JTBC는 JSON 응답 사용
    )


def create_ytn_headers(for_post: bool = False) -> Dict[str, str]:
    """
    YTN 뉴스 API 요청에 사용할 헤더를 생성합니다.

    Args:
        for_post: POST 요청 여부. True인 경우 Content-Type 헤더가 추가됩니다.
    """
    content_type = "application/x-www-form-urlencoded" if for_post else None

    return create_news_headers(
        referer="https://www.ytn.co.kr/",
        accept="application/json, text/javascript, */*; q=0.01",  # YTN은 JSON/JSONP 응답 사용
        content_type=content_type,
    )
