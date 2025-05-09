from abc import abstractmethod
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.core.interfaces import Service

from .models import QueueItem, QueueStatus
from .repositories import InMemoryQueueRepository
from .schemas import (
    QueueItemCreate,
    QueueItemResponse,
    QueueItemUpdate,
    QueueListResponse,
)


class QueueService(Service):
    @abstractmethod
    async def enqueue(self, data: QueueItemCreate) -> QueueItemResponse:
        pass

    @abstractmethod
    async def get_item(self, id: str) -> Optional[QueueItemResponse]:
        pass

    @abstractmethod
    async def update_item(
        self, id: str, data: QueueItemUpdate
    ) -> Optional[QueueItemResponse]:
        pass

    @abstractmethod
    async def delete_item(self, id: str) -> bool:
        pass

    @abstractmethod
    async def list_items(self, skip: int = 0, limit: int = 100) -> QueueListResponse:
        pass


class InMemoryQueueService(QueueService):
    def __init__(self, repository: InMemoryQueueRepository):
        self.repository = repository

    async def enqueue(self, data: QueueItemCreate) -> QueueItemResponse:
        item_id = str(uuid4())
        item = QueueItem(
            id=item_id,
            article_id=data.article_id,
            priority=data.priority,
            status=QueueStatus.waiting,
            enqueued_at=datetime.now(),
        )
        await self.repository.save(item)
        return QueueItemResponse(**item.model_dump())

    async def get_item(self, id: str) -> Optional[QueueItemResponse]:
        item = await self.repository.find_by_id(id)
        if item:
            return QueueItemResponse(**item.model_dump())
        return None

    async def update_item(
        self, id: str, data: QueueItemUpdate
    ) -> Optional[QueueItemResponse]:
        item = await self.repository.find_by_id(id)
        if not item:
            return None
        if data.status:
            item.status = data.status
        if data.priority is not None:
            item.priority = data.priority
        if data.failed_reason:
            item.failed_reason = data.failed_reason
        item.processed_at = (
            datetime.now()
            if data.status in [QueueStatus.done, QueueStatus.failed]
            else None
        )
        await self.repository.save(item)
        return QueueItemResponse(**item.model_dump())

    async def delete_item(self, id: str) -> bool:
        return await self.repository.delete(id)

    async def list_items(self, skip: int = 0, limit: int = 100) -> QueueListResponse:
        items = await self.repository.find_all(skip=skip, limit=limit)
        return QueueListResponse(
            items=[QueueItemResponse(**i.model_dump()) for i in items],
            total=len(items),
        )
