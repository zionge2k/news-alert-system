from abc import abstractmethod
from typing import List, Optional

from app.core.interfaces import Repository

from .models import PublishedArticle


class PublishedRepository(Repository[PublishedArticle]):
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[PublishedArticle]:
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[PublishedArticle]:
        pass

    @abstractmethod
    async def save(self, entity: PublishedArticle) -> PublishedArticle:
        pass

    @abstractmethod
    async def update(
        self, id: str, entity: PublishedArticle
    ) -> Optional[PublishedArticle]:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass

    async def get(self, id: str):
        return await self.find_by_id(id)

    async def list(self, limit: int = 100, offset: int = 0):
        return await self.find_all(skip=offset, limit=limit)


class InMemoryPublishedRepository(PublishedRepository):
    def __init__(self):
        self._items = {}

    async def find_by_id(self, id: str) -> Optional[PublishedArticle]:
        return self._items.get(id)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[PublishedArticle]:
        items = list(self._items.values())
        return items[skip : skip + limit]

    async def save(self, entity: PublishedArticle) -> PublishedArticle:
        self._items[entity.id] = entity
        return entity

    async def update(
        self, id: str, entity: PublishedArticle
    ) -> Optional[PublishedArticle]:
        if id in self._items:
            self._items[id] = entity
            return entity
        return None

    async def delete(self, id: str) -> bool:
        return self._items.pop(id, None) is not None
