from abc import abstractmethod
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.core.interfaces import Service

from .models import PublishedArticle, PublishedStatus
from .repositories import InMemoryPublishedRepository
from .schemas import (
    PublishedArticleCreate,
    PublishedArticleResponse,
    PublishedArticleUpdate,
    PublishedListResponse,
)


class PublishedService(Service):
    @abstractmethod
    async def publish(self, data: PublishedArticleCreate) -> PublishedArticleResponse:
        pass

    @abstractmethod
    async def get_article(self, id: str) -> Optional[PublishedArticleResponse]:
        pass

    @abstractmethod
    async def update_article(
        self, id: str, data: PublishedArticleUpdate
    ) -> Optional[PublishedArticleResponse]:
        pass

    @abstractmethod
    async def delete_article(self, id: str) -> bool:
        pass

    @abstractmethod
    async def list_articles(
        self, skip: int = 0, limit: int = 100
    ) -> PublishedListResponse:
        pass


class InMemoryPublishedService(PublishedService):
    def __init__(self, repository: InMemoryPublishedRepository):
        self.repository = repository

    async def publish(self, data: PublishedArticleCreate) -> PublishedArticleResponse:
        article_id = str(uuid4())
        article = PublishedArticle(
            id=article_id,
            article_id=data.article_id,
            status=PublishedStatus.published,
            published_at=datetime.now(),
        )
        await self.repository.save(article)
        return PublishedArticleResponse(**article.model_dump())

    async def get_article(self, id: str) -> Optional[PublishedArticleResponse]:
        article = await self.repository.find_by_id(id)
        if article:
            return PublishedArticleResponse(**article.model_dump())
        return None

    async def update_article(
        self, id: str, data: PublishedArticleUpdate
    ) -> Optional[PublishedArticleResponse]:
        article = await self.repository.find_by_id(id)
        if not article:
            return None
        if data.status:
            article.status = data.status
            if data.status == PublishedStatus.archived:
                article.archive()
            elif data.status == PublishedStatus.deleted:
                article.soft_delete()
        await self.repository.save(article)
        return PublishedArticleResponse(**article.model_dump())

    async def delete_article(self, id: str) -> bool:
        return await self.repository.delete(id)

    async def list_articles(
        self, skip: int = 0, limit: int = 100
    ) -> PublishedListResponse:
        articles = await self.repository.find_all(skip=skip, limit=limit)
        return PublishedListResponse(
            items=[PublishedArticleResponse(**a.model_dump()) for a in articles],
            total=len(articles),
        )
