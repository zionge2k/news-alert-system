"""
Published 도메인 모델

이 모듈은 발행된 뉴스 기사(Article)와 관련된 도메인 모델을 정의합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class PublishedStatus(str, Enum):
    """발행된 기사의 상태를 나타내는 열거형"""

    PUBLISHED = "published"  # 발행됨
    ARCHIVED = "archived"  # 보관됨
    DELETED = "deleted"  # 삭제됨


class PublishedArticle:
    """
    발행된 기사 도메인 모델

    발행된 기사의 속성과 비즈니스 로직을 포함합니다.
    """

    def __init__(
        self,
        article_id: str,
        platform: str,
        id: Optional[str] = None,
        status: PublishedStatus = PublishedStatus.PUBLISHED,
        published_at: Optional[datetime] = None,
        archived_at: Optional[datetime] = None,
        deleted_at: Optional[datetime] = None,
        channel_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        PublishedArticle 초기화

        Args:
            article_id: 발행된 기사의 ID
            platform: 발행 플랫폼 (discord, slack 등)
            id: 발행 항목 ID (기본값: 자동 생성)
            status: 발행 상태 (기본값: PUBLISHED)
            published_at: 발행 시간 (기본값: 현재 시간)
            archived_at: 보관 시간
            deleted_at: 삭제 시간
            channel_id: 발행된 채널 ID
            metadata: 추가 메타데이터
        """
        self.id = id if id else str(uuid4())
        self.article_id = article_id
        self.platform = platform
        self.status = status
        self.published_at = published_at if published_at else datetime.now()
        self.archived_at = archived_at
        self.deleted_at = deleted_at
        self.channel_id = channel_id
        self.metadata = metadata if metadata else {}

    def archive(self) -> None:
        """기사를 보관 상태로 변경합니다."""
        if self.status != PublishedStatus.PUBLISHED:
            raise ValueError(f"Cannot archive article with status {self.status}")

        self.status = PublishedStatus.ARCHIVED
        self.archived_at = datetime.now()

    def delete(self) -> None:
        """기사를 삭제 상태로 변경합니다."""
        if self.status == PublishedStatus.DELETED:
            raise ValueError("Article is already deleted")

        self.status = PublishedStatus.DELETED
        self.deleted_at = datetime.now()

    def restore(self) -> None:
        """삭제되거나 보관된 기사를 발행 상태로 복원합니다."""
        if self.status == PublishedStatus.PUBLISHED:
            raise ValueError("Article is already in published state")

        self.status = PublishedStatus.PUBLISHED

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        메타데이터를 업데이트합니다.

        Args:
            metadata: 업데이트할 메타데이터
        """
        self.metadata.update(metadata)

    def is_published(self) -> bool:
        """
        기사가 발행 상태인지 확인합니다.

        Returns:
            bool: 발행 상태 여부
        """
        return self.status == PublishedStatus.PUBLISHED

    def to_dict(self) -> Dict[str, Any]:
        """
        PublishedArticle을 딕셔너리로 변환합니다.

        Returns:
            Dict[str, Any]: PublishedArticle의 딕셔너리 표현
        """
        return {
            "id": self.id,
            "article_id": self.article_id,
            "platform": self.platform,
            "status": self.status.value,
            "published_at": self.published_at.isoformat(),
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "channel_id": self.channel_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PublishedArticle":
        """
        딕셔너리에서 PublishedArticle을 생성합니다.

        Args:
            data: PublishedArticle 데이터가 포함된 딕셔너리

        Returns:
            PublishedArticle: 생성된 PublishedArticle 객체
        """
        # 열거형 값 변환
        status = (
            PublishedStatus(data["status"])
            if "status" in data
            else PublishedStatus.PUBLISHED
        )

        # 날짜 변환
        published_at = (
            datetime.fromisoformat(data["published_at"])
            if "published_at" in data
            else None
        )
        archived_at = (
            datetime.fromisoformat(data["archived_at"])
            if "archived_at" in data and data["archived_at"]
            else None
        )
        deleted_at = (
            datetime.fromisoformat(data["deleted_at"])
            if "deleted_at" in data and data["deleted_at"]
            else None
        )

        return cls(
            id=data.get("id"),
            article_id=data["article_id"],
            platform=data["platform"],
            status=status,
            published_at=published_at,
            archived_at=archived_at,
            deleted_at=deleted_at,
            channel_id=data.get("channel_id"),
            metadata=data.get("metadata", {}),
        )
