"""
호환성 레이어 테스트 모듈

이 모듈은 common/utils에서 utils로의 마이그레이션을 위한 호환성 레이어가
정상적으로 작동하는지 확인하는 테스트를 포함합니다.
"""

import warnings

import pytest


class TestCompatibilityLayer:
    """호환성 레이어 테스트 클래스"""

    def test_legacy_imports_work(self):
        """레거시 임포트가 여전히 작동하는지 확인"""
        # 경고를 무시하고 임포트
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # Config 임포트 테스트
            from common.utils import (
                Config,
                ConfigEnvironment,
                ConfigError,
                global_config,
            )

            assert Config is not None
            assert ConfigEnvironment is not None
            assert ConfigError is not None
            assert global_config is not None

            # Exception 임포트 테스트
            from common.utils import (
                BaseException,
                ConfigurationException,
                DatabaseException,
                ValidationException,
                exception_handler,
                log_exception,
                wrap_exception,
            )

            assert BaseException is not None
            assert ValidationException is not None
            assert ConfigurationException is not None
            assert DatabaseException is not None
            assert exception_handler is not None
            assert log_exception is not None
            assert wrap_exception is not None

            # Logger 임포트 테스트
            from common.utils import get_logger

            assert get_logger is not None

            # HTTP 유틸리티 테스트
            from common.utils import create_headers, create_request_headers

            assert create_request_headers is not None
            assert create_headers is not None

            # JSON 유틸리티 테스트
            from common.utils import clean_json, clean_json_keys

            assert clean_json_keys is not None
            assert clean_json is not None

            # datetime 유틸리티 테스트
            from common.utils import format_datetime, get_current_timestamp

            assert get_current_timestamp is not None
            assert format_datetime is not None

            # text 유틸리티 테스트
            from common.utils import remove_html_tags, sanitize_text

            assert sanitize_text is not None
            assert remove_html_tags is not None

    def test_new_imports_work(self):
        """새로운 임포트 방식이 작동하는지 확인"""
        # 패키지 수준 임포트
        from utils import (
            BaseException,
            Config,
            ConfigEnvironment,
            ConfigError,
            ConfigurationException,
            ValidationException,
            clean_json_keys,
            create_request_headers,
            format_datetime,
            get_current_timestamp,
            get_logger,
            global_config,
            remove_html_tags,
            sanitize_text,
        )

        assert Config is not None
        assert ConfigEnvironment is not None
        assert ConfigError is not None
        assert global_config is not None
        assert BaseException is not None
        assert ValidationException is not None
        assert ConfigurationException is not None
        assert get_logger is not None
        assert create_request_headers is not None
        assert clean_json_keys is not None
        assert get_current_timestamp is not None
        assert format_datetime is not None
        assert sanitize_text is not None
        assert remove_html_tags is not None

        # 직접 모듈 임포트
        from utils.config import Config, ConfigEnvironment, global_config
        from utils.datetime_utils import format_datetime, get_current_timestamp
        from utils.exceptions import BaseException, ConfigError, ValidationException
        from utils.http import create_request_headers
        from utils.json_utils import clean_json_keys
        from utils.logger import get_logger
        from utils.text_utils import remove_html_tags, sanitize_text

        assert Config is not None
        assert ConfigEnvironment is not None
        assert global_config is not None
        assert BaseException is not None
        assert ValidationException is not None
        assert ConfigError is not None
        assert get_logger is not None
        assert create_request_headers is not None
        assert clean_json_keys is not None
        assert get_current_timestamp is not None
        assert format_datetime is not None
        assert sanitize_text is not None
        assert remove_html_tags is not None

    def test_deprecation_warnings(self):
        """레거시 임포트 시 경고가 발생하는지 확인"""
        with pytest.warns(DeprecationWarning):
            from common.utils import get_logger

        with pytest.warns(DeprecationWarning):
            from common.utils import Config
