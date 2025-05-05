"""
커버리지 테스트를 위한 샘플 테스트 파일

이 파일은 테스트 커버리지 설정이 올바르게 작동하는지 확인하기 위한 샘플 테스트를 포함합니다.
"""

import pytest


def dummy_function(a, b):
    """덧셈 연산을 수행하는 더미 함수"""
    if a < 0 or b < 0:
        return None
    return a + b


class TestCoverageSample:
    """커버리지 설정 테스트를 위한 샘플 테스트 클래스"""

    def test_dummy_function_positive(self):
        """양수 입력에 대한 더미 함수 테스트"""
        assert dummy_function(1, 2) == 3
        assert dummy_function(0, 0) == 0
        assert dummy_function(10, 20) == 30

    def test_dummy_function_negative(self):
        """음수 입력에 대한 더미 함수 테스트"""
        assert dummy_function(-1, 2) is None
        assert dummy_function(1, -2) is None
        assert dummy_function(-1, -2) is None

    @pytest.mark.parametrize("a, b, expected", [(5, 10, 15), (3, 7, 10), (0, 5, 5)])
    def test_dummy_function_parametrized(self, a, b, expected):
        """파라미터화된 더미 함수 테스트"""
        assert dummy_function(a, b) == expected
