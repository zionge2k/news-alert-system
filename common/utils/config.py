"""
설정 관리 유틸리티 모듈

이 모듈은 애플리케이션 설정을 로드, 관리하기 위한 공통 기능을 제공합니다.
"""

import copy
import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union

import yaml


class ConfigEnvironment(Enum):
    """애플리케이션 실행 환경"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

    @classmethod
    def from_string(cls, env_string: str) -> "ConfigEnvironment":
        """
        문자열로부터 ConfigEnvironment 값 반환

        Args:
            env_string: 환경값을 나타내는 문자열

        Returns:
            ConfigEnvironment: 해당하는 환경 값, 일치하는 값이 없으면 DEVELOPMENT 반환
        """
        env_string = env_string.lower()

        if env_string in ("development", "dev"):
            return cls.DEVELOPMENT
        elif env_string in ("testing", "test"):
            return cls.TESTING
        elif env_string in ("production", "prod"):
            return cls.PRODUCTION

        return cls.DEVELOPMENT  # 기본값


class ConfigError(Exception):
    """설정 관련 예외"""

    pass


T = TypeVar("T", bound="Config")


class Config:
    """설정 관리 클래스"""

    def __init__(self, config_data: Dict[str, Any] = None):
        """
        Config 객체 생성

        Args:
            config_data: 초기 설정 데이터 (선택 사항)
        """
        self._config: Dict[str, Any] = copy.deepcopy(config_data) if config_data else {}

    @property
    def environment(self) -> ConfigEnvironment:
        """현재 설정된 실행 환경"""
        return self._get_environment()

    def _get_environment(self) -> ConfigEnvironment:
        """
        환경 변수 또는 설정값에서 현재 실행 환경 조회

        Returns:
            ConfigEnvironment: 현재 환경 설정
        """
        env_string = os.environ.get("APP_ENV", "development")
        return ConfigEnvironment.from_string(env_string)

    @classmethod
    def load_from_file(
        cls, file_path: Union[str, Path], env_specific: bool = True
    ) -> T:
        """
        파일에서 설정 로드

        Args:
            file_path: 설정 파일 경로
            env_specific: 환경별 설정 적용 여부

        Returns:
            Config: 설정 객체

        Raises:
            ConfigError: 설정 파일 로드 실패 시
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ConfigError(f"Config file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                if file_path.suffix.lower() in (".yaml", ".yml"):
                    config_data = yaml.safe_load(file)
                elif file_path.suffix.lower() == ".json":
                    config_data = json.load(file)
                else:
                    raise ConfigError(
                        f"Unsupported config file format: {file_path.suffix}"
                    )

                config_obj = cls(config_data)

                # 환경별 설정 적용 (예: development, testing, production 섹션)
                if env_specific and isinstance(config_data, dict):
                    env_key = config_obj.environment.name.lower()
                    if env_key in config_data:
                        # 환경별 설정으로 기본 설정 덮어쓰기
                        env_config = config_data[env_key]
                        config_obj._update_config_recursive(
                            config_obj._config, env_config
                        )

                return config_obj

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigError(
                f"Failed to parse config file {file_path}: {str(e)}"
            ) from e
        except Exception as e:
            raise ConfigError(f"Error loading config from {file_path}: {str(e)}") from e

    def _update_config_recursive(
        self, base: Dict[str, Any], update: Dict[str, Any]
    ) -> None:
        """
        설정 딕셔너리를 재귀적으로 업데이트

        Args:
            base: 업데이트할 기본 딕셔너리
            update: 새 값이 있는 딕셔너리
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # 두 값이 모두 딕셔너리인 경우 재귀적으로 병합
                self._update_config_recursive(base[key], value)
            else:
                # 그 외의 경우 값 덮어쓰기
                base[key] = copy.deepcopy(value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        설정값 조회

        Args:
            key: 설정 키 (점으로 구분된 경로 가능: 'database.host')
            default: 키가 없을 경우 반환할 기본값

        Returns:
            조회된 설정값 또는 기본값
        """
        if "." not in key:
            return self._config.get(key, default)

        # 점으로 구분된 경로 처리 (예: 'database.host')
        current = self._config
        parts = key.split(".")

        for i, part in enumerate(parts):
            if part not in current or not isinstance(current[part], dict):
                # 중간 경로가 없거나 딕셔너리가 아닌 경우
                if i == len(parts) - 1:
                    # 마지막 부분은 값이 없어도 괜찮음
                    return current.get(part, default)
                else:
                    # 중간 경로가 없으면 기본값 반환
                    return default

            current = current[part]

        return current

    def set(self, key: str, value: Any) -> None:
        """
        설정값 설정

        Args:
            key: 설정 키 (점으로 구분된 경로 가능: 'database.host')
            value: 설정할 값
        """
        if "." not in key:
            self._config[key] = value
            return

        # 점으로 구분된 경로 처리 (예: 'database.host')
        current = self._config
        parts = key.split(".")

        # 마지막 부분 제외한 모든 부분에 대해 딕셔너리 생성
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # 경로 중간이 딕셔너리가 아니면 딕셔너리로 변환
                current[part] = {}

            current = current[part]

        # 마지막 부분에 값 설정
        current[parts[-1]] = value

    def as_dict(self) -> Dict[str, Any]:
        """
        전체 설정을 딕셔너리로 반환

        Returns:
            설정 딕셔너리의 깊은 복사본
        """
        return copy.deepcopy(self._config)

    def save_to_file(self, file_path: Union[str, Path], format: str = "yaml") -> None:
        """
        설정을 파일로 저장

        Args:
            file_path: 저장할 파일 경로
            format: 파일 형식 ('yaml' 또는 'json')

        Raises:
            ConfigError: 파일 저장 실패 시
        """
        file_path = Path(file_path)

        # 디렉토리가 없으면 생성
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                if format.lower() == "yaml":
                    yaml.dump(self._config, file, default_flow_style=False)
                elif format.lower() == "json":
                    json.dump(self._config, file, indent=2, ensure_ascii=False)
                else:
                    raise ConfigError(f"Unsupported format: {format}")
        except Exception as e:
            raise ConfigError(f"Failed to save config to {file_path}: {str(e)}") from e


# 전역 설정 객체
global_config = Config()
