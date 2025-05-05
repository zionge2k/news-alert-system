"""
텍스트 처리를 위한 유틸리티 함수를 제공합니다.
"""

import re
from typing import Optional


def sanitize_text(
    text: str,
    allowed_chars: Optional[str] = None,
    replace_with: str = "",
    max_length: Optional[int] = None,
) -> str:
    """텍스트를 정리하고 허용된 문자만 남깁니다.

    Args:
        text: 정리할 텍스트
        allowed_chars: 정규식 패턴으로 허용할 문자 (기본값: 알파벳, 숫자, 공백, 일부 구두점)
        replace_with: 허용되지 않은 문자를 대체할 문자열
        max_length: 결과의 최대 길이 (None이면 제한 없음)

    Returns:
        정리된 텍스트
    """
    if text is None:
        return ""

    # 기본 허용 패턴: 알파벳, 숫자, 공백 및 일반적인 구두점
    if allowed_chars is None:
        allowed_chars = r'[^a-zA-Z0-9\s.,;:!?()\[\]{}\-_\'"]'

    # 허용되지 않은 문자 제거
    cleaned_text = re.sub(allowed_chars, replace_with, str(text))

    # 최대 길이로 자르기
    if max_length is not None and len(cleaned_text) > max_length:
        cleaned_text = cleaned_text[:max_length]

    return cleaned_text


def remove_html_tags(html: str) -> str:
    """HTML 태그를 제거하고 일반 텍스트만 반환합니다.

    Args:
        html: HTML 태그를 포함한 텍스트

    Returns:
        HTML 태그가 제거된 텍스트
    """
    if html is None:
        return ""

    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", str(html))

    # HTML 엔티티 처리 (기본적인 변환)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&amp;", "&")

    # 여러 개의 공백을 하나로 압축
    text = re.sub(r"\s+", " ", text).strip()

    return text
