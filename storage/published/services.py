"""
발행된 기사 관리 서비스 모듈

이 모듈은 다양한 플랫폼에 발행된 기사를 추적하고 관리하는 서비스를 제공합니다.
중복 발행 방지 및 발행 이력 관리 기능을 구현합니다.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Set

from app.models.published import PublishedArticle, PublishStatus
from common.utils.logger import get_logger
from db.mongodb import MongoDB

logger = get_logger(__name__)


class PublishedArticleService:
    """
    발행된 기사 관리 서비스

    다양한 플랫폼에 발행된 기사를 추적하고 관리합니다.
    발행 이력 저장, 조회 및 중복 발행 방지 기능을 제공합니다.
    """

    def __init__(self):
        """
        발행 기사 서비스 초기화
        """
        self.collection_name = PublishedArticle.collection_name

    @property
    def collection(self):
        """
        발행 기사 컬렉션 객체 반환
        """
        db = MongoDB.get_database()
        return db[self.collection_name]

    async def mark_as_published(
        self, unique_id: str, platform: str, channel_id: Optional[str] = None
    ) -> bool:
        """
        기사를 발행 완료 상태로 표시합니다.

        Args:
            unique_id: 발행된 기사의 고유 ID
            platform: 발행된 플랫폼 (discord, slack 등)
            channel_id: 발행된 채널 ID

        Returns:
            bool: 등록 성공 여부
        """
        try:
            published_article = PublishedArticle(
                unique_id=unique_id,
                platform=platform,
                published_at=datetime.now(),
                channel_id=channel_id,
                status=PublishStatus.SUCCESS.value,
                retry_count=0,
            )

            await self.collection.insert_one(published_article.to_document())
            logger.info(f"기사가 발행 완료로 등록됨: {platform}/{unique_id}")
            return True

        except Exception as e:
            logger.error(f"기사 발행 완료 등록 중 오류: {str(e)}")
            return False

    async def mark_as_failed(
        self, unique_id: str, platform: str, retry_count: int = 1
    ) -> bool:
        """
        기사 발행 실패를 기록합니다.

        Args:
            unique_id: 발행 실패한 기사의 고유 ID
            platform: 발행 플랫폼
            retry_count: 시도 횟수

        Returns:
            bool: 등록 성공 여부
        """
        try:
            published_article = PublishedArticle(
                unique_id=unique_id,
                platform=platform,
                published_at=datetime.now(),
                status=PublishStatus.FAILED.value,
                retry_count=retry_count,
            )

            await self.collection.insert_one(published_article.to_document())
            logger.info(
                f"기사 발행 실패로 등록됨: {platform}/{unique_id} (시도 횟수: {retry_count})"
            )
            return True

        except Exception as e:
            logger.error(f"기사 발행 실패 등록 중 오류: {str(e)}")
            return False

    async def is_published(self, unique_id: str, platform: str = None) -> bool:
        """
        기사가 이미 발행되었는지 확인합니다.

        Args:
            unique_id: 확인할 기사의 고유 ID
            platform: 특정 플랫폼 (None이면 모든 플랫폼에서 검색)

        Returns:
            bool: 발행 여부
        """
        try:
            query = {"unique_id": unique_id, "status": PublishStatus.SUCCESS.value}

            if platform:
                query["platform"] = platform

            result = await self.collection.find_one(query, projection={"_id": 1})
            return result is not None

        except Exception as e:
            logger.error(f"기사 발행 확인 중 오류: {str(e)}")
            return False

    async def get_published_article_ids(
        self, platform: str = None, hours: int = 0
    ) -> Set[str]:
        """
        지정된 조건에 맞는 발행된 기사의 ID 목록을 반환합니다.

        Args:
            platform: 특정 플랫폼 (None이면 모든 플랫폼)
            hours: 특정 시간 이내에 발행된 기사만 조회 (0이면 시간 제한 없음)

        Returns:
            Set[str]: 발행된 기사 ID 세트
        """
        query = {"status": PublishStatus.SUCCESS.value}

        if platform:
            query["platform"] = platform

        if hours > 0:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            query["published_at"] = {"$gte": cutoff_time}

        try:
            published_ids = set()

            async for doc in self.collection.find(query, projection={"unique_id": 1}):
                if "unique_id" in doc:  # unique_id 필드가 있는지 확인
                    published_ids.add(doc["unique_id"])

            logger.info(f"{len(published_ids)}개의 발행된 기사 ID 조회됨")
            return published_ids

        except Exception as e:
            logger.error(f"발행된 기사 ID 조회 중 오류: {str(e)}")
            return set()


# 싱글톤 인스턴스
published_article_service = PublishedArticleService()
