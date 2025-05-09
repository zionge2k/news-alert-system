from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models import ArticleMetadata, ArticleStatus


class ArticleCreate(BaseModel):
    title: str
    url: str
    author: Optional[str] = None
    content: Optional[str] = None
    metadata: ArticleMetadata


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[ArticleMetadata] = None


class ArticleResponse(BaseModel):
    id: str
    title: str
    url: str
    author: Optional[str] = None
    content: Optional[str] = None
    metadata: ArticleMetadata
    status: ArticleStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
