"""
호환성 레이어: 기존 common/utils에서 새로운 utils 모듈로의 전환을 위한 어댑터입니다.
기존 코드가 common/utils를 통해 기능에 접근할 수 있도록 유지하면서 새로운 구조로의 마이그레이션을 촉진합니다.
"""

import functools
import warnings

# 새로운 utils 패키지에서 모든 모듈을 임포트합니다
from utils.config import Config, ConfigEnvironment, global_config
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

# 특수 모듈에서 추가 유틸리티 함수들을 임포트합니다
from utils.http import create_request_headers
from utils.json_utils import clean_json_keys
from utils.logger import get_logger
from utils.text_utils import remove_html_tags, sanitize_text

# 레거시 함수명을 새 구현에 매핑합니다
create_headers = create_request_headers
clean_json = clean_json_keys
get_timestamp = get_current_timestamp
format_date = format_datetime

# 레거시 호환성을 위한 별칭 정의
ConfigError = ConfigurationException

# 모든 공개 심볼을 정의합니다
__all__ = [
    # config 모듈
    "Config",
    "ConfigEnvironment",
    "global_config",
    "ConfigError",
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
    "create_headers",
    # json_utils 모듈
    "clean_json_keys",
    "clean_json",
    # datetime_utils 모듈
    "get_current_timestamp",
    "get_timestamp",
    "format_datetime",
    "format_date",
    # text_utils 모듈
    "sanitize_text",
    "remove_html_tags",
]


# 사용 시 경고 메시지를 표시하는 데코레이터
def deprecated_import_warning(func):
    """
    common/utils에서 임포트했을 때 사용자에게 경고 메시지를 표시하는 데코레이터입니다.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            "common/utils 모듈에서 임포트하는 것은 더 이상 사용되지 않습니다. "
            "대신 utils 패키지에서 직접 임포트하세요. "
            f"예: 'from utils import {func.__name__}' 또는 'from utils.모듈명 import {func.__name__}'",
            DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper


# 모든 공개 함수와 클래스에 경고 데코레이터를 적용합니다
for name in __all__:
    if name in globals() and callable(globals()[name]):
        globals()[name] = deprecated_import_warning(globals()[name])
