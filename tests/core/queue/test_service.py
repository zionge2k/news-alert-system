import pytest

from app.core.queue.models import QueueItem, QueueStatus
from app.core.queue.repositories import InMemoryQueueRepository
from app.core.queue.schemas import QueueItemCreate, QueueItemUpdate
from app.core.queue.services import InMemoryQueueService


@pytest.mark.asyncio
async def test_enqueue_and_get_item():
    repo = InMemoryQueueRepository()
    service = InMemoryQueueService(repo)
    data = QueueItemCreate(article_id="article-1", priority=10)
    created = await service.enqueue(data)
    assert created.article_id == data.article_id
    assert created.status == QueueStatus.waiting
    fetched = await service.get_item(created.id)
    assert fetched is not None
    assert fetched.article_id == data.article_id


@pytest.mark.asyncio
async def test_update_and_delete_item():
    repo = InMemoryQueueRepository()
    service = InMemoryQueueService(repo)
    data = QueueItemCreate(article_id="article-2", priority=5)
    created = await service.enqueue(data)
    update = QueueItemUpdate(status=QueueStatus.processing, priority=7)
    updated = await service.update_item(created.id, update)
    assert updated.status == QueueStatus.processing
    assert updated.priority == 7
    deleted = await service.delete_item(created.id)
    assert deleted is True
    fetched = await service.get_item(created.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_list_items():
    repo = InMemoryQueueRepository()
    service = InMemoryQueueService(repo)
    for i in range(3):
        data = QueueItemCreate(article_id=f"article-{i}", priority=i)
        await service.enqueue(data)
    result = await service.list_items()
    assert result.total == 3
    assert all(item.article_id.startswith("article-") for item in result.items)
