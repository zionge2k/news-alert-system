"""
어댑터 모듈 - 기존 코드와 새 코드 사이의 호환성 계층.

이 패키지는 레거시 코드가 새로운 구조로 마이그레이션하는 동안
기존 API 호출을 유지할 수 있도록 하는 어댑터를 제공합니다.
"""

from adapters.infra import (
    HTTPClientAdapter,
    MongoDBAdapter,
    close_mongodb,
    init_mongodb,
)
from adapters.repository_adapter import article_repository

__all__ = [
    "article_repository",
    "MongoDBAdapter",
    "HTTPClientAdapter",
    "init_mongodb",
    "close_mongodb",
]
