"""
Article 도메인 스키마

이 모듈은 Article 도메인 모델의 데이터 검증 및 직렬화를 위한 Pydantic 스키마를 정의합니다.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from core.article.models import ArticleStatus


class ArticleBase(BaseModel):
    """기사 기본 스키마"""

    title: str = Field(..., description="기사 제목")
    content: str = Field(..., description="기사 본문 내용")
    source: str = Field(..., description="뉴스 출처 (예: JTBC, MBC, YTN)")
    url: Optional[str] = Field(None, description="원본 기사 URL")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="추가 메타데이터"
    )


class ArticleCreate(ArticleBase):
    """기사 생성 스키마"""

    author_id: str = Field(..., description="작성자 ID")

    @validator("title")
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("제목은 비어있을 수 없습니다")
        return v.strip()

    @validator("content")
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("내용은 비어있을 수 없습니다")
        return v


class ArticleUpdate(BaseModel):
    """기사 업데이트 스키마"""

    title: Optional[str] = Field(None, description="기사 제목")
    content: Optional[str] = Field(None, description="기사 본문 내용")
    source: Optional[str] = Field(None, description="뉴스 출처")
    url: Optional[str] = Field(None, description="원본 기사 URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")

    @validator("title")
    def title_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("제목은 비어있을 수 없습니다")
        return v.strip() if v else None


class ArticleResponse(ArticleBase):
    """기사 응답 스키마"""

    id: str = Field(..., description="기사 ID")
    author_id: str = Field(..., description="작성자 ID")
    status: ArticleStatus = Field(..., description="기사 상태")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="마지막 수정 시간")
    published_at: Optional[datetime] = Field(None, description="발행 시간")

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ArticleStatus: lambda status: status.value,
        }


class ArticleList(BaseModel):
    """기사 목록 응답 스키마"""

    items: List[ArticleResponse] = Field(..., description="기사 목록")
    total: int = Field(..., description="전체 기사 수")
    page: int = Field(1, description="현재 페이지")
    size: int = Field(..., description="페이지 크기")

    class Config:
        orm_mode = True
