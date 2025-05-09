import pytest

from app.core.article.models import ArticleMetadata
from app.core.article.repositories import InMemoryArticleRepository
from app.core.article.schemas import ArticleCreate
from app.core.article.services import InMemoryArticleService
from app.core.published.repositories import InMemoryPublishedRepository
from app.core.published.schemas import PublishedArticleCreate
from app.core.published.services import InMemoryPublishedService
from app.core.queue.repositories import InMemoryQueueRepository
from app.core.queue.schemas import QueueItemCreate
from app.core.queue.services import InMemoryQueueService

# Article, Queue, Published 관련 import (예시)
# from app.models.article import ArticleModel
# from app.models.queue import QueueItem
# from app.models.published import PublishedModel


@pytest.mark.asyncio
async def test_article_to_published_full_flow():
    # Article 생성
    article_repo = InMemoryArticleRepository()
    article_service = InMemoryArticleService(article_repo)
    article_data = ArticleCreate(
        title="통합테스트 기사",
        url="https://example.com/integration",
        author="홍길동",
        content="통합테스트 본문",
        metadata=ArticleMetadata(platform="TEST", tags=["통합"], category="테스트"),
    )
    article = await article_service.create_article(article_data)

    # Queue 등록
    queue_repo = InMemoryQueueRepository()
    queue_service = InMemoryQueueService(queue_repo)
    queue_data = QueueItemCreate(article_id=article.id, priority=1)
    queue_item = await queue_service.enqueue(queue_data)
    assert queue_item.article_id == article.id

    # Published 처리
    published_repo = InMemoryPublishedRepository()
    published_service = InMemoryPublishedService(published_repo)
    published_data = PublishedArticleCreate(article_id=article.id)
    published_article = await published_service.publish(published_data)
    assert published_article.article_id == article.id
    assert published_article.status.value == "published"


# TODO: 데이터 무결성, 이벤트, 에러 처리 등 세부 테스트 함수 추가
