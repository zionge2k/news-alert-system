from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .models import PublishedStatus


class PublishedArticleCreate(BaseModel):
    article_id: str


class PublishedArticleUpdate(BaseModel):
    status: Optional[PublishedStatus] = None


class PublishedArticleResponse(BaseModel):
    id: str
    article_id: str
    status: PublishedStatus
    published_at: datetime
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class PublishedListResponse(BaseModel):
    items: List[PublishedArticleResponse]
    total: int
