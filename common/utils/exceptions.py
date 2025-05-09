"""
예외 처리 유틸리티 모듈

이 모듈은 애플리케이션 전체에서 일관된 예외 처리를 위한 도구를 제공합니다.
"""

import logging
import sys
import traceback
from typing import Any, Callable, Dict, Optional, Type

# 기본 로거 설정
logger = logging.getLogger(__name__)


class BaseException(Exception):
    """애플리케이션의 모든 사용자 정의 예외의 기본 클래스"""

    def __init__(
        self, message: str = "", code: str = None, details: Dict[str, Any] = None
    ):
        """
        사용자 정의 예외 초기화

        Args:
            message: 예외 메시지
            code: 예외 코드 (오류 식별에 사용)
            details: 추가적인 오류 상세 정보를 담은 딕셔너리
        """
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        """예외를 문자열로 표현"""
        detail_str = f", details={self.details}" if self.details else ""
        return f"{self.code}: {self.message}{detail_str}"


class ValidationException(BaseException):
    """데이터 유효성 검사 관련 예외"""

    pass


class ConfigurationException(BaseException):
    """설정 관련 예외"""

    pass


class DatabaseException(BaseException):
    """데이터베이스 관련 예외"""

    pass


class NetworkException(BaseException):
    """네트워크/API 통신 관련 예외"""

    pass


class AuthenticationException(BaseException):
    """인증 관련 예외"""

    pass


class AuthorizationException(BaseException):
    """권한 관련 예외"""

    pass


class ResourceNotFoundException(BaseException):
    """리소스를 찾을 수 없을 때 발생하는 예외"""

    pass


class BusinessRuleException(BaseException):
    """비즈니스 규칙 위반 관련 예외"""

    pass


def wrap_exception(
    exception: Exception,
    target_exception: Type[BaseException] = BaseException,
    message: Optional[str] = None,
    code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> BaseException:
    """
    외부 예외를 애플리케이션 예외로 래핑

    Args:
        exception: 래핑할 원본 예외
        target_exception: 변환할 대상 예외 클래스
        message: 새 예외에 사용할 메시지 (None이면 원본 예외 메시지 사용)
        code: 새 예외에 사용할 코드
        details: 새 예외에 포함할 추가 세부 정보

    Returns:
        래핑된 애플리케이션 예외
    """
    wrapped_details = details or {}
    wrapped_details["original_exception"] = str(exception)
    wrapped_details["original_type"] = exception.__class__.__name__

    return target_exception(
        message=message or str(exception), code=code, details=wrapped_details
    )


def exception_handler(func: Callable) -> Callable:
    """
    예외 처리 데코레이터

    함수/메서드를 래핑하여 일관된 예외 처리 로직 적용

    Args:
        func: 래핑할 함수/메서드

    Returns:
        래핑된 함수
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseException as e:
            # 이미 처리된 애플리케이션 예외는 로깅만 하고 다시 발생
            logger.error(f"Application exception: {e.code} - {e.message}")
            raise
        except Exception as e:
            # 예상치 못한 예외는 래핑하고 로깅
            logger.error(f"Unexpected exception: {str(e)}")
            logger.debug(traceback.format_exc())
            wrapped = wrap_exception(e)
            raise wrapped

    return wrapper


def log_exception(exception: Exception, log_level: int = logging.ERROR) -> None:
    """
    예외를 로깅

    Args:
        exception: 로깅할 예외
        log_level: 로깅 레벨
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if isinstance(exception, BaseException):
        logger.log(log_level, f"{exception.code}: {exception.message}")
        if exception.details:
            logger.log(log_level, f"Details: {exception.details}")
    else:
        logger.log(log_level, f"Exception: {str(exception)}")

    if log_level <= logging.DEBUG:
        logger.debug(
            "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        )
