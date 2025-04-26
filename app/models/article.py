"""
MongoDB 기사 문서 모델 정의

이 모듈은 MongoDB에 저장될 기사 문서 모델을 정의합니다.
Pydantic을 사용하여 스키마를 정의하고, Motor를 통해 MongoDB와 직접 상호작용합니다.
"""

from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    model_validator,
)

from app.schemas.article import ArticleDTO
from common.utils.logger import get_logger

logger = get_logger(__name__)


class MongoArticleMetadata(BaseModel):
    """
    MongoDB에 저장될 기사 메타데이터 모델

    이 클래스는 app.schemas.article.ArticleMetadata를 기반으로 하지만,
    MongoDB 문서 모델에 맞게 조정되었습니다.

    Attributes:
        platform: 뉴스 플랫폼 (예: MBC, YTN, JTBC)
        category: 뉴스 카테고리 (예: 정치, 경제, 사회)
        tags: 기사 관련 태그 목록
        published_at: 기사가 언론사 플랫폼에 발행된 시간
        collected_at: 시스템에서 기사를 수집한 시간
        updated_at: 기사 정보가 마지막으로 업데이트된 시간
        article_id: 플랫폼별 기사 고유 ID
        platform_specific: 플랫폼별 특수 메타데이터를 저장하는 사전
    """

    # 모델 설정
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    platform: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    article_id: Optional[str] = None  # 플랫폼별 기사 ID
    platform_specific: Dict[str, Any] = Field(
        default_factory=dict
    )  # 플랫폼별 추가 정보

    @field_serializer("published_at", "collected_at", "updated_at")
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """datetime 객체를 ISO 형식 문자열로 직렬화합니다."""
        if dt is None:
            return None
        return dt.isoformat()


class ArticleModel(BaseModel):
    """
    MongoDB에 저장될 기사 문서 모델

    이 모델은 app.schemas.article.ArticleDTO를 기반으로 하지만,
    MongoDB 문서로 저장되기 위해 필요한 필드와 메서드를 추가했습니다.

    Attributes:
        title: 기사 제목
        url: 기사 원문 URL
        author: 기자 이름
        content: 기사 본문
        metadata: 기사 메타데이터
        unique_id: 기사 식별을 위한 복합키 (platform_article_id)
        created_at: 문서 생성 시간
        updated_at: 문서 업데이트 시간
    """

    # 모델 설정
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={"collection_name": "articles"},
    )

    title: str
    url: str
    author: Optional[str] = None
    content: Optional[str] = None
    metadata: MongoArticleMetadata
    unique_id: str  # platform_article_id 형식의 복합키
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    # 클래스 변수 정의
    collection_name: ClassVar[str] = "articles"

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """datetime 객체를 ISO 형식 문자열로 직렬화합니다."""
        if dt is None:
            return None
        return dt.isoformat()

    @classmethod
    def from_article_dto(cls, article_dto: ArticleDTO) -> "ArticleModel":
        """
        ArticleDTO를 ArticleModel로 변환합니다.

        Args:
            article_dto: 변환할 ArticleDTO 인스턴스

        Returns:
            ArticleModel 인스턴스
        """
        metadata_dict = article_dto.metadata.model_dump()

        # 기본 메타데이터 필드 추출
        base_metadata = {
            "platform": metadata_dict.pop("platform"),
            "category": metadata_dict.pop("category", None),
            "tags": metadata_dict.pop("tags", []),
            "published_at": metadata_dict.pop("published_at", None),
            "collected_at": metadata_dict.pop("collected_at", datetime.now()),
            "updated_at": metadata_dict.pop("updated_at", None),
        }

        # article_id 추출 (플랫폼별 메타데이터에 존재할 경우)
        article_id = metadata_dict.pop("article_id", None)
        if article_id:
            base_metadata["article_id"] = article_id

        # 나머지 플랫폼별 특수 필드는 platform_specific에 저장
        base_metadata["platform_specific"] = metadata_dict

        # 복합키 생성 (platform_article_id)
        platform = base_metadata["platform"]
        if article_id:
            unique_id = f"{platform}_{article_id}"
        else:
            # article_id가 없는 경우 URL을 해시화하여 사용
            import hashlib

            url_hash = hashlib.md5(article_dto.url.encode()).hexdigest()
            unique_id = f"{platform}_{url_hash}"

        return cls(
            title=article_dto.title,
            url=article_dto.url,
            author=article_dto.author,
            content=article_dto.content,
            metadata=MongoArticleMetadata(**base_metadata),
            unique_id=unique_id,
            created_at=datetime.now(),
        )

    def to_article_dto(self) -> dict:
        """
        ArticleModel을 딕셔너리로 변환합니다.
        (완전한 ArticleDTO 변환은 플랫폼별 메타데이터 클래스가 필요하므로 딕셔너리 반환)

        Returns:
            ArticleDTO 형식의 딕셔너리
        """
        metadata_dict = self.metadata.model_dump()

        # platform_specific의 내용을 메타데이터 최상위로 이동
        platform_specific = metadata_dict.pop("platform_specific", {})
        metadata_dict.update(platform_specific)

        return {
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "content": self.content,
            "metadata": metadata_dict,
        }

    def to_document(self) -> Dict[str, Any]:
        """
        ArticleModel을 MongoDB 문서 형식으로 변환합니다.

        Returns:
            MongoDB 문서로 변환된 딕셔너리
        """
        return self.model_dump(by_alias=True)

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "ArticleModel":
        """
        MongoDB 문서를 ArticleModel로 변환합니다.

        Args:
            document: MongoDB 문서 딕셔너리

        Returns:
            ArticleModel 인스턴스
        """
        # MongoDB의 _id 필드 제거 (Pydantic 모델에 없음)
        if "_id" in document:
            document.pop("_id")

        return cls.model_validate(document)

    @model_validator(mode="before")
    @classmethod
    def process_mongodb_id(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        MongoDB에서 가져온 데이터를 처리하기 위한 검증기

        특히 _id 필드를 처리합니다.

        Args:
            data: 입력 데이터

        Returns:
            처리된 데이터
        """
        # _id 필드가 있으면 제거
        if isinstance(data, dict) and "_id" in data:
            data.pop("_id")

        return data


async def create_article_indexes(db):
    """
    ArticleModel이 사용할 인덱스를 생성합니다.

    Args:
        db: AsyncIOMotorDatabase 인스턴스
    """
    from pymongo.errors import OperationFailure

    try:
        # 1. 기존 인덱스 정보 조회
        existing_indexes = await db[ArticleModel.collection_name].index_information()
        logger.info(f"기존 인덱스: {list(existing_indexes.keys())}")

        # 2. unique_id 유니크 인덱스 생성 (복합키 기반 중복 검사)
        if "unique_id_1" not in existing_indexes:
            try:
                await db[ArticleModel.collection_name].create_index(
                    "unique_id", unique=True
                )
                logger.info("unique_id 유니크 인덱스 생성 완료")
            except OperationFailure as e:
                logger.warning(f"unique_id 인덱스 생성 실패: {str(e)}")
                # 충돌 시 이전 인덱스 삭제 후 재시도
                try:
                    await db[ArticleModel.collection_name].drop_index("unique_id_1")
                    await db[ArticleModel.collection_name].create_index(
                        "unique_id", unique=True
                    )
                    logger.info("unique_id 인덱스 재생성 완료")
                except Exception as inner_e:
                    logger.error(f"인덱스 재생성 중 오류: {str(inner_e)}")

        # 3. URL 인덱스 (존재하면 skip, 없으면 추가)
        if "url_1" not in existing_indexes:
            await db[ArticleModel.collection_name].create_index("url")
            logger.info("url 인덱스 생성 완료")

        # 4. 제목과 내용에 대한 텍스트 인덱스
        if not any("title_text" in idx for idx in existing_indexes.keys()):
            await db[ArticleModel.collection_name].create_index(
                [("title", "text"), ("content", "text")]
            )
            logger.info("텍스트 인덱스 생성 완료")

        # 5. 발행 시간 기준 정렬을 위한 인덱스
        if "metadata.published_at_-1" not in existing_indexes:
            await db[ArticleModel.collection_name].create_index(
                [("metadata.published_at", -1)]
            )
            logger.info("published_at 인덱스 생성 완료")

        # 6. 플랫폼 기준 필터링을 위한 인덱스
        if "metadata.platform_1" not in existing_indexes:
            await db[ArticleModel.collection_name].create_index("metadata.platform")
            logger.info("platform 인덱스 생성 완료")

        logger.info("인덱스 생성 작업 완료")

    except Exception as e:
        logger.error(f"인덱스 생성 중 오류 발생: {str(e)}")
        raise
