"""
MongoDB 큐 서비스 로직 모듈

이 모듈은 MongoDB에 저장된 뉴스 기사를 큐에 추가하고 관리하는 기능을 구현합니다.
MongoDB에 저장된 ArticleModel 객체를 QueueItem으로 변환하여 큐에 추가하고 처리합니다.

데이터 흐름:
크롤링 -> [ArticleDTO] -> [ArticleModel] -> DB 저장 -> [QueueItem] -> 발행
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.article import ArticleModel
from app.models.queue import QueueItem, QueueStatus
from common.utils.logger import get_logger
from db.mongodb import MongoDB
from storage.queue.mongodb_queue import mongodb_queue

logger = get_logger(__name__)


class QueueService:
    """
    큐 서비스 클래스

    MongoDB에 저장된 뉴스 기사를 큐에 추가하고 처리하는 서비스 로직을 구현합니다.
    모든 기사는 먼저 MongoDB에 저장된 후 큐에 추가되어야 합니다.
    """

    def __init__(self, queue=mongodb_queue):
        """
        큐 서비스 초기화

        Args:
            queue: 사용할 큐 구현체 (기본값: mongodb_queue)
        """
        self.queue = queue

    async def add_articles_from_db(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        hours: int = 12,
    ) -> int:
        """
        MongoDB에 저장된 기사를 큐에 추가합니다.

        Args:
            platform: 필터링할 플랫폼 (None이면 모든 플랫폼)
            category: 필터링할 카테고리 (None이면 모든 카테고리)
            limit: 최대 추가할 기사 수
            hours: N시간 이내 수집된 기사만 추가

        Returns:
            int: 성공적으로 추가된 기사 수
        """
        try:
            db = MongoDB.get_database()
            collection = db[ArticleModel.collection_name]

            # 쿼리 조건 구성
            query = {}

            # 플랫폼 필터
            if platform:
                query["metadata.platform"] = platform

            # 카테고리 필터
            if category:
                query["metadata.category"] = category

            # 시간 필터 (N시간 이내)
            if hours > 0:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                query["created_at"] = {"$gte": cutoff_time}

            # 쿼리 실행 (최신순으로 정렬)
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            articles = []

            # 기사 목록 수집
            async for doc in cursor:
                article = ArticleModel.from_document(doc)
                articles.append(article)

            # 수집된 전체 기사 수
            total_found = len(articles)
            logger.info(f"DB에서 {total_found}개 기사 조회됨")

            if total_found == 0:
                return 0

            # 큐에 추가 성공 카운트
            success_count = 0

            # 각 기사를 큐에 추가
            for article in articles:
                try:
                    # ArticleModel을 QueueItem으로 변환
                    queue_item = QueueItem.create_from_article(article)

                    # 중복 확인
                    if await self.queue.is_duplicate(queue_item.unique_id):
                        logger.info(f"이미 큐에 존재하는 기사: {queue_item.title}")
                        continue

                    # 큐에 추가
                    result = await self.queue.enqueue(queue_item)

                    if result:
                        logger.info(f"기사가 발행 큐에 추가됨: {queue_item.title}")
                        success_count += 1
                except Exception as e:
                    logger.error(f"기사 추가 중 오류: {str(e)}")
                    continue

            logger.info(
                f"DB에서 {total_found}개 기사 중 {success_count}개가 큐에 추가됨"
            )
            return success_count

        except Exception as e:
            logger.error(f"DB 기사 큐 추가 중 오류 발생: {str(e)}")
            return 0

    async def get_pending_articles(self, limit: int = 10) -> List[QueueItem]:
        """
        처리할 대기 중인 기사를 가져옵니다.

        Args:
            limit: 가져올 기사 수

        Returns:
            List[QueueItem]: 처리할 기사 목록
        """
        try:
            # 큐에서 처리할 아이템 가져오기
            return await self.queue.dequeue(limit)
        except Exception as e:
            logger.error(f"대기 중인 기사 가져오기 중 오류: {str(e)}")
            return []

    async def mark_article_published(self, unique_id: str) -> bool:
        """
        기사를 발행 완료로 표시합니다.

        Args:
            unique_id: 발행 완료된 기사의 고유 ID

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            return await self.queue.mark_as_completed(unique_id)
        except Exception as e:
            logger.error(f"기사 발행 완료 표시 중 오류: {str(e)}")
            return False

    async def mark_article_failed(
        self, unique_id: str, error_message: str = None
    ) -> bool:
        """
        기사 발행 실패로 표시합니다.

        Args:
            unique_id: 발행 실패한 기사의 고유 ID
            error_message: 실패 원인 메시지

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            return await self.queue.mark_as_failed(unique_id, error_message)
        except Exception as e:
            logger.error(f"기사 발행 실패 표시 중 오류: {str(e)}")
            return False

    async def retry_failed_articles(self, max_retries: int = 3) -> int:
        """
        실패한 기사를 재시도합니다.

        Args:
            max_retries: 최대 재시도 횟수

        Returns:
            int: 재시도 큐에 추가된 기사 수
        """
        try:
            return await self.queue.retry_failed(max_retries)
        except Exception as e:
            logger.error(f"실패 기사 재시도 중 오류: {str(e)}")
            return 0

    async def get_queue_status(self) -> dict:
        """
        큐의 현재 상태를 조회합니다.

        Returns:
            dict: 상태별 기사 수를 포함한 큐 상태 정보
        """
        try:
            return await self.queue.get_status()
        except Exception as e:
            logger.error(f"큐 상태 조회 중 오류: {str(e)}")
            return {}

    async def clean_old_articles(self, days: int = 7) -> int:
        """
        오래된 완료 기사를 정리합니다.

        Args:
            days: 보관할 일수

        Returns:
            int: 정리된 기사 수
        """
        try:
            return await self.queue.clean_completed(days)
        except Exception as e:
            logger.error(f"오래된 기사 정리 중 오류: {str(e)}")
            return 0


# 싱글톤 인스턴스
queue_service = QueueService()
