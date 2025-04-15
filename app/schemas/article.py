from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# T는 공변성을 갖는 타입 변수
T = TypeVar("T", covariant=True)


class ArticleDTO(BaseModel, Generic[T]):
    """
    뉴스 기사 DTO 모델

    공변성을 만족하는 제네릭 설계로, 확장 가능한 뉴스 기사 데이터 구조 제공
    """

    title: str
    url: str
    platform: str
    author: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None  # 기사가 실제로 발행된 시간
    created_at: datetime = Field(
        default_factory=datetime.now
    )  # 시스템에서 기사를 수집한 시간
    updated_at: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "속보: 중요 뉴스입니다",
                "url": "https://news.example.com/article/12345",
                "platform": "JTBC",
                "author": "홍길동",
                "content": "뉴스 본문 내용...",
                "category": "정치",
                "tags": ["속보", "정치", "대통령"],
                "published_at": "2023-07-01T10:00:00",
                "created_at": "2023-07-01T12:30:00",
            }
        }
