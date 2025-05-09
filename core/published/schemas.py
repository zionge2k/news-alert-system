"""
Published 도메인 스키마

이 모듈은 Published 도메인 모델의 데이터 검증 및 직렬화를 위한 Pydantic 스키마를 정의합니다.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from core.published.models import PublishedStatus


class PublishedArticleBase(BaseModel):
    """발행된 기사 기본 스키마"""

    article_id: str = Field(..., description="발행된 기사의 ID")
    platform: str = Field(..., description="발행 플랫폼 (discord, slack 등)")
    channel_id: Optional[str] = Field(None, description="발행된 채널 ID")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="추가 메타데이터"
    )


class PublishedArticleCreate(PublishedArticleBase):
    """발행된 기사 생성 스키마"""

    @validator("article_id")
    def article_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("article_id must not be empty")
        return v

    @validator("platform")
    def platform_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("platform must not be empty")
        return v


class PublishedArticleUpdate(BaseModel):
    """발행된 기사 업데이트 스키마"""

    status: Optional[PublishedStatus] = Field(None, description="발행 상태")
    channel_id: Optional[str] = Field(None, description="발행된 채널 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")


class PublishedArticleResponse(PublishedArticleBase):
    """발행된 기사 응답 스키마"""

    id: str = Field(..., description="발행 항목 ID")
    status: PublishedStatus = Field(..., description="발행 상태")
    published_at: datetime = Field(..., description="발행 시간")
    archived_at: Optional[datetime] = Field(None, description="보관 시간")
    deleted_at: Optional[datetime] = Field(None, description="삭제 시간")

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "article_id": "123e4567-e89b-12d3-a456-426614174001",
                "platform": "discord",
                "status": "published",
                "published_at": "2023-01-01T12:00:00",
                "archived_at": None,
                "deleted_at": None,
                "channel_id": "123456789012345678",
                "metadata": {"message_id": "987654321098765432"},
            }
        }


class PublishedArticleList(BaseModel):
    """발행된 기사 목록 스키마"""

    items: List[PublishedArticleResponse] = Field(..., description="발행된 기사 목록")
    total: int = Field(..., description="전체 항목 수")
    page: int = Field(1, description="현재 페이지 번호")
    size: int = Field(10, description="페이지 크기")

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "article_id": "123e4567-e89b-12d3-a456-426614174001",
                        "platform": "discord",
                        "status": "published",
                        "published_at": "2023-01-01T12:00:00",
                        "archived_at": None,
                        "deleted_at": None,
                        "channel_id": "123456789012345678",
                        "metadata": {"message_id": "987654321098765432"},
                    }
                ],
                "total": 42,
                "page": 1,
                "size": 10,
            }
        }
