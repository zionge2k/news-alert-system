"""
Article 도메인 모델

이 모듈은 뉴스 기사(Article)와 관련된 도메인 모델을 정의합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class ArticleStatus(str, Enum):
    """기사 상태를 나타내는 열거형"""

    DRAFT = "draft"  # 임시 저장된 기사
    PUBLISHED = "published"  # 발행된 기사
    DELETED = "deleted"  # 삭제된 기사


class Article:
    """
    뉴스 기사 도메인 모델

    기사의 핵심 속성과 비즈니스 로직을 포함합니다.
    """

    def __init__(
        self,
        title: str,
        content: str,
        author_id: str,
        source: str,
        id: Optional[str] = None,
        status: ArticleStatus = ArticleStatus.DRAFT,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        published_at: Optional[datetime] = None,
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Article 객체 초기화

        Args:
            title: 기사 제목
            content: 기사 본문 내용
            author_id: 작성자 ID
            source: 뉴스 출처 (예: "JTBC", "MBC", "YTN")
            id: 기사 ID (기본값: 자동 생성된 UUID)
            status: 기사 상태 (기본값: DRAFT)
            created_at: 생성 시간 (기본값: 현재 시간)
            updated_at: 마지막 수정 시간 (기본값: 현재 시간)
            published_at: 발행 시간 (기본값: None)
            url: 원본 기사 URL (기본값: None)
            metadata: 추가 메타데이터 (기본값: 빈 딕셔너리)
        """
        self.id = id if id else str(uuid4())
        self.title = title
        self.content = content
        self.author_id = author_id
        self.source = source
        self.status = status
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()
        self.published_at = published_at
        self.url = url
        self.metadata = metadata if metadata else {}

    def update_content(
        self, title: Optional[str] = None, content: Optional[str] = None
    ) -> None:
        """
        기사 내용 업데이트

        Args:
            title: 새 제목 (None인 경우 변경 없음)
            content: 새 내용 (None인 경우 변경 없음)
        """
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        self.updated_at = datetime.utcnow()

    def publish(self) -> None:
        """
        기사를 발행 상태로 변경

        이미 발행된 경우 아무 작업도 수행하지 않습니다.
        """
        if self.status != ArticleStatus.PUBLISHED:
            self.status = ArticleStatus.PUBLISHED
            self.published_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """
        기사를 삭제 상태로 변경 (소프트 삭제)

        이미 삭제된 경우 아무 작업도 수행하지 않습니다.
        """
        if self.status != ArticleStatus.DELETED:
            self.status = ArticleStatus.DELETED
            self.updated_at = datetime.utcnow()

    def restore(self) -> None:
        """
        삭제된 기사를 복원

        삭제된 상태가 아닌 경우 아무 작업도 수행하지 않습니다.
        """
        if self.status == ArticleStatus.DELETED:
            self.status = ArticleStatus.DRAFT
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Article 객체를 딕셔너리로 변환

        Returns:
            Dict[str, Any]: 기사 데이터를 포함한 딕셔너리
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author_id": self.author_id,
            "source": self.source,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": (
                self.published_at.isoformat() if self.published_at else None
            ),
            "url": self.url,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Article":
        """
        딕셔너리에서 Article 객체 생성

        Args:
            data: 기사 데이터를 포함한 딕셔너리

        Returns:
            Article: 생성된 Article 객체
        """
        # datetime 문자열을 datetime 객체로 변환
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if "created_at" in data and data["created_at"]
            else None
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data and data["updated_at"]
            else None
        )
        published_at = (
            datetime.fromisoformat(data["published_at"])
            if "published_at" in data and data["published_at"]
            else None
        )

        # 상태 문자열을 ArticleStatus 열거형으로 변환
        status = (
            ArticleStatus(data["status"])
            if "status" in data and data["status"]
            else ArticleStatus.DRAFT
        )

        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            content=data.get("content", ""),
            author_id=data.get("author_id", ""),
            source=data.get("source", ""),
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            published_at=published_at,
            url=data.get("url"),
            metadata=data.get("metadata", {}),
        )
