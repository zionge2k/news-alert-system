"""
로깅 유틸리티에 대한 테스트 모듈

이 모듈은 common.utils.logger 모듈의 기능을 테스트합니다.
"""

import io
import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from common.utils.logger import get_logger


class TestLogger:
    """로거 유틸리티 테스트 클래스"""

    def setup_method(self):
        """각 테스트 전에 로거 설정을 초기화"""
        # 로거 캐시 초기화
        logging.Logger.manager.loggerDict.clear()
        root = logging.getLogger()

        # 핸들러 제거
        if root.handlers:
            for handler in root.handlers[:]:
                root.removeHandler(handler)

    def test_get_logger_returns_logger_instance(self):
        """get_logger 함수가 Logger 인스턴스를 반환하는지 테스트"""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_with_same_name_returns_same_instance(self):
        """동일한 이름으로 get_logger를 호출하면 동일한 인스턴스를 반환하는지 테스트"""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")
        assert logger1 is logger2

    def test_get_logger_with_different_names_returns_different_instances(self):
        """다른 이름으로 get_logger를 호출하면 다른 인스턴스를 반환하는지 테스트"""
        logger1 = get_logger("test_logger1")
        logger2 = get_logger("test_logger2")
        assert logger1 is not logger2
        assert logger1.name == "test_logger1"
        assert logger2.name == "test_logger2"

    def test_logger_default_level(self):
        """로거가 올바른 기본 로그 레벨을 가지는지 테스트"""
        # 로거 캐시 및 핸들러 초기화
        logging.Logger.manager.loggerDict.clear()
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # 직접 basicConfig 호출
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)-5s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # root logger가 INFO 레벨로 설정되어 있는지 확인
        assert logging.getLogger().level == logging.INFO

        # 생성된 로거는 상위 로거의 설정을 상속
        logger = get_logger("test_logger_level")
        assert logger.level == 0  # 0은 로거가 부모로부터 레벨을 상속받는다는 의미

    def test_logger_captures_output(self):
        """로거가 메시지를 출력하는지 캡처하여 테스트"""
        # 핸들러 모킹
        string_io = io.StringIO()
        stream_handler = logging.StreamHandler(string_io)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-5s] %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        stream_handler.setFormatter(formatter)

        # 로거 설정
        logger = get_logger("test_stdout")
        logger.setLevel(logging.INFO)
        logger.addHandler(stream_handler)
        logger.propagate = False  # 루트 로거로 전파하지 않음

        # 로그 메시지 출력
        logger.info("Test log message")

        # 캡처된 출력 확인
        output = string_io.getvalue()
        assert "Test log message" in output
        assert "[INFO " in output

    def test_custom_logger_format(self):
        """직접 생성한 로거가 올바른 형식으로 메시지를 출력하는지 테스트"""
        # 커스텀 핸들러 및 포맷터 생성
        string_io = io.StringIO()
        stream_handler = logging.StreamHandler(string_io)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-5s] %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        stream_handler.setFormatter(formatter)

        # 로거 설정
        logger = get_logger("test_format")
        logger.setLevel(logging.INFO)
        logger.addHandler(stream_handler)
        logger.propagate = False  # 루트 로거로 전파하지 않음

        # 로그 메시지 출력
        logger.info("Format test message")

        # 캡처된 출력 확인
        output = string_io.getvalue()

        # 포맷 확인
        assert "Format test message" in output
        assert "[INFO " in output
        assert len(output.split()) >= 3  # 날짜 시간, 레벨, 메시지

    @patch("logging.Logger.error")
    def test_logger_error_method_called(self, mock_error):
        """로거의 error 메소드가 호출되는지 테스트"""
        logger = get_logger("test_error")
        logger.error("Test error message")
        mock_error.assert_called_once_with("Test error message")

    @patch("logging.Logger.warning")
    def test_logger_warning_method_called(self, mock_warning):
        """로거의 warning 메소드가 호출되는지 테스트"""
        logger = get_logger("test_warning")
        logger.warning("Test warning message")
        mock_warning.assert_called_once_with("Test warning message")

    @patch("logging.Logger.debug")
    def test_logger_debug_method_called(self, mock_debug):
        """로거의 debug 메소드가 호출되는지 테스트"""
        logger = get_logger("test_debug")
        logger.debug("Test debug message")
        mock_debug.assert_called_once_with("Test debug message")

    def test_logger_level_filtering(self):
        """로거가 설정된 레벨에 따라 메시지를 필터링하는지 테스트"""
        # 캡처 핸들러 설정
        string_io = io.StringIO()
        stream_handler = logging.StreamHandler(string_io)
        stream_handler.setLevel(logging.INFO)

        # 로거 설정
        logger = get_logger("test_filter")
        logger.setLevel(logging.INFO)
        logger.addHandler(stream_handler)
        logger.propagate = False  # 루트 로거로 전파하지 않음

        # DEBUG 메시지는 INFO 레벨에서 출력되지 않음
        logger.debug("This should not be logged")
        assert "This should not be logged" not in string_io.getvalue()

        # INFO 메시지는 INFO 레벨에서 출력됨
        logger.info("This should be logged")
        assert "This should be logged" in string_io.getvalue()

    def test_logger_with_exception(self):
        """로거가 예외 정보를 올바르게 기록하는지 테스트"""
        logger = get_logger("test_exception")

        with patch("logging.Logger.exception") as mock_exception:
            try:
                raise ValueError("Test exception")
            except ValueError as e:
                logger.exception("Exception occurred: %s", e)

            mock_exception.assert_called_once()
            assert "Exception occurred:" in mock_exception.call_args[0][0]

    def test_logger_propagation(self):
        """로거가 상위 로거로 메시지를 전파하는지 테스트"""
        # 출력 캡처를 위한 StringIO 객체
        string_io = io.StringIO()

        # 부모 로거 설정
        parent_logger = get_logger("test_parent")
        parent_logger.setLevel(logging.INFO)

        # 부모 로거에 핸들러 추가
        handler = logging.StreamHandler(string_io)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(name)s: %(message)s")
        handler.setFormatter(formatter)
        parent_logger.addHandler(handler)

        # 자식 로거 생성 (propagate 기본값은 True)
        child_logger = get_logger("test_parent.child")
        child_logger.setLevel(logging.INFO)

        # 자식 로거에서 메시지 출력
        child_logger.info("Child message")

        # 부모 로거의 핸들러가 메시지를 출력했는지 확인
        output = string_io.getvalue()
        assert "test_parent.child: Child message" in output
