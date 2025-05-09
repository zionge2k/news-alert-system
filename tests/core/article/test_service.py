import asyncio

import pytest

from app.core.article.models import Article, ArticleMetadata, ArticleStatus
from app.core.article.repositories import InMemoryArticleRepository
from app.core.article.schemas import ArticleCreate, ArticleUpdate
from app.core.article.services import InMemoryArticleService


@pytest.mark.asyncio
async def test_create_and_get_article():
    repo = InMemoryArticleRepository()
    service = InMemoryArticleService(repo)
    data = ArticleCreate(
        title="테스트 기사",
        url="https://example.com/news/1",
        author="홍길동",
        content="본문 내용",
        metadata=ArticleMetadata(platform="TEST", tags=["뉴스"], category="정치"),
    )
    created = await service.create_article(data)
    assert created.title == data.title
    assert created.url == data.url
    assert created.author == data.author
    assert created.status == ArticleStatus.draft

    fetched = await service.get_article(created.id)
    assert fetched is not None
    assert fetched.title == data.title


@pytest.mark.asyncio
async def test_update_and_delete_article():
    repo = InMemoryArticleRepository()
    service = InMemoryArticleService(repo)
    data = ArticleCreate(
        title="업데이트 전",
        url="https://example.com/news/2",
        author="홍길동",
        content="본문",
        metadata=ArticleMetadata(platform="TEST", tags=["뉴스"], category="정치"),
    )
    created = await service.create_article(data)
    update = ArticleUpdate(title="업데이트 후", content="수정된 본문")
    updated = await service.update_article(created.id, update)
    assert updated.title == "업데이트 후"
    assert updated.content == "수정된 본문"

    deleted = await service.delete_article(created.id)
    assert deleted is True
    fetched = await service.get_article(created.id)
    assert fetched.status == ArticleStatus.deleted


@pytest.mark.asyncio
async def test_list_articles():
    repo = InMemoryArticleRepository()
    service = InMemoryArticleService(repo)
    for i in range(5):
        data = ArticleCreate(
            title=f"기사 {i}",
            url=f"https://example.com/news/{i}",
            author="홍길동",
            content="본문",
            metadata=ArticleMetadata(platform="TEST", tags=["뉴스"], category="정치"),
        )
        await service.create_article(data)
    result = await service.list_articles()
    assert result.total == 5
    assert all(a.title.startswith("기사") for a in result.articles)
