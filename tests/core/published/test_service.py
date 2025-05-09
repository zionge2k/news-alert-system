import pytest

from app.core.published.models import PublishedArticle, PublishedStatus
from app.core.published.repositories import InMemoryPublishedRepository
from app.core.published.schemas import PublishedArticleCreate, PublishedArticleUpdate
from app.core.published.services import InMemoryPublishedService


@pytest.mark.asyncio
async def test_publish_and_get_article():
    repo = InMemoryPublishedRepository()
    service = InMemoryPublishedService(repo)
    data = PublishedArticleCreate(article_id="article-1")
    created = await service.publish(data)
    assert created.article_id == data.article_id
    assert created.status == PublishedStatus.published
    fetched = await service.get_article(created.id)
    assert fetched is not None
    assert fetched.article_id == data.article_id


@pytest.mark.asyncio
async def test_update_and_delete_article():
    repo = InMemoryPublishedRepository()
    service = InMemoryPublishedService(repo)
    data = PublishedArticleCreate(article_id="article-2")
    created = await service.publish(data)
    update = PublishedArticleUpdate(status=PublishedStatus.archived)
    updated = await service.update_article(created.id, update)
    assert updated.status == PublishedStatus.archived
    deleted = await service.delete_article(created.id)
    assert deleted is True
    fetched = await service.get_article(created.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_list_articles():
    repo = InMemoryPublishedRepository()
    service = InMemoryPublishedService(repo)
    for i in range(2):
        data = PublishedArticleCreate(article_id=f"article-{i}")
        await service.publish(data)
    result = await service.list_articles()
    assert result.total == 2
    assert all(item.article_id.startswith("article-") for item in result.items)
