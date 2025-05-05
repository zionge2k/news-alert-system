"""
로깅 유틸리티 모듈

이 모듈은 애플리케이션 전체에서 일관된 로깅을 위한 유틸리티를 제공합니다.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

# 기본 로그 레벨 설정
DEFAULT_LOG_LEVEL = logging.INFO
LOG_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# 기본 로그 형식 설정
DEFAULT_FORMAT = "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 루트 로거의 기본 구성
logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format=DEFAULT_FORMAT,
    datefmt=DEFAULT_DATE_FORMAT,
)


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    이름 기반 로거를 반환합니다. 일반적으로 모듈 이름을 넘겨줍니다.

    Args:
        name: 로거 이름 (일반적으로 __name__)
        log_level: 로그 레벨 ('debug', 'info', 'warning', 'error', 'critical')

    Returns:
        logging.Logger: 설정된 로거 인스턴스

    예:
        logger = get_logger(__name__, 'debug')
    """
    logger = logging.getLogger(name)

    # 환경 변수 또는 직접 지정된 로그 레벨 설정
    if log_level is None:
        env_log_level = os.environ.get("LOG_LEVEL", "").lower()
        if env_log_level in LOG_LEVEL_MAP:
            logger.setLevel(LOG_LEVEL_MAP[env_log_level])
    else:
        logger.setLevel(LOG_LEVEL_MAP.get(log_level.lower(), DEFAULT_LOG_LEVEL))

    return logger


def setup_file_logging(
    file_path: str,
    log_level: Optional[str] = None,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    format_str: Optional[str] = None,
) -> None:
    """
    파일 로깅을 설정합니다.

    Args:
        file_path: 로그 파일 경로
        log_level: 로그 레벨 ('debug', 'info', 'warning', 'error', 'critical')
        max_size: 파일당 최대 크기 (바이트)
        backup_count: 유지할 백업 파일 수
        format_str: 로그 포맷 문자열 (None이면 기본값 사용)
    """
    # 로그 디렉토리 생성
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 로그 레벨 설정
    level = (
        LOG_LEVEL_MAP.get(log_level.lower(), DEFAULT_LOG_LEVEL)
        if log_level
        else DEFAULT_LOG_LEVEL
    )

    # 로그 포맷 설정
    formatter = logging.Formatter(
        format_str or DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT
    )

    # 파일 핸들러 설정
    file_handler = RotatingFileHandler(
        file_path, maxBytes=max_size, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # 루트 로거에 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
