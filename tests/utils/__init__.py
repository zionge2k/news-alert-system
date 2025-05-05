"""
유틸리티 테스트 패키지

이 패키지는 애플리케이션의 유틸리티 함수들에 대한 테스트를 포함합니다.
"""

import pytest


def pytest_configure(config):
    """유틸리티 테스트를 위한 마커 등록"""
    config.addinivalue_line(
        "markers", "utils: marks tests related to utility functions"
    )
