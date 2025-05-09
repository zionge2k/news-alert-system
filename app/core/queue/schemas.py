from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .models import QueueStatus


class QueueItemCreate(BaseModel):
    article_id: str
    priority: int


class QueueItemUpdate(BaseModel):
    status: Optional[QueueStatus] = None
    priority: Optional[int] = None
    failed_reason: Optional[str] = None


class QueueItemResponse(BaseModel):
    id: str
    article_id: str
    status: QueueStatus
    enqueued_at: datetime
    processed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    priority: int


class QueueListResponse(BaseModel):
    items: List[QueueItemResponse]
    total: int
