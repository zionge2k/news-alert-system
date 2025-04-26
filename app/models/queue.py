"""
MongoDB 큐 모델 정의 모듈

이 모듈은 MongoDB를 사용하여 큐 기능을 구현하기 위한 모델을 정의합니다.
뉴스 기사를 Discord에 발행하기 전에 버퍼링하고 중복 방지 기능을 제공합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.article import ArticleModel

# 큐 컬렉션 이름 상수
QUEUE_COLLECTION_NAME = "queue_items"


def get_queue_collection_name() -> str:
    """
    MongoDB 큐 컬렉션 이름을 반환합니다.

    Returns:
        str: 큐 컬렉션 이름
    """
    return QUEUE_COLLECTION_NAME


class QueueStatus(str, Enum):
    """
    큐 아이템의 상태를 나타내는 열거형
    """

    PENDING = "pending"  # 대기 중
    PROCESSING = "processing"  # 처리 중
    COMPLETED = "completed"  # 완료됨
    FAILED = "failed"  # 실패


class QueueItem(BaseModel):
    """
    뉴스 기사 큐 아이템 모델

    MongoDB에 저장되는 큐 아이템을 나타내며, 기사를 Discord에 발행하기 전까지 보관합니다.
    """

    # 모델 설정
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_schema_extra={"collection_name": QUEUE_COLLECTION_NAME},
    )

    # 필수 필드
    article_id: str = Field(..., description="MongoDB에 저장된 원본 기사의 ID")
    platform: str = Field(..., description="뉴스 플랫폼(네이버, 다음 등)")
    title: str = Field(..., description="기사 제목")
    url: str = Field(..., description="기사 URL")
    unique_id: str = Field(..., description="고유 식별자 (URL 기반 생성)")

    # 선택 필드
    content: Optional[str] = Field(None, description="기사 본문 요약")
    category: Optional[str] = Field(None, description="기사 카테고리")
    published_at: Optional[datetime] = Field(None, description="Discord에 발행된 시간")

    # 상태 관련 필드
    status: str = Field(default=QueueStatus.PENDING.value, description="큐 아이템 상태")
    retry_count: int = Field(default=0, description="재시도 횟수")
    error_message: Optional[str] = Field(None, description="실패 시 오류 메시지")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: datetime = Field(
        default_factory=datetime.now, description="마지막 업데이트 시간"
    )

    def to_document(self) -> Dict[str, Any]:
        """
        MongoDB 문서로 변환

        Returns:
            Dict[str, Any]: MongoDB에 저장할 문서 형식
        """
        return self.model_dump(by_alias=True)

    @classmethod
    def process_mongodb_id(cls, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        MongoDB 문서에서 _id 필드를 처리하여 Pydantic 모델에 맞게 변환

        Args:
            document: MongoDB 문서

        Returns:
            Dict[str, Any]: _id 필드가 처리된 문서
        """
        # MongoDB _id 필드 제거 (Pydantic 모델에 없음)
        if "_id" in document:
            document = document.copy()
            document.pop("_id")

        return document

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "QueueItem":
        """
        MongoDB 문서에서 QueueItem 객체 생성

        Args:
            document: MongoDB 문서

        Returns:
            QueueItem: 생성된 큐 아이템 객체
        """
        # MongoDB _id 필드 제거 및 모델 검증
        processed_doc = cls.process_mongodb_id(document)
        return cls.model_validate(processed_doc)

    @classmethod
    def create_from_article(cls, article: ArticleModel) -> "QueueItem":
        """
        ArticleModel에서 QueueItem 생성

        Args:
            article: ArticleModel 인스턴스

        Returns:
            QueueItem: 생성된 큐 아이템

        Raises:
            ValueError: article이 ArticleModel 인스턴스가 아닌 경우
        """
        if not isinstance(article, ArticleModel):
            raise ValueError(
                f"article은 ArticleModel 인스턴스여야 합니다. 받은 타입: {type(article)}"
            )

        # article의 _id 필드 확인
        article_id = str(getattr(article, "_id", None))
        if not article_id:
            # _id가 없는 경우 unique_id 사용
            article_id = article.unique_id

        # 카테고리 정보 추출
        category = (
            article.metadata.category if hasattr(article.metadata, "category") else None
        )

        # 컨텐츠 필드 확인
        content = article.content

        return cls(
            article_id=article_id,
            platform=article.metadata.platform,
            title=article.title,
            url=article.url,
            unique_id=article.unique_id,
            content=content,
            category=category,
        )


async def create_queue_indexes(db):
    """
    QueueItem 모델이 사용할 인덱스를 생성합니다.

    Args:
        db: AsyncIOMotorDatabase 인스턴스
    """
    from pymongo import ASCENDING, DESCENDING

    from common.utils.logger import get_logger

    logger = get_logger(__name__)
    collection_name = get_queue_collection_name()

    try:
        # 1. 기존 인덱스 정보 조회
        existing_indexes = await db[collection_name].index_information()
        logger.info(f"기존 인덱스: {list(existing_indexes.keys())}")

        # 2. unique_id 유니크 인덱스 (중복 방지)
        if "unique_id_1" not in existing_indexes:
            await db[collection_name].create_index("unique_id", unique=True)
            logger.info("unique_id 유니크 인덱스 생성 완료")

        # 3. 상태 기반 조회를 위한 인덱스
        if "status_1" not in existing_indexes:
            await db[collection_name].create_index("status")
            logger.info("status 인덱스 생성 완료")

        # 4. 생성 시간 기준 정렬을 위한 인덱스
        if "created_at_-1" not in existing_indexes:
            await db[collection_name].create_index([("created_at", DESCENDING)])
            logger.info("created_at 인덱스 생성 완료")

        # 5. 복합 인덱스: 상태 + 생성 시간 (처리할 항목 조회 최적화)
        if "status_1_created_at_1" not in existing_indexes:
            await db[collection_name].create_index(
                [("status", ASCENDING), ("created_at", ASCENDING)]
            )
            logger.info("status+created_at 복합 인덱스 생성 완료")

    except Exception as e:
        logger.error(f"인덱스 생성 중 오류 발생: {str(e)}")
        raise
