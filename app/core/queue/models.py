from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class QueueStatus(str, Enum):
    waiting = "waiting"
    processing = "processing"
    done = "done"
    failed = "failed"


class QueueItem(BaseModel):
    id: str
    article_id: str
    status: QueueStatus = QueueStatus.waiting
    enqueued_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    priority: int
    # 기타 필드는 테스트 코드 분석 후 추가

    def mark_processing(self):
        self.status = QueueStatus.processing
        self.processed_at = None

    def mark_done(self):
        self.status = QueueStatus.done
        self.processed_at = datetime.now()

    def mark_failed(self, reason: str):
        self.status = QueueStatus.failed
        self.failed_reason = reason
        self.processed_at = datetime.now()
