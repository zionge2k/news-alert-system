from abc import abstractmethod
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.core.article.models import ArticleStatus
from app.core.interfaces import Service

from .models import Article
from .repositories import InMemoryArticleRepository
from .schemas import ArticleCreate, ArticleListResponse, ArticleResponse, ArticleUpdate


class ArticleService(Service):
    @abstractmethod
    async def create_article(self, data: ArticleCreate) -> ArticleResponse:
        pass

    @abstractmethod
    async def get_article(self, id: str) -> Optional[ArticleResponse]:
        pass

    @abstractmethod
    async def update_article(
        self, id: str, data: ArticleUpdate
    ) -> Optional[ArticleResponse]:
        pass

    @abstractmethod
    async def delete_article(self, id: str) -> bool:
        pass

    @abstractmethod
    async def list_articles(
        self, skip: int = 0, limit: int = 100
    ) -> ArticleListResponse:
        pass


class InMemoryArticleService(ArticleService):
    def __init__(self, repository: InMemoryArticleRepository):
        self.repository = repository

    async def create_article(self, data: ArticleCreate) -> ArticleResponse:
        article_id = str(uuid4())
        article = Article(
            id=article_id,
            title=data.title,
            url=data.url,
            author=data.author,
            content=data.content,
            metadata=data.metadata,
            status=ArticleStatus.draft,
            created_at=datetime.now(),
        )
        await self.repository.save(article)
        return ArticleResponse(**article.model_dump())

    async def get_article(self, id: str) -> Optional[ArticleResponse]:
        article = await self.repository.find_by_id(id)
        if article:
            return ArticleResponse(**article.model_dump())
        return None

    async def update_article(
        self, id: str, data: ArticleUpdate
    ) -> Optional[ArticleResponse]:
        article = await self.repository.find_by_id(id)
        if not article:
            return None
        article.update_content(title=data.title, content=data.content)
        if data.metadata:
            article.metadata = data.metadata
        article.updated_at = datetime.now()
        await self.repository.save(article)
        return ArticleResponse(**article.model_dump())

    async def delete_article(self, id: str) -> bool:
        article = await self.repository.find_by_id(id)
        if not article:
            return False
        article.soft_delete()
        await self.repository.save(article)
        return True

    async def list_articles(
        self, skip: int = 0, limit: int = 100
    ) -> ArticleListResponse:
        articles = await self.repository.find_all(skip=skip, limit=limit)
        return ArticleListResponse(
            articles=[ArticleResponse(**a.model_dump()) for a in articles],
            total=len(articles),
        )
