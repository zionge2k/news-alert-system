"""
Queue 도메인 모델

이 모듈은 뉴스 기사(Article)의 발행 대기열과 관련된 도메인 모델을 정의합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class QueueStatus(str, Enum):
    """대기열 항목의 상태를 나타내는 열거형"""

    PENDING = "pending"  # 대기 중
    SCHEDULED = "scheduled"  # 발행 예약됨
    PROCESSING = "processing"  # 처리 중
    COMPLETED = "completed"  # 처리 완료
    FAILED = "failed"  # 처리 실패
    CANCELLED = "cancelled"  # 취소됨


class QueuePriority(int, Enum):
    """대기열 항목의 우선순위를 나타내는 열거형"""

    LOW = 0  # 낮은 우선순위
    NORMAL = 1  # 일반 우선순위
    HIGH = 2  # 높은 우선순위
    URGENT = 3  # 긴급 우선순위


class QueueItem:
    """
    대기열 항목 도메인 모델

    대기열에 있는 기사의 속성과 비즈니스 로직을 포함합니다.
    """

    def __init__(
        self,
        article_id: str,
        id: Optional[str] = None,
        status: QueueStatus = QueueStatus.PENDING,
        priority: QueuePriority = QueuePriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        processed_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        """
        QueueItem 초기화

        Args:
            article_id: 대기열에 등록된 기사 ID
            id: 대기열 항목 ID (기본값: 자동 생성)
            status: 대기열 항목 상태 (기본값: PENDING)
            priority: 대기열 항목 우선순위 (기본값: NORMAL)
            scheduled_at: 발행 예약 시간
            created_at: 생성 시간 (기본값: 현재 시간)
            updated_at: 마지막 업데이트 시간 (기본값: 현재 시간)
            processed_at: 처리 완료 시간
            metadata: 추가 메타데이터
            error_message: 실패 시 오류 메시지
        """
        self.id = id if id else str(uuid4())
        self.article_id = article_id
        self.status = status
        self.priority = priority
        self.scheduled_at = scheduled_at
        self.created_at = created_at if created_at else datetime.now()
        self.updated_at = updated_at if updated_at else datetime.now()
        self.processed_at = processed_at
        self.metadata = metadata if metadata else {}
        self.error_message = error_message

    def schedule(self, scheduled_at: datetime) -> None:
        """
        기사 발행을 예약합니다.

        Args:
            scheduled_at: 발행 예약 시간
        """
        if self.status not in [QueueStatus.PENDING, QueueStatus.SCHEDULED]:
            raise ValueError(f"Cannot schedule item with status {self.status}")

        self.scheduled_at = scheduled_at
        self.status = QueueStatus.SCHEDULED
        self.updated_at = datetime.now()

    def start_processing(self) -> None:
        """기사 처리를 시작합니다."""
        if self.status not in [QueueStatus.PENDING, QueueStatus.SCHEDULED]:
            raise ValueError(f"Cannot start processing item with status {self.status}")

        self.status = QueueStatus.PROCESSING
        self.updated_at = datetime.now()

    def complete(self) -> None:
        """기사 처리를 완료합니다."""
        if self.status != QueueStatus.PROCESSING:
            raise ValueError(f"Cannot complete item with status {self.status}")

        self.status = QueueStatus.COMPLETED
        self.processed_at = datetime.now()
        self.updated_at = datetime.now()

    def fail(self, error_message: str) -> None:
        """
        기사 처리 실패를 기록합니다.

        Args:
            error_message: 실패 이유를 설명하는 오류 메시지
        """
        self.status = QueueStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """기사 처리를 취소합니다."""
        if self.status in [QueueStatus.COMPLETED, QueueStatus.FAILED]:
            raise ValueError(f"Cannot cancel item with status {self.status}")

        self.status = QueueStatus.CANCELLED
        self.updated_at = datetime.now()

    def retry(self) -> None:
        """실패한 기사 처리를 재시도합니다."""
        if self.status != QueueStatus.FAILED:
            raise ValueError(f"Cannot retry item with status {self.status}")

        self.status = QueueStatus.PENDING
        self.error_message = None
        self.updated_at = datetime.now()

    def set_priority(self, priority: QueuePriority) -> None:
        """
        기사의 처리 우선순위를 설정합니다.

        Args:
            priority: 새 우선순위 값
        """
        self.priority = priority
        self.updated_at = datetime.now()

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        메타데이터를 업데이트합니다.

        Args:
            metadata: 업데이트할 메타데이터
        """
        self.metadata.update(metadata)
        self.updated_at = datetime.now()

    def is_ready_to_process(self) -> bool:
        """
        기사가 처리 준비가 되었는지 확인합니다.

        Returns:
            bool: 처리 준비 여부
        """
        if self.status != QueueStatus.SCHEDULED:
            return self.status == QueueStatus.PENDING

        # 예약된 경우 예약 시간이 현재 시간보다 이전인지 확인
        return self.scheduled_at is not None and self.scheduled_at <= datetime.now()

    def is_active(self) -> bool:
        """
        기사가 활성 상태인지 확인합니다 (아직 처리 중이거나 대기 중).

        Returns:
            bool: 활성 상태 여부
        """
        return self.status in [
            QueueStatus.PENDING,
            QueueStatus.SCHEDULED,
            QueueStatus.PROCESSING,
        ]

    def to_dict(self) -> Dict[str, Any]:
        """
        QueueItem을 딕셔너리로 변환합니다.

        Returns:
            Dict[str, Any]: QueueItem의 딕셔너리 표현
        """
        return {
            "id": self.id,
            "article_id": self.article_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "scheduled_at": (
                self.scheduled_at.isoformat() if self.scheduled_at else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "metadata": self.metadata,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueueItem":
        """
        딕셔너리에서 QueueItem을 생성합니다.

        Args:
            data: QueueItem 데이터가 포함된 딕셔너리

        Returns:
            QueueItem: 생성된 QueueItem 객체
        """
        # 열거형 값 변환
        status = (
            QueueStatus(data["status"]) if "status" in data else QueueStatus.PENDING
        )
        priority = (
            QueuePriority(data["priority"])
            if "priority" in data
            else QueuePriority.NORMAL
        )

        # 날짜 변환
        created_at = (
            datetime.fromisoformat(data["created_at"]) if "created_at" in data else None
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else None
        )
        scheduled_at = (
            datetime.fromisoformat(data["scheduled_at"])
            if "scheduled_at" in data and data["scheduled_at"]
            else None
        )
        processed_at = (
            datetime.fromisoformat(data["processed_at"])
            if "processed_at" in data and data["processed_at"]
            else None
        )

        return cls(
            id=data.get("id"),
            article_id=data["article_id"],
            status=status,
            priority=priority,
            scheduled_at=scheduled_at,
            created_at=created_at,
            updated_at=updated_at,
            processed_at=processed_at,
            metadata=data.get("metadata", {}),
            error_message=data.get("error_message"),
        )
