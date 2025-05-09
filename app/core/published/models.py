from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PublishedStatus(str, Enum):
    published = "published"
    archived = "archived"
    deleted = "deleted"


class PublishedArticle(BaseModel):
    id: str
    article_id: str
    status: PublishedStatus = PublishedStatus.published
    published_at: datetime = Field(default_factory=datetime.now)
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def archive(self):
        self.status = PublishedStatus.archived
        self.archived_at = datetime.now()

    def soft_delete(self):
        self.status = PublishedStatus.deleted
        self.deleted_at = datetime.now()

    # 기타 필드는 테스트 코드 분석 후 추가
