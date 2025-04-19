import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.models.article import create_article_indexes

# 환경변수 로드
load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB 연결 및 관리를 담당하는 클래스"""

    # 클래스 변수로 MongoDB 클라이언트와 DB 인스턴스 관리
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    # 기본 설정값
    DB_NAME = "news_alert"
    DEFAULT_URL = "mongodb://root:1234@localhost:27017"

    @classmethod
    async def connect(
        cls, mongodb_url: Optional[str] = None, db_name: Optional[str] = None
    ) -> None:
        """
        MongoDB에 비동기 연결을 설정합니다.

        Args:
            mongodb_url: MongoDB 연결 URL. 기본값은 환경 변수나 기본 URL입니다.
            db_name: 사용할 데이터베이스 이름. 기본값은 클래스 상수나 환경 변수입니다.
        """
        # 연결 URL 결정
        _url = mongodb_url or os.getenv("MONGODB_URL", cls.DEFAULT_URL)

        # 데이터베이스 이름 결정
        _db_name = db_name or os.getenv("MONGODB_DB_NAME", cls.DB_NAME)

        try:
            # 비동기 MongoDB 클라이언트 생성
            cls.client = AsyncIOMotorClient(_url)
            cls.db = cls.client[_db_name]

            # 연결 확인을 위해 admin 데이터베이스에 ping 요청
            await cls.client.admin.command("ping")
            logger.info(f"MongoDB에 성공적으로 연결되었습니다. DB: {_db_name}")

            # 필요한 인덱스 초기화
            await cls._initialize_indexes()

        except Exception as e:
            logger.error(f"MongoDB 연결 중 오류 발생: {str(e)}")
            raise

    @classmethod
    async def close(cls) -> None:
        """MongoDB 연결을 종료합니다."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB 연결이 종료되었습니다.")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        데이터베이스 인스턴스를 반환합니다.

        Returns:
            AsyncIOMotorDatabase: MongoDB 데이터베이스 인스턴스

        Raises:
            ConnectionError: MongoDB에 연결되어 있지 않은 경우
        """
        # 객체 자체가 아닌 DB 참조가 있는지 확인
        if cls.db is None:
            logger.error("MongoDB에 연결되어 있지 않습니다.")
            raise ConnectionError(
                "MongoDB에 연결되어 있지 않습니다. connect() 메서드를 먼저 호출하세요."
            )
        return cls.db

    @classmethod
    def get_collection(cls, collection_name: str):
        """
        지정된 이름의 컬렉션을 반환합니다.

        Args:
            collection_name: 컬렉션 이름

        Returns:
            AsyncIOMotorCollection: MongoDB 컬렉션 인스턴스
        """
        return cls.get_database()[collection_name]

    @classmethod
    async def _initialize_indexes(cls) -> None:
        """필요한 인덱스를 초기화합니다."""
        try:
            # 기사 모델 인덱스 생성
            await create_article_indexes(cls.db)
            logger.info("MongoDB 인덱스가 성공적으로 생성되었습니다.")
        except Exception as e:
            logger.error(f"인덱스 생성 중 오류 발생: {str(e)}")
            raise


async def init_mongodb(
    mongodb_url: Optional[str] = None, db_name: Optional[str] = None
) -> None:
    """
    애플리케이션 시작 시 MongoDB를 초기화합니다.
    이 함수는 애플리케이션 시작 시점에 한 번 호출해야 합니다.

    Args:
        mongodb_url: MongoDB 연결 URL. 기본값은 환경 변수나 기본 URL입니다.
        db_name: 사용할 데이터베이스 이름. 기본값은 클래스 상수나 환경 변수입니다.
    """
    await MongoDB.connect(mongodb_url, db_name)
    logger.info("MongoDB가 초기화되었습니다.")


async def close_mongodb() -> None:
    """
    애플리케이션 종료 시 MongoDB 연결을 종료합니다.
    이 함수는 애플리케이션 종료 시점에 호출해야 합니다.
    """
    await MongoDB.close()
    logger.info("MongoDB 연결이 종료되었습니다.")
