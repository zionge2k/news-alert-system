"""
발행된 기사 관리 모델 정의 모듈

이 모듈은 다양한 플랫폼(Discord, Slack 등)에 발행된 기사를 추적하기 위한 모델을 정의합니다.
발행 이력을 관리하여 기사가 중복 발행되는 것을 방지합니다.
"""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field

from common.utils.logger import get_logger

logger = get_logger(__name__)


class PublishStatus(str, Enum):
    """
    기사 발행 상태를 나타내는 열거형
    """

    SUCCESS = "success"  # 발행 성공
    FAILED = "failed"  # 발행 실패
    DELETED = "deleted"  # 발행 후 삭제됨


class PublishedArticle(BaseModel):
    """
    발행된 기사 정보를 저장하는 모델

    다양한 플랫폼에 발행된 기사의 정보를 기록하여 중복 발행을 방지하고
    발행 이력을 관리합니다.

    Attributes:
        unique_id: 원본 기사의 고유 ID
        platform: 발행 플랫폼 (discord, slack, email 등)
        published_at: 발행 시간
        channel_id: 발행된 채널 ID (플랫폼별로 다른 의미를 가질 수 있음)
        status: 발행 상태
        retry_count: 발행 시도 횟수
    """

    # 모델 설정
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={"collection_name": "published_articles"},
    )

    # 필수 필드
    unique_id: str = Field(..., description="원본 기사의 고유 ID")
    platform: str = Field(..., description="발행 플랫폼 (discord, slack, email 등)")

    # 선택 필드
    published_at: datetime = Field(
        default_factory=datetime.now, description="발행 시간"
    )
    channel_id: Optional[str] = Field(None, description="발행된 채널 ID")
    status: str = Field(default=PublishStatus.SUCCESS.value, description="발행 상태")
    retry_count: int = Field(default=0, description="발행 시도 횟수")

    # 클래스 변수 정의
    collection_name: ClassVar[str] = "published_articles"

    def to_document(self):
        """
        MongoDB 문서로 변환합니다.

        Returns:
            dict: MongoDB에 저장할 문서 형식
        """
        return self.model_dump(by_alias=True)

    @classmethod
    def from_document(cls, document):
        """
        MongoDB 문서에서 객체를 생성합니다.

        Args:
            document: MongoDB 문서 딕셔너리

        Returns:
            PublishedArticle: 생성된 객체
        """
        # MongoDB _id 필드 제거 (Pydantic 모델에 없음)
        if "_id" in document:
            document = document.copy()
            document.pop("_id")

        return cls.model_validate(document)


async def create_published_article_indexes(db):
    """
    PublishedArticle 모델을 위한 MongoDB 인덱스를 생성합니다.

    Args:
        db: AsyncIOMotorDatabase 인스턴스
    """
    from pymongo import ASCENDING, DESCENDING

    try:
        # 기존 인덱스 확인
        existing_indexes = await db[
            PublishedArticle.collection_name
        ].index_information()
        logger.info(f"기존 인덱스: {list(existing_indexes.keys())}")

        # 1. 고유 인덱스: unique_id + platform 조합으로 중복 방지
        if "unique_id_1_platform_1" not in existing_indexes:
            await db[PublishedArticle.collection_name].create_index(
                [("unique_id", ASCENDING), ("platform", ASCENDING)], unique=True
            )
            logger.info("unique_id + platform 복합 유니크 인덱스 생성 완료")

        # 2. 플랫폼 별 조회를 위한 인덱스
        if "platform_1_status_1" not in existing_indexes:
            await db[PublishedArticle.collection_name].create_index(
                [("platform", ASCENDING), ("status", ASCENDING)]
            )
            logger.info("platform + status 복합 인덱스 생성 완료")

        # 3. 발행 시간 기준 정렬 인덱스
        if "published_at_-1" not in existing_indexes:
            await db[PublishedArticle.collection_name].create_index(
                [("published_at", DESCENDING)]
            )
            logger.info("published_at 인덱스 생성 완료")

        logger.info("발행 기사 인덱스 생성 작업 완료")

    except Exception as e:
        logger.error(f"발행 기사 인덱스 생성 중 오류 발생: {str(e)}")
        raise
