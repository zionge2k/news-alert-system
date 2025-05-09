"""
Queue 도메인 서비스

이 모듈은 Queue 도메인 모델의 비즈니스 로직을 처리하는 서비스를 정의합니다.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.exceptions import (
    BusinessRuleViolationException,
    EntityNotFoundException,
    ValidationException,
)
from core.interfaces import Service
from core.queue.models import QueueItem, QueuePriority, QueueStatus
from core.queue.repositories import QueueRepository
from core.queue.schemas import QueueItemCreate, QueueItemList, QueueItemUpdate

logger = logging.getLogger(__name__)


class QueueService(Service):
    """
    Queue 도메인 서비스

    Queue 엔티티에 대한 비즈니스 로직을 처리합니다.
    """

    def __init__(self, repository: QueueRepository):
        """
        QueueService 초기화

        Args:
            repository: Queue 저장소 인터페이스
        """
        self.repository = repository

    async def add_to_queue(self, data: QueueItemCreate) -> QueueItem:
        """
        대기열에 항목을 추가합니다.

        Args:
            data: 대기열 항목 생성 데이터

        Returns:
            QueueItem: 생성된 대기열 항목

        Raises:
            ValidationException: 유효성 검증 실패 시
        """
        try:
            # 이미 대기열에 있는지 확인
            existing_item = await self.repository.find_by_article_id(data.article_id)
            if existing_item and existing_item.is_active():
                raise BusinessRuleViolationException(
                    f"Article with id '{data.article_id}' is already in the queue"
                )

            # 새 대기열 항목 생성
            queue_item = QueueItem(
                article_id=data.article_id,
                priority=data.priority,
                scheduled_at=data.scheduled_at,
                metadata=data.metadata,
            )

            # 예약 시간이 있으면 상태를 SCHEDULED로 변경
            if data.scheduled_at:
                queue_item.status = QueueStatus.SCHEDULED

            return await self.repository.save(queue_item)
        except Exception as e:
            if not isinstance(e, BusinessRuleViolationException):
                logger.error(f"대기열 항목 추가 중 오류 발생: {e}")
                raise ValidationException(str(e))
            raise

    async def get_queue_item(self, item_id: str) -> QueueItem:
        """
        대기열 항목을 조회합니다.

        Args:
            item_id: 대기열 항목 ID

        Returns:
            QueueItem: 조회된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
        """
        item = await self.repository.find_by_id(item_id)
        if not item:
            raise EntityNotFoundException("QueueItem", item_id)
        return item

    async def get_queue_item_by_article_id(
        self, article_id: str
    ) -> Optional[QueueItem]:
        """
        기사 ID로 대기열 항목을 조회합니다.

        Args:
            article_id: 기사 ID

        Returns:
            Optional[QueueItem]: 조회된 대기열 항목 또는 None
        """
        return await self.repository.find_by_article_id(article_id)

    async def update_queue_item(self, item_id: str, data: QueueItemUpdate) -> QueueItem:
        """
        대기열 항목을 업데이트합니다.

        Args:
            item_id: 대기열 항목 ID
            data: 업데이트할 데이터

        Returns:
            QueueItem: 업데이트된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 업데이트가 허용되지 않는 상태인 경우
        """
        item = await self.get_queue_item(item_id)

        # 완료된 항목은 업데이트 불가
        if item.status in [QueueStatus.COMPLETED, QueueStatus.CANCELLED]:
            raise BusinessRuleViolationException(
                f"Cannot update item with status {item.status}"
            )

        # 데이터 변환
        update_data = {}
        if data.priority is not None:
            update_data["priority"] = data.priority
        if data.scheduled_at is not None:
            update_data["scheduled_at"] = data.scheduled_at
            update_data["status"] = QueueStatus.SCHEDULED
        if data.status is not None:
            update_data["status"] = data.status
        if data.metadata is not None:
            update_data["metadata"] = data.metadata
        if data.error_message is not None:
            update_data["error_message"] = data.error_message

        updated_item = await self.repository.update(item_id, update_data)
        if not updated_item:
            raise EntityNotFoundException("QueueItem", item_id)

        return updated_item

    async def schedule_item(self, item_id: str, scheduled_at: datetime) -> QueueItem:
        """
        대기열 항목을 예약합니다.

        Args:
            item_id: 대기열 항목 ID
            scheduled_at: 예약 시간

        Returns:
            QueueItem: 업데이트된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 예약이 허용되지 않는 상태인 경우
        """
        item = await self.get_queue_item(item_id)

        try:
            item.schedule(scheduled_at)
            return await self.repository.save(item)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e))

    async def start_processing(self, item_id: str) -> QueueItem:
        """
        대기열 항목의 처리를 시작합니다.

        Args:
            item_id: 대기열 항목 ID

        Returns:
            QueueItem: 업데이트된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 처리 시작이 허용되지 않는 상태인 경우
        """
        item = await self.get_queue_item(item_id)

        try:
            item.start_processing()
            return await self.repository.save(item)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e))

    async def complete_item(self, item_id: str) -> QueueItem:
        """
        대기열 항목의 처리를 완료합니다.

        Args:
            item_id: 대기열 항목 ID

        Returns:
            QueueItem: 업데이트된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 완료가 허용되지 않는 상태인 경우
        """
        item = await self.get_queue_item(item_id)

        try:
            item.complete()
            return await self.repository.save(item)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e))

    async def fail_item(self, item_id: str, error_message: str) -> QueueItem:
        """
        대기열 항목의 처리 실패를 기록합니다.

        Args:
            item_id: 대기열 항목 ID
            error_message: 실패 이유를 설명하는 오류 메시지

        Returns:
            QueueItem: 업데이트된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
        """
        item = await self.get_queue_item(item_id)

        item.fail(error_message)
        return await self.repository.save(item)

    async def cancel_item(self, item_id: str) -> QueueItem:
        """
        대기열 항목을 취소합니다.

        Args:
            item_id: 대기열 항목 ID

        Returns:
            QueueItem: 업데이트된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 취소가 허용되지 않는 상태인 경우
        """
        item = await self.get_queue_item(item_id)

        try:
            item.cancel()
            return await self.repository.save(item)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e))

    async def retry_item(self, item_id: str) -> QueueItem:
        """
        실패한 대기열 항목을 재시도합니다.

        Args:
            item_id: 대기열 항목 ID

        Returns:
            QueueItem: 업데이트된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 재시도가 허용되지 않는 상태인 경우
        """
        item = await self.get_queue_item(item_id)

        try:
            item.retry()
            return await self.repository.save(item)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e))

    async def set_priority(self, item_id: str, priority: QueuePriority) -> QueueItem:
        """
        대기열 항목의 우선순위를 설정합니다.

        Args:
            item_id: 대기열 항목 ID
            priority: 새 우선순위 값

        Returns:
            QueueItem: 업데이트된 대기열 항목

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
        """
        item = await self.get_queue_item(item_id)

        item.set_priority(priority)
        return await self.repository.save(item)

    async def get_ready_items(self, limit: int = 10) -> List[QueueItem]:
        """
        처리 준비가 된 대기열 항목을 조회합니다.

        Args:
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 처리 준비가 된 대기열 항목 목록
        """
        return await self.repository.find_ready_items(limit)

    async def list_queue_items(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[QueueStatus] = None,
        article_id: Optional[str] = None,
        priority: Optional[QueuePriority] = None,
    ) -> QueueItemList:
        """
        대기열 항목 목록을 조회합니다.

        Args:
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기
            status: 상태 필터
            article_id: 기사 ID 필터
            priority: 우선순위 필터

        Returns:
            QueueItemList: 대기열 항목 목록 및 페이지네이션 정보
        """
        filters = {}

        if status:
            filters["status"] = status

        if article_id:
            filters["article_id"] = article_id

        if priority:
            filters["priority"] = priority

        items, total = await self.repository.find_with_pagination(filters, page, size)

        return QueueItemList(items=items, total=total, page=page, size=size)

    async def count_by_status(self, status: QueueStatus) -> int:
        """
        상태별 대기열 항목 수를 조회합니다.

        Args:
            status: 조회할 상태

        Returns:
            int: 해당 상태의 대기열 항목 수
        """
        return await self.repository.count({"status": status})

    async def remove_from_queue(self, item_id: str) -> bool:
        """
        대기열에서 항목을 제거합니다.

        Args:
            item_id: 대기열 항목 ID

        Returns:
            bool: 제거 성공 여부

        Raises:
            EntityNotFoundException: 대기열 항목을 찾을 수 없는 경우
        """
        item = await self.get_queue_item(item_id)

        return await self.repository.delete(item_id)

    async def process_next_batch(self, batch_size: int = 10) -> List[QueueItem]:
        """
        다음 처리할 대기열 항목 배치를 가져와 처리 중 상태로 변경합니다.

        Args:
            batch_size: 배치 크기

        Returns:
            List[QueueItem]: 처리 중으로 변경된 대기열 항목 목록
        """
        ready_items = await self.get_ready_items(batch_size)
        processing_items = []

        for item in ready_items:
            try:
                item.start_processing()
                await self.repository.save(item)
                processing_items.append(item)
            except ValueError as e:
                logger.warning(f"대기열 항목 {item.id} 처리 시작 실패: {e}")
                continue

        return processing_items
