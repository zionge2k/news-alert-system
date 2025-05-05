"""
utils 패키지는 애플리케이션 전반에서 사용되는 공통 유틸리티 기능을 제공합니다.
이 패키지는 이전의 common/utils를 대체합니다.
"""

# 주요 모듈에서 기본 클래스와 함수 임포트
from utils.config import Config, ConfigEnvironment, ConfigError, global_config
from utils.datetime_utils import format_datetime, get_current_timestamp
from utils.exceptions import (
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

# 유틸리티 모듈에서 함수 임포트
from utils.http import create_request_headers
from utils.json_utils import clean_json_keys
from utils.logger import get_logger
from utils.text_utils import remove_html_tags, sanitize_text

# 모든 공개 심볼을 정의합니다
__all__ = [
    # config 모듈
    "Config",
    "ConfigEnvironment",
    "ConfigError",
    "global_config",
    # exceptions 모듈
    "AuthenticationException",
    "AuthorizationException",
    "BaseException",
    "BusinessRuleException",
    "ConfigurationException",
    "DatabaseException",
    "NetworkException",
    "ResourceNotFoundException",
    "ValidationException",
    "exception_handler",
    "log_exception",
    "wrap_exception",
    # logger 모듈
    "get_logger",
    # http 모듈
    "create_request_headers",
    # json_utils 모듈
    "clean_json_keys",
    # datetime_utils 모듈
    "get_current_timestamp",
    "format_datetime",
    # text_utils 모듈
    "sanitize_text",
    "remove_html_tags",
]
