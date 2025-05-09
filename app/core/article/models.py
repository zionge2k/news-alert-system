from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ArticleStatus(str, Enum):
    draft = "draft"
    published = "published"
    deleted = "deleted"


class ArticleMetadata(BaseModel):
    platform: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class Article(BaseModel):
    id: str
    title: str
    url: str
    author: Optional[str] = None
    content: Optional[str] = None
    metadata: ArticleMetadata
    status: ArticleStatus = ArticleStatus.draft
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    def publish(self):
        self.status = ArticleStatus.published
        self.published_at = datetime.now()
        self.updated_at = datetime.now()

    def update_content(
        self, title: Optional[str] = None, content: Optional[str] = None
    ):
        if title:
            self.title = title
        if content:
            self.content = content
        self.updated_at = datetime.now()

    def soft_delete(self):
        self.status = ArticleStatus.deleted
        self.updated_at = datetime.now()

    # 기타 필드 및 메서드는 테스트 코드 분석 후 추가
