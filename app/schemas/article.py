from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


class ArticleMetadata(BaseModel):
    """기본 뉴스 기사 메타데이터 모델

    모든 플랫폼별 메타데이터 클래스가 상속받아야 하는 기본 클래스입니다.
    뉴스 기사의 분류, 태깅, 시간 정보 등 부가적인 데이터를 담습니다.

    Attributes:
        platform: 뉴스 플랫폼 (예: MBC, YTN, JTBC)
        category: 뉴스 카테고리 (예: 정치, 경제, 사회)
        tags: 기사 관련 태그 목록
        published_at: 기사가 언론사 플랫폼에 발행된 시간
        created_at: 시스템에서 기사를 수집한 시간
        updated_at: 기사 정보가 마지막으로 업데이트된 시간
    """

    platform: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


# ArticleMetadata를 상속받는 타입만 허용하는 제네릭 타입 변수
T = TypeVar("T", bound=ArticleMetadata)


class ArticleDTO(BaseModel, Generic[T]):
    """뉴스 기사 DTO (Data Transfer Object) 모델

    뉴스 기사의 기본 정보와 플랫폼별 메타데이터를 포함하는 DTO입니다.
    제네릭 타입 T를 통해 플랫폼별로 다른 메타데이터 구조를 가질 수 있습니다.

    기본 필드(title, url, author, content)는 모든 플랫폼에서 공통적으로 사용되며,
    플랫폼별 특수한 정보는 metadata 필드를 통해 확장할 수 있습니다.

    Example:
        ```python
        class NaverMetadata(ArticleMetadata):
            press_id: str
            article_id: str

        article = ArticleDTO[NaverMetadata](
            title="뉴스 제목",
            url="https://...",
            author="김기자",
            metadata=NaverMetadata(
                platform="NAVER",
                press_id="032",
                article_id="0001234567"
            )
        )
        ```

    Attributes:
        title: 기사 제목
        url: 기사 원문 URL
        author: 기자 이름 (Optional)
        content: 기사 본문 (Optional)
        metadata: 플랫폼별 메타데이터
    """

    title: str
    url: str
    author: Optional[str] = None
    content: Optional[str] = None
    metadata: T

    class Config:
        schema_extra = {
            "example": {
                "title": "속보: 중요 뉴스입니다",
                "url": "https://news.example.com/article/12345",
                "author": "홍길동",
                "content": "뉴스 본문 내용...",
                "metadata": {
                    "platform": "JTBC",
                    "category": "정치",
                    "tags": ["속보", "정치", "대통령"],
                    "published_at": "2023-07-01T10:00:00",
                    "created_at": "2023-07-01T12:30:00",
                },
            }
        }
