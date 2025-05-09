from abc import abstractmethod
from typing import List, Optional

from app.core.interfaces import Repository

from .models import QueueItem


class QueueRepository(Repository[QueueItem]):
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[QueueItem]:
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[QueueItem]:
        pass

    @abstractmethod
    async def save(self, entity: QueueItem) -> QueueItem:
        pass

    @abstractmethod
    async def update(self, id: str, entity: QueueItem) -> Optional[QueueItem]:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass

    async def get(self, id: str):
        return await self.find_by_id(id)

    async def list(self, limit: int = 100, offset: int = 0):
        return await self.find_all(skip=offset, limit=limit)


class InMemoryQueueRepository(QueueRepository):
    def __init__(self):
        self._items = {}

    async def find_by_id(self, id: str) -> Optional[QueueItem]:
        return self._items.get(id)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[QueueItem]:
        items = list(self._items.values())
        return items[skip : skip + limit]

    async def save(self, entity: QueueItem) -> QueueItem:
        self._items[entity.id] = entity
        return entity

    async def update(self, id: str, entity: QueueItem) -> Optional[QueueItem]:
        if id in self._items:
            self._items[id] = entity
            return entity
        return None

    async def delete(self, id: str) -> bool:
        return self._items.pop(id, None) is not None
