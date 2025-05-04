"""
큐 시스템 인터페이스 정의 모듈

이 모듈은 MongoDB를 사용한 뉴스 기사 큐 시스템의 인터페이스를 정의합니다.
다양한 큐 구현체가 준수해야 할 공통 인터페이스를 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union

from app.models.queue import QueueItem, QueueStatus


class QueueInterface(ABC):
    """
    큐 시스템을 위한 기본 인터페이스

    모든 큐 구현체가 구현해야 하는 기본 메서드를 정의합니다.
    """

    @abstractmethod
    async def enqueue(self, item: QueueItem) -> bool:
        """
        큐에 아이템을 추가합니다.

        Args:
            item: 큐에 추가할 QueueItem 객체

        Returns:
            bool: 추가 성공 여부
        """
        pass

    @abstractmethod
    async def dequeue(self, limit: int = 1) -> List[QueueItem]:
        """
        큐에서 처리할 아이템을 가져옵니다.

        Args:
            limit: 가져올 아이템 수

        Returns:
            List[QueueItem]: 처리할 아이템 목록
        """
        pass

    @abstractmethod
    async def mark_as_completed(self, item_id: str) -> bool:
        """
        아이템을 완료 상태로 표시합니다.

        Args:
            item_id: 완료할 아이템의 ID (unique_id)

        Returns:
            bool: 업데이트 성공 여부
        """
        pass

    @abstractmethod
    async def mark_as_failed(self, item_id: str, error_message: str = None) -> bool:
        """
        아이템을 실패 상태로 표시합니다.

        Args:
            item_id: 실패한 아이템의 ID (unique_id)
            error_message: 실패 원인 메시지

        Returns:
            bool: 업데이트 성공 여부
        """
        pass

    @abstractmethod
    async def retry_failed(self, max_retries: int = 3) -> int:
        """
        실패한 아이템을 재시도합니다.

        Args:
            max_retries: 최대 재시도 횟수

        Returns:
            int: 재시도 큐에 추가된 아이템 수
        """
        pass

    @abstractmethod
    async def is_duplicate(self, unique_id: str) -> bool:
        """
        중복 아이템인지 확인합니다.

        Args:
            unique_id: 확인할 아이템의 고유 ID

        Returns:
            bool: 중복 여부
        """
        pass

    @abstractmethod
    async def get_status(self) -> dict:
        """
        큐의 현재 상태를 조회합니다.

        Returns:
            dict: 상태별 아이템 수를 포함한 큐 상태 정보
        """
        pass

    @abstractmethod
    async def clean_completed(self) -> int:
        """
        완료된 모든 아이템을 정리합니다.

        Returns:
            int: 정리된 아이템 수
        """
        pass
