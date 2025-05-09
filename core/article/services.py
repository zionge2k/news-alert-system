"""
Article 도메인 서비스

이 모듈은 Article 도메인 모델의 비즈니스 로직을 처리하는 서비스를 정의합니다.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from core.article.models import Article, ArticleStatus
from core.article.repositories import ArticleRepository
from core.article.schemas import ArticleCreate, ArticleList, ArticleUpdate
from core.exceptions import (
    BusinessRuleViolationException,
    EntityNotFoundException,
    ValidationException,
)
from core.interfaces import Service

logger = logging.getLogger(__name__)


class ArticleService(Service):
    """
    Article 도메인 서비스

    Article 엔티티에 대한 비즈니스 로직을 처리합니다.
    """

    def __init__(self, repository: ArticleRepository):
        """
        ArticleService 초기화

        Args:
            repository: Article 저장소 인터페이스
        """
        self.repository = repository

    async def create_article(self, data: ArticleCreate) -> Article:
        """
        새 기사 생성

        Args:
            data: 기사 생성 데이터

        Returns:
            Article: 생성된 기사 객체

        Raises:
            ValidationException: 유효성 검증 실패 시
        """
        try:
            article = Article(
                title=data.title,
                content=data.content,
                author_id=data.author_id,
                source=data.source,
                url=data.url,
                metadata=data.metadata,
            )

            return await self.repository.save(article)
        except Exception as e:
            logger.error(f"기사 생성 중 오류 발생: {e}")
            raise ValidationException(str(e))

    async def get_article(self, article_id: str) -> Article:
        """
        기사 조회

        Args:
            article_id: 기사 ID

        Returns:
            Article: 조회된 기사 객체

        Raises:
            EntityNotFoundException: 기사를 찾을 수 없는 경우
        """
        article = await self.repository.find_by_id(article_id)
        if not article:
            raise EntityNotFoundException("Article", article_id)
        return article

    async def update_article(
        self, article_id: str, data: ArticleUpdate, author_id: str
    ) -> Article:
        """
        기사 업데이트

        Args:
            article_id: 기사 ID
            data: 업데이트할 데이터
            author_id: 요청자 ID (권한 검증용)

        Returns:
            Article: 업데이트된 기사 객체

        Raises:
            EntityNotFoundException: 기사를 찾을 수 없는 경우
            BusinessRuleViolationException: 권한이 없는 경우
        """
        article = await self.get_article(article_id)

        # 권한 검증
        if article.author_id != author_id:
            raise BusinessRuleViolationException("기사를 수정할 권한이 없습니다")

        # 이미 발행된 기사는 수정 불가
        if article.status == ArticleStatus.PUBLISHED:
            raise BusinessRuleViolationException(
                "이미 발행된 기사는 수정할 수 없습니다"
            )

        # 데이터 변환
        update_data = {}
        if data.title is not None:
            update_data["title"] = data.title
        if data.content is not None:
            update_data["content"] = data.content
        if data.source is not None:
            update_data["source"] = data.source
        if data.url is not None:
            update_data["url"] = data.url
        if data.metadata is not None:
            update_data["metadata"] = data.metadata

        updated_article = await self.repository.update(article_id, update_data)
        if not updated_article:
            raise EntityNotFoundException("Article", article_id)

        return updated_article

    async def delete_article(
        self, article_id: str, author_id: str, hard_delete: bool = False
    ) -> bool:
        """
        기사 삭제

        Args:
            article_id: 기사 ID
            author_id: 요청자 ID (권한 검증용)
            hard_delete: 하드 삭제 여부 (기본값: False, 소프트 삭제)

        Returns:
            bool: 삭제 성공 여부

        Raises:
            EntityNotFoundException: 기사를 찾을 수 없는 경우
            BusinessRuleViolationException: 권한이 없는 경우
        """
        article = await self.get_article(article_id)

        # 권한 검증
        if article.author_id != author_id:
            raise BusinessRuleViolationException("기사를 삭제할 권한이 없습니다")

        if hard_delete:
            # 하드 삭제
            return await self.repository.delete(article_id)
        else:
            # 소프트 삭제
            article.soft_delete()
            await self.repository.save(article)
            return True

    async def publish_article(self, article_id: str, author_id: str) -> Article:
        """
        기사 발행

        Args:
            article_id: 기사 ID
            author_id: 요청자 ID (권한 검증용)

        Returns:
            Article: 발행된 기사 객체

        Raises:
            EntityNotFoundException: 기사를 찾을 수 없는 경우
            BusinessRuleViolationException: 권한이 없는 경우
        """
        article = await self.get_article(article_id)

        # 권한 검증
        if article.author_id != author_id:
            raise BusinessRuleViolationException("기사를 발행할 권한이 없습니다")

        # 이미 삭제된 기사는 발행 불가
        if article.status == ArticleStatus.DELETED:
            raise BusinessRuleViolationException("삭제된 기사는 발행할 수 없습니다")

        # 발행 상태로 변경
        article.publish()

        # 저장
        return await self.repository.save(article)

    async def restore_article(self, article_id: str, author_id: str) -> Article:
        """
        삭제된 기사 복원

        Args:
            article_id: 기사 ID
            author_id: 요청자 ID (권한 검증용)

        Returns:
            Article: 복원된 기사 객체

        Raises:
            EntityNotFoundException: 기사를 찾을 수 없는 경우
            BusinessRuleViolationException: 권한이 없거나 삭제된 상태가 아닌 경우
        """
        article = await self.get_article(article_id)

        # 권한 검증
        if article.author_id != author_id:
            raise BusinessRuleViolationException("기사를 복원할 권한이 없습니다")

        # 삭제된 상태가 아니면 복원 불가
        if article.status != ArticleStatus.DELETED:
            raise BusinessRuleViolationException(
                "삭제된 상태가 아닌 기사는 복원할 수 없습니다"
            )

        # 복원
        article.restore()

        # 저장
        return await self.repository.save(article)

    async def list_articles(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[ArticleStatus] = None,
        author_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> ArticleList:
        """
        기사 목록 조회

        Args:
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기
            status: 기사 상태 필터
            author_id: 작성자 ID 필터
            source: 출처 필터

        Returns:
            ArticleList: 기사 목록 및 페이지네이션 정보
        """
        filters = {}

        if status:
            filters["status"] = status.value

        if author_id:
            filters["author_id"] = author_id

        if source:
            filters["source"] = source

        articles, total = await self.repository.find_with_pagination(
            filters, page, size
        )

        return ArticleList(items=articles, total=total, page=page, size=size)

    async def search_articles(
        self, query: str, page: int = 1, size: int = 10
    ) -> ArticleList:
        """
        기사 검색

        Args:
            query: 검색 쿼리
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            ArticleList: 검색된 기사 목록 및 페이지네이션 정보
        """
        skip = (page - 1) * size
        articles = await self.repository.search(query, skip, size)

        # 검색 결과의 총 개수를 얻기 위한 추가 쿼리
        # 실제 구현에서는 저장소에서 한 번에 처리하는 것이 효율적
        total = len(await self.repository.search(query, 0, 1000))

        return ArticleList(items=articles, total=total, page=page, size=size)

    async def get_articles_by_source(
        self, source: str, page: int = 1, size: int = 10
    ) -> ArticleList:
        """
        출처별 기사 조회

        Args:
            source: 뉴스 출처
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            ArticleList: 조회된 기사 목록 및 페이지네이션 정보
        """
        skip = (page - 1) * size
        articles = await self.repository.find_by_source(source, skip, size)

        # 총 개수를 얻기 위한 필터
        filters = {"source": source}
        total = await self.repository.count(filters)

        return ArticleList(items=articles, total=total, page=page, size=size)

    async def get_articles_by_author(
        self, author_id: str, page: int = 1, size: int = 10
    ) -> ArticleList:
        """
        작성자별 기사 조회

        Args:
            author_id: 작성자 ID
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            ArticleList: 조회된 기사 목록 및 페이지네이션 정보
        """
        skip = (page - 1) * size
        articles = await self.repository.find_by_author(author_id, skip, size)

        # 총 개수를 얻기 위한 필터
        filters = {"author_id": author_id}
        total = await self.repository.count(filters)

        return ArticleList(items=articles, total=total, page=page, size=size)
