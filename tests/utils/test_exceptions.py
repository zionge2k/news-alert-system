"""
예외 처리 유틸리티 테스트 모듈

이 모듈은 common.utils.exceptions에 정의된 예외 처리 기능을 테스트합니다.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from common.utils.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BaseException,
    BusinessRuleException,
    ConfigurationException,
    DatabaseException,
    NetworkException,
    ResourceNotFoundException,
    ValidationException,
    exception_handler,
    log_exception,
    wrap_exception,
)


class TestBaseException:
    """BaseException 및 파생 예외 클래스 테스트"""

    def test_base_exception_initialization(self):
        """기본 예외 클래스 초기화 테스트"""
        # 기본 매개변수로 초기화
        exc = BaseException()
        assert exc.message == ""
        assert exc.code == "BaseException"
        assert exc.details == {}

        # 모든 매개변수 지정
        exc = BaseException(
            message="테스트 메시지", code="TEST_CODE", details={"key": "value"}
        )
        assert exc.message == "테스트 메시지"
        assert exc.code == "TEST_CODE"
        assert exc.details == {"key": "value"}

    def test_base_exception_str_representation(self):
        """예외 문자열 표현 테스트"""
        # 기본 메시지
        exc = BaseException(message="테스트 메시지")
        assert str(exc) == "BaseException: 테스트 메시지"

        # 사용자 정의 코드
        exc = BaseException(message="테스트 메시지", code="TEST_CODE")
        assert str(exc) == "TEST_CODE: 테스트 메시지"

        # 추가 세부 정보
        exc = BaseException(
            message="테스트 메시지", code="TEST_CODE", details={"key": "value"}
        )
        assert str(exc) == "TEST_CODE: 테스트 메시지, details={'key': 'value'}"

    def test_derived_exceptions(self):
        """파생 예외 클래스 테스트"""
        # 각 예외 유형이 BaseException을 상속받았는지 확인
        assert issubclass(ValidationException, BaseException)
        assert issubclass(ConfigurationException, BaseException)
        assert issubclass(DatabaseException, BaseException)
        assert issubclass(NetworkException, BaseException)
        assert issubclass(AuthenticationException, BaseException)
        assert issubclass(AuthorizationException, BaseException)
        assert issubclass(ResourceNotFoundException, BaseException)
        assert issubclass(BusinessRuleException, BaseException)

        # 각 예외 유형이 올바르게 초기화되는지 확인
        exc = ValidationException(message="유효성 검사 오류")
        assert exc.code == "ValidationException"
        assert exc.message == "유효성 검사 오류"

        exc = DatabaseException(message="DB 오류", details={"table": "users"})
        assert exc.code == "DatabaseException"
        assert exc.message == "DB 오류"
        assert exc.details == {"table": "users"}


class TestExceptionWrappers:
    """예외 래핑 기능 테스트"""

    def test_wrap_exception_basic(self):
        """기본 예외 래핑 테스트"""
        original = ValueError("원본 에러")
        wrapped = wrap_exception(original)

        assert isinstance(wrapped, BaseException)
        assert wrapped.message == "원본 에러"
        assert wrapped.code == "BaseException"
        assert "original_exception" in wrapped.details
        assert str(original) in wrapped.details["original_exception"]
        assert wrapped.details["original_type"] == "ValueError"

    def test_wrap_exception_with_target(self):
        """대상 예외 클래스 지정 테스트"""
        original = ConnectionError("서버에 접속할 수 없습니다")
        wrapped = wrap_exception(original, target_exception=NetworkException)

        assert isinstance(wrapped, NetworkException)
        assert wrapped.message == "서버에 접속할 수 없습니다"
        assert wrapped.code == "NetworkException"
        assert wrapped.details["original_type"] == "ConnectionError"

    def test_wrap_exception_with_custom_params(self):
        """사용자 정의 파라미터로 래핑 테스트"""
        original = KeyError("존재하지 않는 키")
        wrapped = wrap_exception(
            original,
            target_exception=ResourceNotFoundException,
            message="리소스를 찾을 수 없습니다",
            code="RESOURCE_NOT_FOUND",
            details={"resource_type": "키", "resource_id": "missing_key"},
        )

        assert isinstance(wrapped, ResourceNotFoundException)
        assert wrapped.message == "리소스를 찾을 수 없습니다"
        assert wrapped.code == "RESOURCE_NOT_FOUND"
        assert wrapped.details["resource_type"] == "키"
        assert wrapped.details["resource_id"] == "missing_key"
        # 원본 예외 문자열 표현에 키워드가 포함되어 있는지 확인
        # (정확한 형식은 Python 버전에 따라 다를 수 있음)
        assert "존재하지 않는 키" in wrapped.details["original_exception"]
        assert wrapped.details["original_type"] == "KeyError"


class TestExceptionHandler:
    """예외 처리 데코레이터 테스트"""

    def test_handler_with_no_exception(self):
        """예외가 발생하지 않는 경우 테스트"""

        @exception_handler
        def func():
            return "성공"

        result = func()
        assert result == "성공"

    def test_handler_with_base_exception(self):
        """BaseException이 발생하는 경우 테스트"""

        @exception_handler
        def func():
            raise ValidationException("유효성 검사 실패")

        with pytest.raises(ValidationException) as exc_info:
            func()

        assert exc_info.value.code == "ValidationException"
        assert exc_info.value.message == "유효성 검사 실패"

    def test_handler_with_standard_exception(self):
        """표준 예외가 발생하는 경우 테스트"""

        @exception_handler
        def func():
            raise ValueError("잘못된 값")

        with pytest.raises(BaseException) as exc_info:
            func()

        assert exc_info.value.message == "잘못된 값"
        assert "original_exception" in exc_info.value.details
        assert exc_info.value.details["original_type"] == "ValueError"


class TestExceptionLogging:
    """예외 로깅 유틸리티 테스트"""

    @patch("common.utils.exceptions.logger")
    def test_log_base_exception(self, mock_logger):
        """BaseException 로깅 테스트"""
        exc = ValidationException(
            message="유효성 검사 오류",
            code="VALIDATION_ERROR",
            details={"field": "email"},
        )

        log_exception(exc)

        mock_logger.log.assert_any_call(
            logging.ERROR, "VALIDATION_ERROR: 유효성 검사 오류"
        )
        mock_logger.log.assert_any_call(logging.ERROR, "Details: {'field': 'email'}")

    @patch("common.utils.exceptions.logger")
    def test_log_standard_exception(self, mock_logger):
        """표준 예외 로깅 테스트"""
        exc = ValueError("표준 에러")

        log_exception(exc)

        mock_logger.log.assert_called_with(logging.ERROR, "Exception: 표준 에러")

    @patch("common.utils.exceptions.logger")
    @patch("common.utils.exceptions.sys")
    @patch("common.utils.exceptions.traceback")
    def test_log_with_traceback(self, mock_traceback, mock_sys, mock_logger):
        """스택 추적과 함께 로깅하는 경우 테스트"""
        exc = DatabaseException("DB 오류")
        mock_sys.exc_info.return_value = (MagicMock(), MagicMock(), MagicMock())
        mock_traceback.format_exception.return_value = ["스택 추적 라인"]

        log_exception(exc, log_level=logging.DEBUG)

        mock_logger.log.assert_any_call(logging.DEBUG, "DatabaseException: DB 오류")
        mock_logger.debug.assert_called_once()
        mock_traceback.format_exception.assert_called_once()


class TestIntegration:
    """통합 테스트"""

    @patch("common.utils.exceptions.logger")
    def test_exception_handler_with_logging(self, mock_logger):
        """예외 처리 핸들러와 로깅 통합 테스트"""

        @exception_handler
        def func():
            raise ValueError("통합 테스트 에러")

        with pytest.raises(BaseException):
            func()

        # 예상대로 로깅되었는지 확인
        mock_logger.error.assert_any_call("Unexpected exception: 통합 테스트 에러")
