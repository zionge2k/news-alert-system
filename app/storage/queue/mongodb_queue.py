"""
MongoDB 기반 큐 구현 모듈

이 모듈은 MongoDB를 사용하여 큐 기능을 구현합니다.
QueueInterface를 상속받아 모든 큐 기능을 MongoDB 컬렉션으로 구현합니다.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.models.queue import QueueItem, QueueStatus, get_queue_collection_name
from app.storage.queue.interfaces import QueueInterface
from common.utils.logger import get_logger
from db.mongodb import MongoDB

logger = get_logger(__name__)


class MongoDBQueue(QueueInterface):
    """
    MongoDB를 사용한 큐 시스템 구현

    QueueInterface를 상속받아 MongoDB 컬렉션을 사용하여 큐 기능을 구현합니다.
    중복 방지와 상태 관리를 처리합니다.
    """

    def __init__(self):
        """
        MongoDB 큐 초기화
        """
        self.collection_name = get_queue_collection_name()

    @property
    def collection(self):
        """
        MongoDB 컬렉션 객체 반환
        """
        db = MongoDB.get_database()
        return db[self.collection_name]

    async def enqueue(self, item: QueueItem) -> bool:
        """
        큐에 아이템을 추가합니다.
        중복 아이템은 추가되지 않습니다.

        Args:
            item: 큐에 추가할 QueueItem 객체

        Returns:
            bool: 추가 성공 여부
        """
        try:
            # 중복 확인
            if await self.is_duplicate(item.unique_id):
                logger.info(f"중복 아이템 건너뜀: {item.unique_id}")
                return False

            # 큐에 아이템 추가
            document = item.to_document()
            await self.collection.insert_one(document)
            logger.info(f"아이템 추가됨: {item.unique_id}")
            return True

        except DuplicateKeyError:
            # 레이스 컨디션으로 인한 중복 체크 우회 시
            logger.warning(f"중복 키 오류 (동시 삽입 시도): {item.unique_id}")
            return False

        except Exception as e:
            logger.error(f"큐 아이템 추가 중 오류: {str(e)}")
            return False

    async def dequeue(self, limit: int = 1) -> List[QueueItem]:
        """
        큐에서 처리할 아이템을 가져오고 상태를 PROCESSING으로 변경합니다.

        Args:
            limit: 가져올 아이템 수

        Returns:
            List[QueueItem]: 처리할 아이템 목록
        """
        result = []
        current_time = datetime.now()

        try:
            # 대기 중인 아이템을 생성 시간 순으로 조회 (FIFO)
            cursor = (
                self.collection.find({"status": QueueStatus.PENDING.value})
                .sort("created_at", 1)
                .limit(limit)
            )

            async for document in cursor:
                item_id = document["unique_id"]

                # 아이템 상태를 PROCESSING으로 업데이트
                updated_doc = await self.collection.find_one_and_update(
                    {"unique_id": item_id, "status": QueueStatus.PENDING.value},
                    {
                        "$set": {
                            "status": QueueStatus.PROCESSING.value,
                            "updated_at": current_time,
                        }
                    },
                    return_document=ReturnDocument.AFTER,
                )

                if updated_doc:
                    # 성공적으로 업데이트된 경우에만 결과에 추가
                    # MongoDB _id 필드 처리를 위해 모델 메서드 사용
                    result.append(
                        QueueItem.model_validate(
                            QueueItem.process_mongodb_id(updated_doc)
                        )
                    )
                    logger.debug(f"아이템 처리 중: {item_id}")

            logger.info(f"{len(result)}개 아이템을 큐에서 가져옴")
            return result

        except Exception as e:
            logger.error(f"큐에서 아이템 가져오기 중 오류: {str(e)}")
            return []

    async def mark_as_completed(self, item_id: str) -> bool:
        """
        아이템을 완료 상태로 표시합니다.

        Args:
            item_id: 완료할 아이템의 ID (unique_id)

        Returns:
            bool: 업데이트 성공 여부
        """
        current_time = datetime.now()

        try:
            result = await self.collection.update_one(
                {"unique_id": item_id},
                {
                    "$set": {
                        "status": QueueStatus.COMPLETED.value,
                        "updated_at": current_time,
                        "published_at": current_time,
                    }
                },
            )

            success = result.modified_count > 0
            if success:
                logger.info(f"아이템 완료 처리됨: {item_id}")
            else:
                logger.warning(f"아이템 완료 처리 실패 (없거나 이미 완료됨): {item_id}")

            return success

        except Exception as e:
            logger.error(f"아이템 완료 처리 중 오류: {str(e)}")
            return False

    async def mark_as_failed(self, item_id: str, error_message: str = None) -> bool:
        """
        아이템을 실패 상태로 표시하고 재시도 횟수를 증가시킵니다.

        Args:
            item_id: 실패한 아이템의 ID (unique_id)
            error_message: 실패 원인 메시지

        Returns:
            bool: 업데이트 성공 여부
        """
        current_time = datetime.now()

        try:
            update_data = {
                "$set": {
                    "status": QueueStatus.FAILED.value,
                    "updated_at": current_time,
                },
                "$inc": {"retry_count": 1},
            }

            if error_message:
                update_data["$set"]["error_message"] = error_message

            result = await self.collection.update_one(
                {"unique_id": item_id}, update_data
            )

            success = result.modified_count > 0
            if success:
                logger.info(f"아이템 실패 처리됨: {item_id}")
            else:
                logger.warning(
                    f"아이템 실패 처리 실패 (없거나 이미 실패 상태): {item_id}"
                )

            return success

        except Exception as e:
            logger.error(f"아이템 실패 처리 중 오류: {str(e)}")
            return False

    async def retry_failed(self, max_retries: int = 3) -> int:
        """
        실패한 아이템을 재시도합니다.
        최대 재시도 횟수 이하인 아이템만 다시 PENDING 상태로 변경합니다.

        Args:
            max_retries: 최대 재시도 횟수

        Returns:
            int: 재시도 큐에 추가된 아이템 수
        """
        current_time = datetime.now()

        try:
            result = await self.collection.update_many(
                {
                    "status": QueueStatus.FAILED.value,
                    "retry_count": {"$lt": max_retries},
                },
                {
                    "$set": {
                        "status": QueueStatus.PENDING.value,
                        "updated_at": current_time,
                        "error_message": None,
                    }
                },
            )

            retry_count = result.modified_count
            logger.info(f"{retry_count}개 실패 아이템 재시도 처리")
            return retry_count

        except Exception as e:
            logger.error(f"실패 아이템 재시도 처리 중 오류: {str(e)}")
            return 0

    async def is_duplicate(self, unique_id: str) -> bool:
        """
        중복 아이템인지 확인합니다.

        Args:
            unique_id: 확인할 아이템의 고유 ID

        Returns:
            bool: 중복 여부
        """
        try:
            result = await self.collection.find_one(
                {"unique_id": unique_id}, projection={"_id": 1}
            )
            return result is not None

        except Exception as e:
            logger.error(f"중복 확인 중 오류: {str(e)}")
            return False

    async def get_status(self) -> dict:
        """
        큐의 현재 상태를 조회합니다.

        Returns:
            dict: 상태별 아이템 수를 포함한 큐 상태 정보
        """
        try:
            pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]

            cursor = self.collection.aggregate(pipeline)
            status_counts = {}

            async for doc in cursor:
                status_counts[doc["_id"]] = doc["count"]

            # 모든 상태에 대해 기본값 0으로 설정
            for status in QueueStatus:
                if status.value not in status_counts:
                    status_counts[status.value] = 0

            # 전체 개수 추가
            total_count = sum(status_counts.values())
            status_counts["total"] = total_count

            return status_counts

        except Exception as e:
            logger.error(f"큐 상태 조회 중 오류: {str(e)}")
            return {status.value: 0 for status in QueueStatus}

    async def clean_completed(self) -> int:
        """
        완료된 모든 아이템을 정리합니다.

        Returns:
            int: 정리된 아이템 수
        """
        try:
            result = await self.collection.delete_many(
                {
                    "status": QueueStatus.COMPLETED.value,
                }
            )

            deleted_count = result.deleted_count
            logger.info(f"{deleted_count}개의 완료 아이템 정리됨")
            return deleted_count

        except Exception as e:
            logger.error(f"완료 아이템 정리 중 오류: {str(e)}")
            return 0


# 싱글톤 인스턴스
mongodb_queue = MongoDBQueue()
