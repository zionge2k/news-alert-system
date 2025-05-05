"""
이 모듈은 common.utils.config 모듈의 기능을 테스트합니다.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from common.utils.config import Config, ConfigEnvironment, ConfigError, global_config


class TestConfigEnvironment:
    """ConfigEnvironment 열거형 테스트 클래스"""

    def test_from_string_development(self):
        assert (
            ConfigEnvironment.from_string("development")
            == ConfigEnvironment.DEVELOPMENT
        )
        assert ConfigEnvironment.from_string("dev") == ConfigEnvironment.DEVELOPMENT

    def test_from_string_testing(self):
        assert ConfigEnvironment.from_string("testing") == ConfigEnvironment.TESTING
        assert ConfigEnvironment.from_string("test") == ConfigEnvironment.TESTING

    def test_from_string_production(self):
        assert (
            ConfigEnvironment.from_string("production") == ConfigEnvironment.PRODUCTION
        )
        assert ConfigEnvironment.from_string("prod") == ConfigEnvironment.PRODUCTION

    def test_from_string_case_insensitive(self):
        assert (
            ConfigEnvironment.from_string("DEVELOPMENT")
            == ConfigEnvironment.DEVELOPMENT
        )
        assert ConfigEnvironment.from_string("Testing") == ConfigEnvironment.TESTING
        assert (
            ConfigEnvironment.from_string("Production") == ConfigEnvironment.PRODUCTION
        )

    def test_from_string_unknown(self):
        assert ConfigEnvironment.from_string("unknown") == ConfigEnvironment.DEVELOPMENT
        assert ConfigEnvironment.from_string("") == ConfigEnvironment.DEVELOPMENT


class TestConfig:
    """Config 클래스 테스트"""

    def test_init_empty(self):
        config = Config()
        assert config._config == {}

    def test_init_with_data(self):
        data = {"key1": "value1", "key2": {"nested": "value2"}}
        config = Config(data)
        assert config._config == data
        # 깊은 복사 확인
        assert config._config is not data

    @mock.patch.dict(os.environ, {"APP_ENV": "production"})
    def test_environment_from_env_var(self):
        config = Config()
        assert config.environment == ConfigEnvironment.PRODUCTION

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_environment_default(self):
        config = Config()
        assert config.environment == ConfigEnvironment.DEVELOPMENT

    def test_get_simple_keys(self):
        config = Config({"key1": "value1", "key2": "value2"})
        assert config.get("key1") == "value1"
        assert config.get("key2") == "value2"

    def test_get_nested_keys(self):
        config = Config(
            {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "credentials": {"username": "user", "password": "pass"},
                }
            }
        )
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432
        assert config.get("database.credentials.username") == "user"
        assert config.get("database.credentials.password") == "pass"

    def test_get_default_value(self):
        config = Config({"key1": "value1"})
        assert config.get("missing_key") is None
        assert config.get("missing_key", "default") == "default"

    def test_get_nested_missing_key(self):
        config = Config({"level1": {"level2": "value"}})
        assert config.get("level1.missing") is None
        assert config.get("missing.level2") is None
        assert config.get("level1.missing", "default") == "default"

    def test_set_simple_key(self):
        config = Config()
        config.set("key1", "value1")
        assert config.get("key1") == "value1"

        # 기존 키 업데이트
        config.set("key1", "new_value")
        assert config.get("key1") == "new_value"

    def test_set_nested_key(self):
        config = Config()
        config.set("database.host", "localhost")
        assert config.get("database.host") == "localhost"

        config.set("database.credentials.username", "user")
        assert config.get("database.credentials.username") == "user"

        # 기존 중첩 구조 유지 확인
        config.set("database.port", 5432)
        assert config.get("database.port") == 5432
        assert config.get("database.host") == "localhost"  # 기존 키는 그대로 유지

    def test_set_overwrite_non_dict(self):
        config = Config({"database": "simple_value"})
        config.set("database.host", "localhost")

        # database가 딕셔너리로 변환되어야 함
        assert isinstance(config.get("database"), dict)
        assert config.get("database.host") == "localhost"

    def test_as_dict(self):
        data = {"key1": "value1", "nested": {"key2": "value2"}}
        config = Config(data)
        result = config.as_dict()

        # 딕셔너리가 반환되어야 함
        assert isinstance(result, dict)
        assert result == data

        # 깊은 복사 확인
        assert result is not config._config

        # 원본 데이터 변경이 반환된 딕셔너리에 영향을 주지 않아야 함
        result["key1"] = "changed"
        assert config.get("key1") == "value1"


class TestConfigFileOperations:
    """Config 클래스 파일 작업 테스트"""

    def test_load_from_yaml_file(self):
        # 임시 YAML 파일 생성
        yaml_content = """
        server:
          host: localhost
          port: 8080
        database:
          url: postgresql://user:pass@localhost/dbname
        """

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(yaml_content)
            temp_path = temp_file.name

        try:
            config = Config.load_from_file(temp_path)
            assert config.get("server.host") == "localhost"
            assert config.get("server.port") == 8080
            assert (
                config.get("database.url") == "postgresql://user:pass@localhost/dbname"
            )
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)

    def test_load_from_json_file(self):
        # 임시 JSON 파일 생성
        json_content = {
            "server": {"host": "localhost", "port": 8080},
            "database": {"url": "postgresql://user:pass@localhost/dbname"},
        }

        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w+", delete=False
        ) as temp_file:
            json.dump(json_content, temp_file)
            temp_path = temp_file.name

        try:
            config = Config.load_from_file(temp_path)
            assert config.get("server.host") == "localhost"
            assert config.get("server.port") == 8080
            assert (
                config.get("database.url") == "postgresql://user:pass@localhost/dbname"
            )
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)

    def test_load_with_env_specific_settings(self):
        # 환경별 설정이 있는 YAML 파일
        yaml_content = """
        server:
          host: default-host
          port: 8080
        
        development:
          server:
            host: dev-host
        
        testing:
          server:
            host: test-host
            port: 9090
        
        production:
          server:
            host: prod-host
            port: 80
        """

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(yaml_content)
            temp_path = temp_file.name

        try:
            # 개발 환경 설정 테스트
            with mock.patch.dict(os.environ, {"APP_ENV": "development"}):
                config = Config.load_from_file(temp_path)
                assert (
                    config.get("server.host") == "dev-host"
                )  # 환경별 설정으로 덮어쓰기
                assert config.get("server.port") == 8080  # 기본값 유지

            # 테스트 환경 설정 테스트
            with mock.patch.dict(os.environ, {"APP_ENV": "testing"}):
                config = Config.load_from_file(temp_path)
                assert config.get("server.host") == "test-host"
                assert config.get("server.port") == 9090

            # 운영 환경 설정 테스트
            with mock.patch.dict(os.environ, {"APP_ENV": "production"}):
                config = Config.load_from_file(temp_path)
                assert config.get("server.host") == "prod-host"
                assert config.get("server.port") == 80
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)

    def test_load_without_env_specific_settings(self):
        yaml_content = """
        server:
          host: default-host
          port: 8080
        
        development:
          server:
            host: dev-host
        """

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w+", delete=False
        ) as temp_file:
            temp_file.write(yaml_content)
            temp_path = temp_file.name

        try:
            # env_specific=False로 설정하면 환경별 설정이 적용되지 않아야 함
            with mock.patch.dict(os.environ, {"APP_ENV": "development"}):
                config = Config.load_from_file(temp_path, env_specific=False)
                assert (
                    config.get("server.host") == "default-host"
                )  # 환경별 설정이 적용되지 않음
                assert config.get("server.port") == 8080
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)

    def test_load_file_not_found(self):
        non_existent_path = "/non/existent/path/config.yml"
        with pytest.raises(ConfigError) as exc_info:
            Config.load_from_file(non_existent_path)
        assert "Config file not found" in str(exc_info.value)

    def test_load_invalid_format(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w+", delete=False
        ) as temp_file:
            temp_file.write("This is not a valid config file")
            temp_path = temp_file.name

        try:
            with pytest.raises(ConfigError) as exc_info:
                Config.load_from_file(temp_path)
            assert "Unsupported config file format" in str(exc_info.value)
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)

    def test_load_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w+", delete=False
        ) as temp_file:
            temp_file.write("invalid: yaml: content:")
            temp_path = temp_file.name

        try:
            with pytest.raises(ConfigError) as exc_info:
                Config.load_from_file(temp_path)
            assert "Failed to parse config file" in str(exc_info.value)
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)

    def test_save_to_yaml_file(self):
        config = Config(
            {
                "server": {"host": "localhost", "port": 8080},
                "database": {"url": "postgresql://user:pass@localhost/dbname"},
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "config.yaml"
            config.save_to_file(file_path)

            # 파일이 생성되었는지 확인
            assert file_path.exists()

            # 저장된 내용 확인
            with open(file_path, "r") as file:
                saved_data = yaml.safe_load(file)
                assert saved_data["server"]["host"] == "localhost"
                assert saved_data["server"]["port"] == 8080
                assert (
                    saved_data["database"]["url"]
                    == "postgresql://user:pass@localhost/dbname"
                )

    def test_save_to_json_file(self):
        config = Config(
            {
                "server": {"host": "localhost", "port": 8080},
                "database": {"url": "postgresql://user:pass@localhost/dbname"},
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "config.json"
            config.save_to_file(file_path, format="json")

            # 파일이 생성되었는지 확인
            assert file_path.exists()

            # 저장된 내용 확인
            with open(file_path, "r") as file:
                saved_data = json.load(file)
                assert saved_data["server"]["host"] == "localhost"
                assert saved_data["server"]["port"] == 8080
                assert (
                    saved_data["database"]["url"]
                    == "postgresql://user:pass@localhost/dbname"
                )

    def test_save_invalid_format(self):
        config = Config()
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "config.txt"
            with pytest.raises(ConfigError) as exc_info:
                config.save_to_file(file_path, format="txt")
            assert "Unsupported format" in str(exc_info.value)

    def test_save_to_nonexistent_directory(self):
        config = Config({"key": "value"})
        with tempfile.TemporaryDirectory() as temp_dir:
            # 중첩된 디렉토리 경로
            file_path = Path(temp_dir) / "nested" / "dir" / "config.yaml"

            # 디렉토리가 없어도 저장 가능해야 함
            config.save_to_file(file_path)

            # 파일이 생성되었는지 확인
            assert file_path.exists()

            # 저장된 내용 확인
            with open(file_path, "r") as file:
                saved_data = yaml.safe_load(file)
                assert saved_data["key"] == "value"
