"""
인프라 호환성 레이어: 기존 코드가 새로운 인프라 계층으로 마이그레이션하는 동안 호환성을 제공합니다.

이 모듈은 레거시 API와 새로운 인프라 계층 사이의 어댑터를 제공하여
점진적인 마이그레이션이 가능하도록 합니다.
"""

import functools
import logging
import warnings
from typing import Any, Dict, List, Optional, Union

# 레거시 DB 모듈
import db.mongodb as legacy_mongodb
import infra
from infra import (
    AioHttpClient,
    DiscordClient,
    HttpClient,
    Message,
    MongoDB,
    create_mongodb_connection,
)

logger = logging.getLogger(__name__)


# MongoDB 어댑터
class MongoDBAdapter:
    """
    기존 db.mongodb.MongoDB 클래스와 새로운 infra.database.MongoDB 클래스 사이의 어댑터.
    """

    _instance = None
    _mongodb = None

    @classmethod
    def get_instance(cls) -> "MongoDBAdapter":
        """싱글톤 인스턴스를 반환합니다."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """
        새 인프라의 MongoDB 인스턴스를 생성합니다.
        """
        # 기존 환경 변수와 동일한 방식으로 연결
        self._mongodb = create_mongodb_connection()

    async def connect(
        self, mongodb_url: Optional[str] = None, db_name: Optional[str] = None
    ) -> None:
        """
        MongoDB에 연결합니다. 기존 db.mongodb.MongoDB.connect() 메서드와 호환됩니다.

        Args:
            mongodb_url: MongoDB 연결 URL (기본값: 환경 변수에서 가져옴)
            db_name: 사용할 데이터베이스 이름 (기본값: 환경 변수에서 가져옴)
        """
        if mongodb_url or db_name:
            # 파라미터가 명시적으로 지정된 경우 새 연결 생성
            self._mongodb = create_mongodb_connection(uri=mongodb_url, database=db_name)

        # 연결
        await self._mongodb.connect()
        logger.info("MongoDB에 연결되었습니다.")

    async def close(self) -> None:
        """
        MongoDB 연결을 종료합니다. 기존 db.mongodb.MongoDB.close() 메서드와 호환됩니다.
        """
        if self._mongodb:
            await self._mongodb.disconnect()
            logger.info("MongoDB 연결이 종료되었습니다.")

    def get_database(self):
        """
        데이터베이스 인스턴스를 반환합니다. 기존 db.mongodb.MongoDB.get_database() 메서드와 호환됩니다.

        Returns:
            MongoDB 인스턴스

        Raises:
            ConnectionError: MongoDB 연결이 없는 경우
        """
        if not self._mongodb:
            logger.error("MongoDB에 연결되어 있지 않습니다.")
            raise ConnectionError(
                "MongoDB에 연결되어 있지 않습니다. connect() 메서드를 먼저 호출하세요."
            )
        return self._mongodb

    def get_collection(self, collection_name: str):
        """
        컬렉션을 반환합니다. 기존 db.mongodb.MongoDB.get_collection() 메서드와 호환됩니다.

        Args:
            collection_name: 컬렉션 이름

        Returns:
            MongoDB의 컬렉션 객체
        """
        return collection_name  # 실제로는 필요하지 않음, 새 API에서는 컬렉션 이름만 문자열로 받음


# 기존 MongoDB 클래스와 인터페이스 일치를 위해 속성 재정의
MongoDB.client = property(lambda self: self._client)
MongoDB.db = property(lambda self: self._db)
MongoDB.DB_NAME = legacy_mongodb.MongoDB.DB_NAME
MongoDB.DEFAULT_URL = legacy_mongodb.MongoDB.DEFAULT_URL


# HTTP 클라이언트 어댑터
class HTTPClientAdapter:
    """
    레거시 HTTP 클라이언트와 새로운 AioHttpClient 사이의 어댑터.
    """

    def __init__(
        self, base_url: str = "", timeout: int = 30, headers: Dict[str, str] = None
    ):
        """
        AioHttpClient 인스턴스를 생성합니다.

        Args:
            base_url: 모든 요청의 기본 URL
            timeout: 요청 타임아웃(초)
            headers: 모든 요청에 포함할 기본 헤더
        """
        self._client = AioHttpClient(
            base_url=base_url, timeout=timeout, default_headers=headers or {}
        )

    async def __aenter__(self):
        """비동기 컨텍스트 관리자 진입."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 관리자 종료."""
        await self.close()

    async def close(self):
        """클라이언트 세션을 종료합니다."""
        await self._client.close()

    async def get(self, url: str, **kwargs):
        """
        GET 요청을 수행합니다.

        Args:
            url: 요청 URL
            **kwargs: 추가 요청 옵션

        Returns:
            응답 데이터(딕셔너리)
        """
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, data=None, json=None, **kwargs):
        """
        POST 요청을 수행합니다.

        Args:
            url: 요청 URL
            data: 폼 데이터
            json: JSON 데이터
            **kwargs: 추가 요청 옵션

        Returns:
            응답 데이터(딕셔너리)
        """
        return await self._client.post(url, data=data, json_data=json, **kwargs)

    async def put(self, url: str, data=None, json=None, **kwargs):
        """
        PUT 요청을 수행합니다.

        Args:
            url: 요청 URL
            data: 폼 데이터
            json: JSON 데이터
            **kwargs: 추가 요청 옵션

        Returns:
            응답 데이터(딕셔너리)
        """
        return await self._client.put(url, data=data, json_data=json, **kwargs)

    async def delete(self, url: str, **kwargs):
        """
        DELETE 요청을 수행합니다.

        Args:
            url: 요청 URL
            **kwargs: 추가 요청 옵션

        Returns:
            응답 데이터(딕셔너리)
        """
        return await self._client.delete(url, **kwargs)


# 몽고디비 레거시 함수 어댑터
async def init_mongodb(
    mongodb_url: Optional[str] = None, db_name: Optional[str] = None
) -> None:
    """
    MongoDB 연결을 초기화합니다. 기존 db.mongodb.init_mongodb() 함수와 호환됩니다.

    Args:
        mongodb_url: MongoDB 연결 URL (기본값: 환경 변수에서 가져옴)
        db_name: 사용할 데이터베이스 이름 (기본값: 환경 변수에서 가져옴)
    """
    adapter = MongoDBAdapter.get_instance()
    await adapter.connect(mongodb_url, db_name)


async def close_mongodb() -> None:
    """
    MongoDB 연결을 종료합니다. 기존 db.mongodb.close_mongodb() 함수와 호환됩니다.
    """
    adapter = MongoDBAdapter.get_instance()
    await adapter.close()


def deprecated_import_warning(func):
    """
    더 이상 사용되지 않는 임포트에 대한 경고를 표시하는 데코레이터.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__}은(는) 더 이상 사용되지 않습니다. 새로운 인프라 모듈을 직접 사용하세요.",
            DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper
