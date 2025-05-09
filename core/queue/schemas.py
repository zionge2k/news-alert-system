"""
Queue 도메인 스키마

이 모듈은 Queue 도메인 모델의 데이터 검증 및 직렬화를 위한 Pydantic 스키마를 정의합니다.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from core.queue.models import QueuePriority, QueueStatus


class QueueItemBase(BaseModel):
    """대기열 항목 기본 스키마"""

    article_id: str = Field(..., description="대기열에 등록된 기사 ID")
    priority: QueuePriority = Field(
        default=QueuePriority.NORMAL, description="대기열 항목 우선순위"
    )
    scheduled_at: Optional[datetime] = Field(None, description="발행 예약 시간")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="추가 메타데이터"
    )


class QueueItemCreate(QueueItemBase):
    """대기열 항목 생성 스키마"""

    @validator("article_id")
    def article_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("article_id must not be empty")
        return v


class QueueItemUpdate(BaseModel):
    """대기열 항목 업데이트 스키마"""

    priority: Optional[QueuePriority] = Field(None, description="대기열 항목 우선순위")
    scheduled_at: Optional[datetime] = Field(None, description="발행 예약 시간")
    status: Optional[QueueStatus] = Field(None, description="대기열 항목 상태")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")
    error_message: Optional[str] = Field(None, description="실패 시 오류 메시지")


class QueueItemResponse(QueueItemBase):
    """대기열 항목 응답 스키마"""

    id: str = Field(..., description="대기열 항목 ID")
    status: QueueStatus = Field(..., description="대기열 항목 상태")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="마지막 업데이트 시간")
    processed_at: Optional[datetime] = Field(None, description="처리 완료 시간")
    error_message: Optional[str] = Field(None, description="실패 시 오류 메시지")

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "article_id": "123e4567-e89b-12d3-a456-426614174001",
                "status": "pending",
                "priority": 1,
                "scheduled_at": "2023-01-01T12:00:00",
                "created_at": "2023-01-01T10:00:00",
                "updated_at": "2023-01-01T10:00:00",
                "processed_at": None,
                "metadata": {"channel": "discord", "target": "news-alerts"},
                "error_message": None,
            }
        }


class QueueItemList(BaseModel):
    """대기열 항목 목록 스키마"""

    items: List[QueueItemResponse] = Field(..., description="대기열 항목 목록")
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
                        "status": "pending",
                        "priority": 1,
                        "scheduled_at": "2023-01-01T12:00:00",
                        "created_at": "2023-01-01T10:00:00",
                        "updated_at": "2023-01-01T10:00:00",
                        "processed_at": None,
                        "metadata": {"channel": "discord", "target": "news-alerts"},
                        "error_message": None,
                    }
                ],
                "total": 42,
                "page": 1,
                "size": 10,
            }
        }
