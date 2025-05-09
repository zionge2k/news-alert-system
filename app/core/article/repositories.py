from abc import abstractmethod
from typing import List, Optional

from app.core.interfaces import Repository

from .models import Article


class ArticleRepository(Repository[Article]):
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Article]:
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Article]:
        pass

    @abstractmethod
    async def save(self, entity: Article) -> Article:
        pass

    @abstractmethod
    async def update(self, id: str, entity: Article) -> Optional[Article]:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass

    async def get(self, id: str):
        return await self.find_by_id(id)

    async def list(self, limit: int = 100, offset: int = 0):
        return await self.find_all(skip=offset, limit=limit)


class InMemoryArticleRepository(ArticleRepository):
    def __init__(self):
        self._articles = {}

    async def find_by_id(self, id: str) -> Optional[Article]:
        return self._articles.get(id)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Article]:
        articles = list(self._articles.values())
        return articles[skip : skip + limit]

    async def save(self, entity: Article) -> Article:
        self._articles[entity.id] = entity
        return entity

    async def update(self, id: str, entity: Article) -> Optional[Article]:
        if id in self._articles:
            self._articles[id] = entity
            return entity
        return None

    async def delete(self, id: str) -> bool:
        return self._articles.pop(id, None) is not None
