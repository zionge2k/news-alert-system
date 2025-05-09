"""
Queue 도메인 저장소

이 모듈은 Queue 도메인 모델의 저장소 인터페이스와 구현체를 정의합니다.
"""

import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pymongo.collection import Collection
from pymongo.database import Database

from core.exceptions import EntityNotFoundException
from core.interfaces import Repository
from core.queue.models import QueueItem, QueuePriority, QueueStatus

logger = logging.getLogger(__name__)


class QueueRepository(Repository[QueueItem, str]):
    """
    QueueItem 엔티티를 위한 저장소 인터페이스

    이 인터페이스는 QueueItem 엔티티의 CRUD 작업을 정의합니다.
    """

    @abstractmethod
    async def find_by_status(
        self, status: QueueStatus, skip: int = 0, limit: int = 100
    ) -> List[QueueItem]:
        """
        상태별 대기열 항목 조회

        Args:
            status: 조회할 대기열 항목 상태
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 조회된 대기열 항목 목록
        """
        pass

    @abstractmethod
    async def find_by_article_id(self, article_id: str) -> Optional[QueueItem]:
        """
        기사 ID로 대기열 항목 조회

        Args:
            article_id: 조회할 기사 ID

        Returns:
            Optional[QueueItem]: 조회된 대기열 항목 또는 None
        """
        pass

    @abstractmethod
    async def find_ready_items(self, limit: int = 10) -> List[QueueItem]:
        """
        처리 준비가 된 대기열 항목 조회

        처리 준비가 된 항목은 다음 조건 중 하나를 만족합니다:
        1. 상태가 PENDING
        2. 상태가 SCHEDULED이고 scheduled_at이 현재 시간보다 이전

        우선순위가 높은 항목이 먼저 반환됩니다.

        Args:
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 처리 준비가 된 대기열 항목 목록
        """
        pass

    @abstractmethod
    async def find_with_pagination(
        self, filters: Dict[str, Any], page: int = 1, size: int = 10
    ) -> Tuple[List[QueueItem], int]:
        """
        필터와 페이지네이션을 적용하여 대기열 항목 조회

        Args:
            filters: 필터 조건
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            Tuple[List[QueueItem], int]: 조회된 대기열 항목 목록과 전체 항목 수
        """
        pass

    @abstractmethod
    async def count(self, filters: Dict[str, Any]) -> int:
        """
        필터 조건에 맞는 대기열 항목 수 조회

        Args:
            filters: 필터 조건

        Returns:
            int: 필터 조건에 맞는 대기열 항목 수
        """
        pass


class InMemoryQueueRepository(QueueRepository):
    """
    메모리 기반 QueueRepository 구현체

    테스트 및 개발용으로 사용됩니다.
    """

    def __init__(self):
        """InMemoryQueueRepository 초기화"""
        self.items: Dict[str, QueueItem] = {}

    async def save(self, entity: QueueItem) -> QueueItem:
        """
        대기열 항목을 저장합니다.

        Args:
            entity: 저장할 대기열 항목

        Returns:
            QueueItem: 저장된 대기열 항목
        """
        self.items[entity.id] = entity
        return entity

    async def find_by_id(self, id: str) -> Optional[QueueItem]:
        """
        ID로 대기열 항목을 조회합니다.

        Args:
            id: 대기열 항목 ID

        Returns:
            Optional[QueueItem]: 조회된 대기열 항목 또는 None
        """
        return self.items.get(id)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[QueueItem]:
        """
        모든 대기열 항목을 조회합니다.

        Args:
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 조회된 대기열 항목 목록
        """
        return list(self.items.values())[skip : skip + limit]

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[QueueItem]:
        """
        대기열 항목을 업데이트합니다.

        Args:
            id: 대기열 항목 ID
            data: 업데이트할 데이터

        Returns:
            Optional[QueueItem]: 업데이트된 대기열 항목 또는 None
        """
        item = await self.find_by_id(id)
        if not item:
            return None

        # 업데이트 가능한 필드 목록
        updatable_fields = [
            "status",
            "priority",
            "scheduled_at",
            "processed_at",
            "metadata",
            "error_message",
        ]

        for field, value in data.items():
            if field in updatable_fields:
                if field == "status" and value is not None:
                    item.status = QueueStatus(value)
                elif field == "priority" and value is not None:
                    item.priority = QueuePriority(value)
                else:
                    setattr(item, field, value)

        item.updated_at = datetime.now()
        return item

    async def delete(self, id: str) -> bool:
        """
        대기열 항목을 삭제합니다.

        Args:
            id: 대기열 항목 ID

        Returns:
            bool: 삭제 성공 여부
        """
        if id in self.items:
            del self.items[id]
            return True
        return False

    async def find_by_status(
        self, status: QueueStatus, skip: int = 0, limit: int = 100
    ) -> List[QueueItem]:
        """
        상태별 대기열 항목 조회

        Args:
            status: 조회할 대기열 항목 상태
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 조회된 대기열 항목 목록
        """
        filtered_items = [item for item in self.items.values() if item.status == status]
        return filtered_items[skip : skip + limit]

    async def find_by_article_id(self, article_id: str) -> Optional[QueueItem]:
        """
        기사 ID로 대기열 항목 조회

        Args:
            article_id: 조회할 기사 ID

        Returns:
            Optional[QueueItem]: 조회된 대기열 항목 또는 None
        """
        for item in self.items.values():
            if item.article_id == article_id:
                return item
        return None

    async def find_ready_items(self, limit: int = 10) -> List[QueueItem]:
        """
        처리 준비가 된 대기열 항목 조회

        Args:
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 처리 준비가 된 대기열 항목 목록
        """
        ready_items = [
            item for item in self.items.values() if item.is_ready_to_process()
        ]

        # 우선순위 내림차순으로 정렬
        sorted_items = sorted(
            ready_items, key=lambda x: (x.priority.value, x.created_at), reverse=True
        )

        return sorted_items[:limit]

    async def find_with_pagination(
        self, filters: Dict[str, Any], page: int = 1, size: int = 10
    ) -> Tuple[List[QueueItem], int]:
        """
        필터와 페이지네이션을 적용하여 대기열 항목 조회

        Args:
            filters: 필터 조건
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            Tuple[List[QueueItem], int]: 조회된 대기열 항목 목록과 전체 항목 수
        """
        filtered_items = self.items.values()

        # 필터 적용
        if filters:
            for field, value in filters.items():
                if field == "status" and value is not None:
                    filtered_items = [
                        item
                        for item in filtered_items
                        if item.status == QueueStatus(value)
                    ]
                elif field == "priority" and value is not None:
                    filtered_items = [
                        item
                        for item in filtered_items
                        if item.priority == QueuePriority(value)
                    ]
                elif field == "article_id" and value is not None:
                    filtered_items = [
                        item for item in filtered_items if item.article_id == value
                    ]

        # 리스트로 변환
        filtered_items = list(filtered_items)
        total = len(filtered_items)

        # 페이지네이션 적용
        skip = (page - 1) * size
        paginated_items = filtered_items[skip : skip + size]

        return paginated_items, total

    async def count(self, filters: Dict[str, Any]) -> int:
        """
        필터 조건에 맞는 대기열 항목 수 조회

        Args:
            filters: 필터 조건

        Returns:
            int: 필터 조건에 맞는 대기열 항목 수
        """
        filtered_items = self.items.values()

        # 필터 적용
        if filters:
            for field, value in filters.items():
                if field == "status" and value is not None:
                    filtered_items = [
                        item
                        for item in filtered_items
                        if item.status == QueueStatus(value)
                    ]
                elif field == "priority" and value is not None:
                    filtered_items = [
                        item
                        for item in filtered_items
                        if item.priority == QueuePriority(value)
                    ]
                elif field == "article_id" and value is not None:
                    filtered_items = [
                        item for item in filtered_items if item.article_id == value
                    ]

        return len(list(filtered_items))


class MongoQueueRepository(QueueRepository):
    """
    MongoDB 기반 QueueRepository 구현체
    """

    def __init__(self, db: Database, collection_name: str = "queue_items"):
        """
        MongoQueueRepository 초기화

        Args:
            db: MongoDB 데이터베이스 객체
            collection_name: 컬렉션 이름 (기본값: "queue_items")
        """
        self.collection: Collection = db[collection_name]

    async def save(self, entity: QueueItem) -> QueueItem:
        """
        대기열 항목을 저장합니다.

        Args:
            entity: 저장할 대기열 항목

        Returns:
            QueueItem: 저장된 대기열 항목
        """
        data = entity.to_dict()

        # upsert 수행
        await self.collection.update_one({"id": entity.id}, {"$set": data}, upsert=True)

        return entity

    async def find_by_id(self, id: str) -> Optional[QueueItem]:
        """
        ID로 대기열 항목을 조회합니다.

        Args:
            id: 대기열 항목 ID

        Returns:
            Optional[QueueItem]: 조회된 대기열 항목 또는 None
        """
        data = await self.collection.find_one({"id": id})
        if not data:
            return None

        return QueueItem.from_dict(data)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[QueueItem]:
        """
        모든 대기열 항목을 조회합니다.

        Args:
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 조회된 대기열 항목 목록
        """
        cursor = self.collection.find().skip(skip).limit(limit)
        items = []

        async for data in cursor:
            items.append(QueueItem.from_dict(data))

        return items

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[QueueItem]:
        """
        대기열 항목을 업데이트합니다.

        Args:
            id: 대기열 항목 ID
            data: 업데이트할 데이터

        Returns:
            Optional[QueueItem]: 업데이트된 대기열 항목 또는 None
        """
        # 상태 및 우선순위 열거형 문자열 변환
        if "status" in data and data["status"] is not None:
            if isinstance(data["status"], QueueStatus):
                data["status"] = data["status"].value

        if "priority" in data and data["priority"] is not None:
            if isinstance(data["priority"], QueuePriority):
                data["priority"] = data["priority"].value

        # updated_at 추가
        data["updated_at"] = datetime.now().isoformat()

        result = await self.collection.update_one({"id": id}, {"$set": data})

        if result.matched_count == 0:
            return None

        return await self.find_by_id(id)

    async def delete(self, id: str) -> bool:
        """
        대기열 항목을 삭제합니다.

        Args:
            id: 대기열 항목 ID

        Returns:
            bool: 삭제 성공 여부
        """
        result = await self.collection.delete_one({"id": id})
        return result.deleted_count > 0

    async def find_by_status(
        self, status: QueueStatus, skip: int = 0, limit: int = 100
    ) -> List[QueueItem]:
        """
        상태별 대기열 항목 조회

        Args:
            status: 조회할 대기열 항목 상태
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 조회된 대기열 항목 목록
        """
        cursor = self.collection.find({"status": status.value}).skip(skip).limit(limit)
        items = []

        async for data in cursor:
            items.append(QueueItem.from_dict(data))

        return items

    async def find_by_article_id(self, article_id: str) -> Optional[QueueItem]:
        """
        기사 ID로 대기열 항목 조회

        Args:
            article_id: 조회할 기사 ID

        Returns:
            Optional[QueueItem]: 조회된 대기열 항목 또는 None
        """
        data = await self.collection.find_one({"article_id": article_id})
        if not data:
            return None

        return QueueItem.from_dict(data)

    async def find_ready_items(self, limit: int = 10) -> List[QueueItem]:
        """
        처리 준비가 된 대기열 항목 조회

        Args:
            limit: 최대 조회 항목 수

        Returns:
            List[QueueItem]: 처리 준비가 된 대기열 항목 목록
        """
        now = datetime.now().isoformat()

        # 준비된 항목 쿼리: PENDING 또는 (SCHEDULED 이고 scheduled_at <= 현재 시간)
        query = {
            "$or": [
                {"status": QueueStatus.PENDING.value},
                {"status": QueueStatus.SCHEDULED.value, "scheduled_at": {"$lte": now}},
            ]
        }

        # 우선순위 내림차순, 생성 시간 오름차순으로 정렬
        cursor = (
            self.collection.find(query)
            .sort(
                [
                    ("priority", -1),  # 우선순위 내림차순
                    ("created_at", 1),  # 생성 시간 오름차순
                ]
            )
            .limit(limit)
        )

        items = []
        async for data in cursor:
            items.append(QueueItem.from_dict(data))

        return items

    async def find_with_pagination(
        self, filters: Dict[str, Any], page: int = 1, size: int = 10
    ) -> Tuple[List[QueueItem], int]:
        """
        필터와 페이지네이션을 적용하여 대기열 항목 조회

        Args:
            filters: 필터 조건
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            Tuple[List[QueueItem], int]: 조회된 대기열 항목 목록과 전체 항목 수
        """
        # MongoDB 쿼리 필터 변환
        query = {}

        if filters:
            for field, value in filters.items():
                if value is not None:
                    if field == "status":
                        query["status"] = (
                            value.value if isinstance(value, QueueStatus) else value
                        )
                    elif field == "priority":
                        query["priority"] = (
                            value.value if isinstance(value, QueuePriority) else value
                        )
                    else:
                        query[field] = value

        # 전체 개수 조회
        total = await self.collection.count_documents(query)

        # 페이지네이션 적용
        skip = (page - 1) * size
        cursor = self.collection.find(query).skip(skip).limit(size)

        items = []
        async for data in cursor:
            items.append(QueueItem.from_dict(data))

        return items, total

    async def count(self, filters: Dict[str, Any]) -> int:
        """
        필터 조건에 맞는 대기열 항목 수 조회

        Args:
            filters: 필터 조건

        Returns:
            int: 필터 조건에 맞는 대기열 항목 수
        """
        # MongoDB 쿼리 필터 변환
        query = {}

        if filters:
            for field, value in filters.items():
                if value is not None:
                    if field == "status":
                        query["status"] = (
                            value.value if isinstance(value, QueueStatus) else value
                        )
                    elif field == "priority":
                        query["priority"] = (
                            value.value if isinstance(value, QueuePriority) else value
                        )
                    else:
                        query[field] = value

        return await self.collection.count_documents(query)
