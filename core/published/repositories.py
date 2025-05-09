"""
Published 도메인 저장소

이 모듈은 Published 도메인 모델의 저장소 인터페이스와 구현체를 정의합니다.
"""

import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pymongo.collection import Collection
from pymongo.database import Database

from core.exceptions import EntityNotFoundException
from core.interfaces import Repository
from core.published.models import PublishedArticle, PublishedStatus

logger = logging.getLogger(__name__)


class PublishedRepository(Repository[PublishedArticle, str]):
    """
    PublishedArticle 엔티티를 위한 저장소 인터페이스

    이 인터페이스는 PublishedArticle 엔티티의 CRUD 작업을 정의합니다.
    """

    @abstractmethod
    async def find_by_article_id(self, article_id: str) -> List[PublishedArticle]:
        """
        기사 ID로 발행 항목 조회

        Args:
            article_id: 조회할 기사 ID

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        pass

    @abstractmethod
    async def find_by_platform(
        self, platform: str, skip: int = 0, limit: int = 100
    ) -> List[PublishedArticle]:
        """
        플랫폼별 발행 항목 조회

        Args:
            platform: 조회할 플랫폼
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        pass

    @abstractmethod
    async def find_by_status(
        self, status: PublishedStatus, skip: int = 0, limit: int = 100
    ) -> List[PublishedArticle]:
        """
        상태별 발행 항목 조회

        Args:
            status: 조회할 발행 항목 상태
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        pass

    @abstractmethod
    async def exists(self, article_id: str, platform: str) -> bool:
        """
        특정 기사가 특정 플랫폼에 발행되었는지 확인

        Args:
            article_id: 확인할 기사 ID
            platform: 확인할 플랫폼

        Returns:
            bool: 발행 여부
        """
        pass

    @abstractmethod
    async def count_by_platform(self, platform: str) -> int:
        """
        플랫폼별 발행 항목 수 조회

        Args:
            platform: 조회할 플랫폼

        Returns:
            int: 발행 항목 수
        """
        pass

    @abstractmethod
    async def count_by_status(self, status: PublishedStatus) -> int:
        """
        상태별 발행 항목 수 조회

        Args:
            status: 조회할 상태

        Returns:
            int: 발행 항목 수
        """
        pass


class InMemoryPublishedRepository(PublishedRepository):
    """
    메모리 기반 PublishedRepository 구현체

    테스트 및 개발 목적으로 사용됩니다.
    """

    def __init__(self):
        """InMemoryPublishedRepository 초기화"""
        self.items: Dict[str, PublishedArticle] = {}

    async def save(self, entity: PublishedArticle) -> PublishedArticle:
        """
        발행 항목을 저장합니다.

        Args:
            entity: 저장할 발행 항목

        Returns:
            PublishedArticle: 저장된 발행 항목
        """
        self.items[entity.id] = entity
        return entity

    async def find_by_id(self, id: str) -> Optional[PublishedArticle]:
        """
        ID로 발행 항목을 조회합니다.

        Args:
            id: 발행 항목 ID

        Returns:
            Optional[PublishedArticle]: 조회된 발행 항목 또는 None
        """
        return self.items.get(id)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[PublishedArticle]:
        """
        모든 발행 항목을 조회합니다.

        Args:
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        items = list(self.items.values())
        return items[skip : skip + limit]

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[PublishedArticle]:
        """
        발행 항목을 업데이트합니다.

        Args:
            id: 발행 항목 ID
            data: 업데이트할 데이터

        Returns:
            Optional[PublishedArticle]: 업데이트된 발행 항목 또는 None
        """
        if id not in self.items:
            return None

        entity = self.items[id]

        # 업데이트 가능한 필드만 처리
        if "status" in data:
            entity.status = data["status"]
        if "channel_id" in data:
            entity.channel_id = data["channel_id"]
        if "metadata" in data:
            entity.metadata = data["metadata"]
        if "archived_at" in data:
            entity.archived_at = data["archived_at"]
        if "deleted_at" in data:
            entity.deleted_at = data["deleted_at"]

        return entity

    async def delete(self, id: str) -> bool:
        """
        발행 항목을 삭제합니다.

        Args:
            id: 발행 항목 ID

        Returns:
            bool: 삭제 성공 여부
        """
        if id not in self.items:
            return False

        del self.items[id]
        return True

    async def find_by_article_id(self, article_id: str) -> List[PublishedArticle]:
        """
        기사 ID로 발행 항목을 조회합니다.

        Args:
            article_id: 조회할 기사 ID

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        return [item for item in self.items.values() if item.article_id == article_id]

    async def find_by_platform(
        self, platform: str, skip: int = 0, limit: int = 100
    ) -> List[PublishedArticle]:
        """
        플랫폼별 발행 항목을 조회합니다.

        Args:
            platform: 조회할 플랫폼
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        items = [item for item in self.items.values() if item.platform == platform]
        return items[skip : skip + limit]

    async def find_by_status(
        self, status: PublishedStatus, skip: int = 0, limit: int = 100
    ) -> List[PublishedArticle]:
        """
        상태별 발행 항목을 조회합니다.

        Args:
            status: 조회할 발행 항목 상태
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        items = [item for item in self.items.values() if item.status == status]
        return items[skip : skip + limit]

    async def exists(self, article_id: str, platform: str) -> bool:
        """
        특정 기사가 특정 플랫폼에 발행되었는지 확인합니다.

        Args:
            article_id: 확인할 기사 ID
            platform: 확인할 플랫폼

        Returns:
            bool: 발행 여부
        """
        for item in self.items.values():
            if (
                item.article_id == article_id
                and item.platform == platform
                and item.status == PublishedStatus.PUBLISHED
            ):
                return True
        return False

    async def count_by_platform(self, platform: str) -> int:
        """
        플랫폼별 발행 항목 수를 조회합니다.

        Args:
            platform: 조회할 플랫폼

        Returns:
            int: 발행 항목 수
        """
        return len([item for item in self.items.values() if item.platform == platform])

    async def count_by_status(self, status: PublishedStatus) -> int:
        """
        상태별 발행 항목 수를 조회합니다.

        Args:
            status: 조회할 상태

        Returns:
            int: 발행 항목 수
        """
        return len([item for item in self.items.values() if item.status == status])


class MongoPublishedRepository(PublishedRepository):
    """
    MongoDB 기반 PublishedRepository 구현체
    """

    def __init__(self, db: Database, collection_name: str = "published_articles"):
        """
        MongoPublishedRepository 초기화

        Args:
            db: MongoDB 데이터베이스 객체
            collection_name: 컬렉션 이름 (기본값: "published_articles")
        """
        self.collection: Collection = db[collection_name]

    async def save(self, entity: PublishedArticle) -> PublishedArticle:
        """
        발행 항목을 저장합니다.

        Args:
            entity: 저장할 발행 항목

        Returns:
            PublishedArticle: 저장된 발행 항목
        """
        data = entity.to_dict()

        # upsert 수행
        await self.collection.update_one({"id": entity.id}, {"$set": data}, upsert=True)

        return entity

    async def find_by_id(self, id: str) -> Optional[PublishedArticle]:
        """
        ID로 발행 항목을 조회합니다.

        Args:
            id: 발행 항목 ID

        Returns:
            Optional[PublishedArticle]: 조회된 발행 항목 또는 None
        """
        data = await self.collection.find_one({"id": id})
        if not data:
            return None

        return PublishedArticle.from_dict(data)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[PublishedArticle]:
        """
        모든 발행 항목을 조회합니다.

        Args:
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        cursor = self.collection.find().skip(skip).limit(limit)
        items = []

        async for data in cursor:
            items.append(PublishedArticle.from_dict(data))

        return items

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[PublishedArticle]:
        """
        발행 항목을 업데이트합니다.

        Args:
            id: 발행 항목 ID
            data: 업데이트할 데이터

        Returns:
            Optional[PublishedArticle]: 업데이트된 발행 항목 또는 None
        """
        # 상태가 변경된 경우 상태 관련 필드 자동 업데이트
        if "status" in data:
            status = data["status"]
            if status == PublishedStatus.ARCHIVED:
                data["archived_at"] = datetime.now()
            elif status == PublishedStatus.DELETED:
                data["deleted_at"] = datetime.now()

        result = await self.collection.find_one_and_update(
            {"id": id}, {"$set": data}, return_document=True
        )

        if not result:
            return None

        return PublishedArticle.from_dict(result)

    async def delete(self, id: str) -> bool:
        """
        발행 항목을 삭제합니다.

        Args:
            id: 발행 항목 ID

        Returns:
            bool: 삭제 성공 여부
        """
        result = await self.collection.delete_one({"id": id})
        return result.deleted_count > 0

    async def find_by_article_id(self, article_id: str) -> List[PublishedArticle]:
        """
        기사 ID로 발행 항목을 조회합니다.

        Args:
            article_id: 조회할 기사 ID

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        cursor = self.collection.find({"article_id": article_id})
        items = []

        async for data in cursor:
            items.append(PublishedArticle.from_dict(data))

        return items

    async def find_by_platform(
        self, platform: str, skip: int = 0, limit: int = 100
    ) -> List[PublishedArticle]:
        """
        플랫폼별 발행 항목을 조회합니다.

        Args:
            platform: 조회할 플랫폼
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        cursor = self.collection.find({"platform": platform}).skip(skip).limit(limit)
        items = []

        async for data in cursor:
            items.append(PublishedArticle.from_dict(data))

        return items

    async def find_by_status(
        self, status: PublishedStatus, skip: int = 0, limit: int = 100
    ) -> List[PublishedArticle]:
        """
        상태별 발행 항목을 조회합니다.

        Args:
            status: 조회할 발행 항목 상태
            skip: 건너뛸 항목 수
            limit: 최대 조회 항목 수

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        cursor = self.collection.find({"status": status.value}).skip(skip).limit(limit)
        items = []

        async for data in cursor:
            items.append(PublishedArticle.from_dict(data))

        return items

    async def exists(self, article_id: str, platform: str) -> bool:
        """
        특정 기사가 특정 플랫폼에 발행되었는지 확인합니다.

        Args:
            article_id: 확인할 기사 ID
            platform: 확인할 플랫폼

        Returns:
            bool: 발행 여부
        """
        count = await self.collection.count_documents(
            {
                "article_id": article_id,
                "platform": platform,
                "status": PublishedStatus.PUBLISHED.value,
            }
        )

        return count > 0

    async def count_by_platform(self, platform: str) -> int:
        """
        플랫폼별 발행 항목 수를 조회합니다.

        Args:
            platform: 조회할 플랫폼

        Returns:
            int: 발행 항목 수
        """
        return await self.collection.count_documents({"platform": platform})

    async def count_by_status(self, status: PublishedStatus) -> int:
        """
        상태별 발행 항목 수를 조회합니다.

        Args:
            status: 조회할 상태

        Returns:
            int: 발행 항목 수
        """
        return await self.collection.count_documents({"status": status.value})
