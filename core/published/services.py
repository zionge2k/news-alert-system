"""
Published 도메인 서비스

이 모듈은 Published 도메인 모델의 비즈니스 로직을 처리하는 서비스를 정의합니다.
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
from core.published.models import PublishedArticle, PublishedStatus
from core.published.repositories import PublishedRepository
from core.published.schemas import (
    PublishedArticleCreate,
    PublishedArticleList,
    PublishedArticleResponse,
    PublishedArticleUpdate,
)

logger = logging.getLogger(__name__)


class PublishedService(Service):
    """
    Published 도메인 서비스

    Published 엔티티에 대한 비즈니스 로직을 처리합니다.
    """

    def __init__(self, repository: PublishedRepository):
        """
        PublishedService 초기화

        Args:
            repository: Published 저장소 인터페이스
        """
        self.repository = repository

    async def publish_article(self, data: PublishedArticleCreate) -> PublishedArticle:
        """
        기사 발행을 기록합니다.

        Args:
            data: 발행 기사 생성 데이터

        Returns:
            PublishedArticle: 생성된 발행 기사

        Raises:
            ValidationException: 유효성 검증 실패 시
            BusinessRuleViolationException: 이미 발행된 기사인 경우
        """
        try:
            # 이미 발행되었는지 확인
            exists = await self.repository.exists(data.article_id, data.platform)
            if exists:
                raise BusinessRuleViolationException(
                    f"Article with id '{data.article_id}' is already published on platform '{data.platform}'"
                )

            # 새 발행 항목 생성
            published_article = PublishedArticle(
                article_id=data.article_id,
                platform=data.platform,
                channel_id=data.channel_id,
                metadata=data.metadata,
            )

            return await self.repository.save(published_article)
        except Exception as e:
            if not isinstance(e, BusinessRuleViolationException):
                logger.error(f"기사 발행 기록 중 오류 발생: {e}")
                raise ValidationException(str(e))
            raise

    async def get_published_article(self, article_id: str) -> PublishedArticle:
        """
        발행된 기사를 조회합니다.

        Args:
            article_id: 발행 항목 ID

        Returns:
            PublishedArticle: 조회된 발행 항목

        Raises:
            EntityNotFoundException: 발행 항목을 찾을 수 없는 경우
        """
        item = await self.repository.find_by_id(article_id)
        if not item:
            raise EntityNotFoundException("PublishedArticle", article_id)
        return item

    async def get_published_by_article_id(
        self, article_id: str
    ) -> List[PublishedArticle]:
        """
        기사 ID로 발행 항목을 조회합니다.

        Args:
            article_id: 기사 ID

        Returns:
            List[PublishedArticle]: 조회된 발행 항목 목록
        """
        return await self.repository.find_by_article_id(article_id)

    async def update_published_article(
        self, article_id: str, data: PublishedArticleUpdate
    ) -> PublishedArticle:
        """
        발행 항목을 업데이트합니다.

        Args:
            article_id: 발행 항목 ID
            data: 업데이트할 데이터

        Returns:
            PublishedArticle: 업데이트된 발행 항목

        Raises:
            EntityNotFoundException: 발행 항목을 찾을 수 없는 경우
        """
        # 데이터 변환
        update_data = {}
        if data.status is not None:
            update_data["status"] = data.status
        if data.channel_id is not None:
            update_data["channel_id"] = data.channel_id
        if data.metadata is not None:
            update_data["metadata"] = data.metadata

        updated_item = await self.repository.update(article_id, update_data)
        if not updated_item:
            raise EntityNotFoundException("PublishedArticle", article_id)

        return updated_item

    async def archive_published_article(self, article_id: str) -> PublishedArticle:
        """
        발행 항목을 보관 상태로 변경합니다.

        Args:
            article_id: 발행 항목 ID

        Returns:
            PublishedArticle: 업데이트된 발행 항목

        Raises:
            EntityNotFoundException: 발행 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 보관이 허용되지 않는 상태인 경우
        """
        item = await self.get_published_article(article_id)

        try:
            item.archive()
            return await self.repository.save(item)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e))

    async def delete_published_article(self, article_id: str) -> PublishedArticle:
        """
        발행 항목을 삭제 상태로 변경합니다.

        Args:
            article_id: 발행 항목 ID

        Returns:
            PublishedArticle: 업데이트된 발행 항목

        Raises:
            EntityNotFoundException: 발행 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 삭제가 허용되지 않는 상태인 경우
        """
        item = await self.get_published_article(article_id)

        try:
            item.delete()
            return await self.repository.save(item)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e))

    async def restore_published_article(self, article_id: str) -> PublishedArticle:
        """
        삭제되거나 보관된 발행 항목을 발행 상태로 복원합니다.

        Args:
            article_id: 발행 항목 ID

        Returns:
            PublishedArticle: 업데이트된 발행 항목

        Raises:
            EntityNotFoundException: 발행 항목을 찾을 수 없는 경우
            BusinessRuleViolationException: 복원이 허용되지 않는 상태인 경우
        """
        item = await self.get_published_article(article_id)

        try:
            item.restore()
            return await self.repository.save(item)
        except ValueError as e:
            raise BusinessRuleViolationException(str(e))

    async def remove_published_article(self, article_id: str) -> bool:
        """
        발행 항목을 영구적으로 삭제합니다.

        Args:
            article_id: 발행 항목 ID

        Returns:
            bool: 삭제 성공 여부

        Raises:
            EntityNotFoundException: 발행 항목을 찾을 수 없는 경우
        """
        # 발행 항목이 존재하는지 확인
        item = await self.repository.find_by_id(article_id)
        if not item:
            raise EntityNotFoundException("PublishedArticle", article_id)

        return await self.repository.delete(article_id)

    async def list_published_articles(
        self,
        page: int = 1,
        size: int = 10,
        platform: Optional[str] = None,
        status: Optional[PublishedStatus] = None,
    ) -> PublishedArticleList:
        """
        발행 항목 목록을 조회합니다.

        Args:
            page: 페이지 번호
            size: 페이지 크기
            platform: 플랫폼 필터
            status: 상태 필터

        Returns:
            PublishedArticleList: 발행 항목 목록
        """
        skip = (page - 1) * size

        # 필터에 따라 조회 방법 결정
        if platform and status:
            # 플랫폼과 상태 모두 필터링
            total = 0  # 복합 필터링에 대한 카운트는 구현 필요
            items = []  # 복합 필터링에 대한 조회는 구현 필요
        elif platform:
            # 플랫폼으로 필터링
            total = await self.repository.count_by_platform(platform)
            items = await self.repository.find_by_platform(platform, skip, size)
        elif status:
            # 상태로 필터링
            total = await self.repository.count_by_status(status)
            items = await self.repository.find_by_status(status, skip, size)
        else:
            # 필터 없음
            items = await self.repository.find_all(skip, size)
            # 전체 개수 계산 (임시)
            all_items = await self.repository.find_all(0, 1000)
            total = len(all_items)

        # 응답 모델로 변환
        response_items = []
        for item in items:
            response_items.append(
                PublishedArticleResponse(
                    id=item.id,
                    article_id=item.article_id,
                    platform=item.platform,
                    status=item.status,
                    published_at=item.published_at,
                    archived_at=item.archived_at,
                    deleted_at=item.deleted_at,
                    channel_id=item.channel_id,
                    metadata=item.metadata,
                )
            )

        return PublishedArticleList(
            items=response_items, total=total, page=page, size=size
        )

    async def is_article_published(self, article_id: str, platform: str) -> bool:
        """
        기사가 특정 플랫폼에 발행되었는지 확인합니다.

        Args:
            article_id: 확인할 기사 ID
            platform: 확인할 플랫폼

        Returns:
            bool: 발행 여부
        """
        return await self.repository.exists(article_id, platform)
