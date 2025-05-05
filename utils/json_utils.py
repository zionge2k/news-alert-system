"""
JSON 데이터 처리를 위한 유틸리티 함수를 제공합니다.
"""

import json
from typing import Any, Dict, List, Union


def clean_json_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """JSON 키를 정리하여 특수 문자를 제거하고 형식을 표준화합니다.

    Args:
        data: 잠재적으로 문제가 있는 키를 가진 입력 딕셔너리

    Returns:
        정리된 키를 가진 딕셔너리
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # 키를 정리 - 공백, 특수 문자 제거, snake_case로 변환
        clean_key = key.lower().replace(" ", "_").replace("-", "_")

        # 중첩된 딕셔너리와 리스트를 재귀적으로 정리
        if isinstance(value, dict):
            result[clean_key] = clean_json_keys(value)
        elif isinstance(value, list):
            result[clean_key] = [
                clean_json_keys(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[clean_key] = value

    return result
