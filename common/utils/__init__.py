"""
utils 패키지는 여러 모듈 간에 공유되는 공통 유틸리티 기능을 제공합니다.

⚠️ 경고: 이 패키지는 더 이상 사용되지 않으며 새로운 `utils` 패키지로 이동되었습니다.
새로운 코드에서는 `from utils import X` 또는 `from utils.모듈명 import X` 형식으로 임포트하세요.
"""

import warnings

# 경고 메시지 표시
warnings.warn(
    "common/utils 패키지는 더 이상 사용되지 않으며 곧 제거될 예정입니다. "
    "대신 utils 패키지를 직접 사용하세요. 예: `from utils import X`",
    DeprecationWarning,
    stacklevel=2,
)

# adapters/utils.py에서 모든 기능 임포트
from adapters.utils import (
    AuthenticationException,
    AuthorizationException,
    BaseException,
    BusinessRuleException,
    Config,
    ConfigEnvironment,
    ConfigError,
    ConfigurationException,
    DatabaseException,
    NetworkException,
    ResourceNotFoundException,
    ValidationException,
    clean_json,
    clean_json_keys,
    create_headers,
    create_request_headers,
    exception_handler,
    format_date,
    format_datetime,
    get_current_timestamp,
    get_logger,
    get_timestamp,
    global_config,
    log_exception,
    remove_html_tags,
    sanitize_text,
    wrap_exception,
)

# 모든 임포트된 심볼을 공개
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
    # 추가 유틸리티 함수들
    "create_request_headers",
    "create_headers",
    "clean_json_keys",
    "clean_json",
    "get_current_timestamp",
    "get_timestamp",
    "format_datetime",
    "format_date",
    "sanitize_text",
    "remove_html_tags",
]
