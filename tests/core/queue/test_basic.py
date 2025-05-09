from datetime import datetime, timedelta

import pytest

from core.queue.models import QueueItem, QueuePriority, QueueStatus
from tests.helpers import dummy_article_dto


def test_dummy_article_dto():
    article = dummy_article_dto()
    assert article.title.startswith("테스트 기사 제목")
    assert article.url.startswith("https://example.com/news/")
    assert article.author.endswith("기자")
    assert article.content.startswith("테스트 기사 내용입니다.")
    assert article.metadata.platform == "TEST"


def test_mock_article_collection(mock_article_collection):
    # 더미 기사 생성 및 insert
    article = dummy_article_dto().model_dump()
    import asyncio

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(mock_article_collection.insert_one(article))
    assert result.inserted_id.startswith("test_id_")
    # find_one 동작 확인
    found = loop.run_until_complete(
        mock_article_collection.find_one({"_id": result.inserted_id})
    )
    assert found["title"].startswith("테스트 기사 제목")


def test_queue_item_creation():
    """QueueItem 생성 테스트"""
    article_id = "test-article-123"
    item = QueueItem(article_id=article_id)

    assert item.id is not None
    assert item.article_id == article_id
    assert item.status == QueueStatus.PENDING
    assert item.priority == QueuePriority.NORMAL
    assert item.created_at is not None
    assert item.updated_at is not None
    assert item.scheduled_at is None
    assert item.processed_at is None
    assert item.metadata == {}
    assert item.error_message is None


def test_queue_item_schedule():
    """QueueItem 예약 테스트"""
    item = QueueItem(article_id="test-article-123")
    scheduled_time = datetime.now() + timedelta(hours=1)

    item.schedule(scheduled_time)

    assert item.status == QueueStatus.SCHEDULED
    assert item.scheduled_at == scheduled_time


def test_queue_item_schedule_invalid_status():
    """유효하지 않은 상태에서 QueueItem 예약 테스트"""
    item = QueueItem(article_id="test-article-123", status=QueueStatus.COMPLETED)
    scheduled_time = datetime.now() + timedelta(hours=1)

    with pytest.raises(ValueError):
        item.schedule(scheduled_time)


def test_queue_item_start_processing():
    """QueueItem 처리 시작 테스트"""
    item = QueueItem(article_id="test-article-123")

    item.start_processing()

    assert item.status == QueueStatus.PROCESSING


def test_queue_item_start_processing_invalid_status():
    """유효하지 않은 상태에서 QueueItem 처리 시작 테스트"""
    item = QueueItem(article_id="test-article-123", status=QueueStatus.COMPLETED)

    with pytest.raises(ValueError):
        item.start_processing()


def test_queue_item_complete():
    """QueueItem 처리 완료 테스트"""
    item = QueueItem(article_id="test-article-123", status=QueueStatus.PROCESSING)

    item.complete()

    assert item.status == QueueStatus.COMPLETED
    assert item.processed_at is not None


def test_queue_item_complete_invalid_status():
    """유효하지 않은 상태에서 QueueItem 처리 완료 테스트"""
    item = QueueItem(article_id="test-article-123", status=QueueStatus.PENDING)

    with pytest.raises(ValueError):
        item.complete()


def test_queue_item_fail():
    """QueueItem 처리 실패 테스트"""
    item = QueueItem(article_id="test-article-123")
    error_message = "테스트 오류 메시지"

    item.fail(error_message)

    assert item.status == QueueStatus.FAILED
    assert item.error_message == error_message


def test_queue_item_cancel():
    """QueueItem 취소 테스트"""
    item = QueueItem(article_id="test-article-123")

    item.cancel()

    assert item.status == QueueStatus.CANCELLED


def test_queue_item_cancel_invalid_status():
    """유효하지 않은 상태에서 QueueItem 취소 테스트"""
    item = QueueItem(article_id="test-article-123", status=QueueStatus.COMPLETED)

    with pytest.raises(ValueError):
        item.cancel()


def test_queue_item_retry():
    """QueueItem 재시도 테스트"""
    item = QueueItem(
        article_id="test-article-123", status=QueueStatus.FAILED, error_message="오류"
    )

    item.retry()

    assert item.status == QueueStatus.PENDING
    assert item.error_message is None


def test_queue_item_retry_invalid_status():
    """유효하지 않은 상태에서 QueueItem 재시도 테스트"""
    item = QueueItem(article_id="test-article-123", status=QueueStatus.PENDING)

    with pytest.raises(ValueError):
        item.retry()


def test_queue_item_set_priority():
    """QueueItem 우선순위 설정 테스트"""
    item = QueueItem(article_id="test-article-123")

    item.set_priority(QueuePriority.HIGH)

    assert item.priority == QueuePriority.HIGH


def test_queue_item_update_metadata():
    """QueueItem 메타데이터 업데이트 테스트"""
    item = QueueItem(article_id="test-article-123")

    item.update_metadata({"channel": "discord", "target": "news-alerts"})

    assert item.metadata == {"channel": "discord", "target": "news-alerts"}

    # 추가 메타데이터 업데이트
    item.update_metadata({"priority_reason": "breaking_news"})

    assert item.metadata == {
        "channel": "discord",
        "target": "news-alerts",
        "priority_reason": "breaking_news",
    }


def test_queue_item_is_ready_to_process():
    """QueueItem 처리 준비 확인 테스트"""
    # 대기 중인 항목
    pending_item = QueueItem(article_id="test-article-123")
    assert pending_item.is_ready_to_process() is True

    # 예약된 항목 (미래)
    future_item = QueueItem(
        article_id="test-article-124",
        status=QueueStatus.SCHEDULED,
        scheduled_at=datetime.now() + timedelta(hours=1),
    )
    assert future_item.is_ready_to_process() is False

    # 예약된 항목 (과거)
    past_item = QueueItem(
        article_id="test-article-125",
        status=QueueStatus.SCHEDULED,
        scheduled_at=datetime.now() - timedelta(hours=1),
    )
    assert past_item.is_ready_to_process() is True

    # 처리 중인 항목
    processing_item = QueueItem(
        article_id="test-article-126", status=QueueStatus.PROCESSING
    )
    assert processing_item.is_ready_to_process() is False


def test_queue_item_is_active():
    """QueueItem 활성 상태 확인 테스트"""
    # 대기 중인 항목
    pending_item = QueueItem(article_id="test-article-123")
    assert pending_item.is_active() is True

    # 예약된 항목
    scheduled_item = QueueItem(
        article_id="test-article-124", status=QueueStatus.SCHEDULED
    )
    assert scheduled_item.is_active() is True

    # 처리 중인 항목
    processing_item = QueueItem(
        article_id="test-article-125", status=QueueStatus.PROCESSING
    )
    assert processing_item.is_active() is True

    # 완료된 항목
    completed_item = QueueItem(
        article_id="test-article-126", status=QueueStatus.COMPLETED
    )
    assert completed_item.is_active() is False

    # 실패한 항목
    failed_item = QueueItem(article_id="test-article-127", status=QueueStatus.FAILED)
    assert failed_item.is_active() is False

    # 취소된 항목
    cancelled_item = QueueItem(
        article_id="test-article-128", status=QueueStatus.CANCELLED
    )
    assert cancelled_item.is_active() is False


def test_queue_item_to_dict():
    """QueueItem to_dict 메서드 테스트"""
    now = datetime.now()
    item = QueueItem(
        id="test-id-123",
        article_id="test-article-123",
        status=QueueStatus.PROCESSING,
        priority=QueuePriority.HIGH,
        scheduled_at=now,
        created_at=now,
        updated_at=now,
        metadata={"channel": "discord"},
    )

    data = item.to_dict()

    assert data["id"] == "test-id-123"
    assert data["article_id"] == "test-article-123"
    assert data["status"] == "processing"
    assert data["priority"] == 2
    assert data["scheduled_at"] == now.isoformat()
    assert data["created_at"] == now.isoformat()
    assert data["updated_at"] == now.isoformat()
    assert data["processed_at"] is None
    assert data["metadata"] == {"channel": "discord"}
    assert data["error_message"] is None


def test_queue_item_from_dict():
    """QueueItem from_dict 메서드 테스트"""
    now = datetime.now()
    data = {
        "id": "test-id-123",
        "article_id": "test-article-123",
        "status": "processing",
        "priority": 2,
        "scheduled_at": now.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "processed_at": None,
        "metadata": {"channel": "discord"},
        "error_message": None,
    }

    item = QueueItem.from_dict(data)

    assert item.id == "test-id-123"
    assert item.article_id == "test-article-123"
    assert item.status == QueueStatus.PROCESSING
    assert item.priority == QueuePriority.HIGH
    assert item.scheduled_at.isoformat() == now.isoformat()
    assert item.created_at.isoformat() == now.isoformat()
    assert item.updated_at.isoformat() == now.isoformat()
    assert item.processed_at is None
    assert item.metadata == {"channel": "discord"}
    assert item.error_message is None
