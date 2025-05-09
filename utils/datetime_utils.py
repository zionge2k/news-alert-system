"""
날짜 및 시간 처리를 위한 유틸리티 함수를 제공합니다.
"""

import datetime
from typing import Optional, Union

import pytz


def get_current_timestamp() -> int:
    """현재 UTC 타임스탬프를 초 단위로 반환합니다."""
    return int(datetime.datetime.now(datetime.timezone.utc).timestamp())


def format_datetime(
    dt: Union[datetime.datetime, str],
    output_format: str = "%Y-%m-%d %H:%M:%S",
    timezone: Optional[str] = None,
) -> str:
    """datetime 객체 또는 문자열을 지정된 형식으로 변환하고 선택적으로 시간대를 변경합니다.

    Args:
        dt: 변환할 datetime 객체 또는 문자열
        output_format: 출력 형식 (예: "%Y-%m-%d %H:%M:%S")
        timezone: 변환할 시간대 (예: "Asia/Seoul")

    Returns:
        포맷된 날짜/시간 문자열
    """
    if isinstance(dt, str):
        # 문자열을 datetime으로 파싱 시도
        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ]:
            try:
                dt = datetime.datetime.strptime(dt, fmt)
                break
            except ValueError:
                continue

    if timezone:
        if not dt.tzinfo:
            # 시간대 정보가 없으면 UTC로 가정
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        # 대상 시간대로 변환
        dt = dt.astimezone(pytz.timezone(timezone))

    return dt.strftime(output_format)
