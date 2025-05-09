"""
Article 도메인 저장소

이 모듈은 Article 도메인 모델의 저장소 인터페이스와 구현체를 정의합니다.
"""

import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pymongo.collection import Collection
from pymongo.database import Database

from core.article.models import Article, ArticleStatus
from core.exceptions import EntityNotFoundException
from core.interfaces import Repository

logger = logging.getLogger(__name__)


class ArticleRepository(Repository[Article, str]):
    """
    Article 엔티티를 위한 저장소 인터페이스

    이 인터페이스는 Article 엔티티의 CRUD 작업을 정의합니다.
    """

    @abstractmethod
    async def find_by_status(
        self, status: ArticleStatus, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        상태별 기사 조회

        Args:
            status: 조회할 기사 상태
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        pass

    @abstractmethod
    async def find_by_author(
        self, author_id: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        작성자별 기사 조회

        Args:
            author_id: 작성자 ID
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        pass

    @abstractmethod
    async def find_by_source(
        self, source: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        출처별 기사 조회

        Args:
            source: 뉴스 출처
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        pass

    @abstractmethod
    async def search(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        기사 검색

        Args:
            query: 검색 쿼리
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 검색된 기사 목록
        """
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        기사 수 조회

        Args:
            filters: 필터 조건

        Returns:
            int: 조회된 기사 수
        """
        pass

    @abstractmethod
    async def find_with_pagination(
        self, filters: Optional[Dict[str, Any]] = None, page: int = 1, size: int = 10
    ) -> Tuple[List[Article], int]:
        """
        페이지네이션을 적용한 기사 조회

        Args:
            filters: 필터 조건
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            Tuple[List[Article], int]: 조회된 기사 목록과 전체 기사 수
        """
        pass


class InMemoryArticleRepository(ArticleRepository):
    """
    메모리 기반 Article 저장소 구현체

    테스트 및 개발 환경에서 사용하기 위한 인메모리 저장소입니다.
    """

    def __init__(self):
        self._articles: Dict[str, Article] = {}

    async def save(self, entity: Article) -> Article:
        """
        기사 저장

        Args:
            entity: 저장할 Article 객체

        Returns:
            Article: 저장된 Article 객체
        """
        self._articles[entity.id] = entity
        return entity

    async def find_by_id(self, id: str) -> Optional[Article]:
        """
        ID로 기사 조회

        Args:
            id: 기사 ID

        Returns:
            Optional[Article]: 조회된 Article 객체 또는 None
        """
        return self._articles.get(id)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Article]:
        """
        모든 기사 조회

        Args:
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        articles = list(self._articles.values())
        return articles[skip : skip + limit]

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Article]:
        """
        기사 업데이트

        Args:
            id: 기사 ID
            data: 업데이트할 데이터

        Returns:
            Optional[Article]: 업데이트된 Article 객체 또는 None
        """
        article = await self.find_by_id(id)
        if not article:
            return None

        if "title" in data:
            article.title = data["title"]
        if "content" in data:
            article.content = data["content"]
        if "source" in data:
            article.source = data["source"]
        if "url" in data:
            article.url = data["url"]
        if "metadata" in data:
            article.metadata = data["metadata"]

        article.updated_at = datetime.utcnow()
        self._articles[id] = article
        return article

    async def delete(self, id: str) -> bool:
        """
        기사 삭제

        Args:
            id: 기사 ID

        Returns:
            bool: 삭제 성공 여부
        """
        if id in self._articles:
            del self._articles[id]
            return True
        return False

    async def find_by_status(
        self, status: ArticleStatus, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        상태별 기사 조회

        Args:
            status: 조회할 기사 상태
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        articles = [
            article for article in self._articles.values() if article.status == status
        ]
        return articles[skip : skip + limit]

    async def find_by_author(
        self, author_id: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        작성자별 기사 조회

        Args:
            author_id: 작성자 ID
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        articles = [
            article
            for article in self._articles.values()
            if article.author_id == author_id
        ]
        return articles[skip : skip + limit]

    async def find_by_source(
        self, source: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        출처별 기사 조회

        Args:
            source: 뉴스 출처
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        articles = [
            article for article in self._articles.values() if article.source == source
        ]
        return articles[skip : skip + limit]

    async def search(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        기사 검색

        Args:
            query: 검색 쿼리
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 검색된 기사 목록
        """
        query = query.lower()
        articles = [
            article
            for article in self._articles.values()
            if query in article.title.lower() or query in article.content.lower()
        ]
        return articles[skip : skip + limit]

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        기사 수 조회

        Args:
            filters: 필터 조건

        Returns:
            int: 조회된 기사 수
        """
        if not filters:
            return len(self._articles)

        count = 0
        for article in self._articles.values():
            match = True
            for key, value in filters.items():
                if key == "status" and isinstance(value, str):
                    if article.status.value != value:
                        match = False
                        break
                elif key == "status" and isinstance(value, ArticleStatus):
                    if article.status != value:
                        match = False
                        break
                elif getattr(article, key, None) != value:
                    match = False
                    break
            if match:
                count += 1

        return count

    async def find_with_pagination(
        self, filters: Optional[Dict[str, Any]] = None, page: int = 1, size: int = 10
    ) -> Tuple[List[Article], int]:
        """
        페이지네이션을 적용한 기사 조회

        Args:
            filters: 필터 조건
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            Tuple[List[Article], int]: 조회된 기사 목록과 전체 기사 수
        """
        if not filters:
            filters = {}

        filtered_articles = []
        for article in self._articles.values():
            match = True
            for key, value in filters.items():
                if key == "status" and isinstance(value, str):
                    if article.status.value != value:
                        match = False
                        break
                elif key == "status" and isinstance(value, ArticleStatus):
                    if article.status != value:
                        match = False
                        break
                elif getattr(article, key, None) != value:
                    match = False
                    break
            if match:
                filtered_articles.append(article)

        total = len(filtered_articles)
        skip = (page - 1) * size
        paginated_articles = filtered_articles[skip : skip + size]

        return paginated_articles, total


class MongoArticleRepository(ArticleRepository):
    """
    MongoDB 기반 Article 저장소 구현체

    MongoDB를 사용하여 Article 엔티티를 저장하고 조회합니다.
    """

    def __init__(self, db: Database, collection_name: str = "articles"):
        """
        MongoDB 저장소 초기화

        Args:
            db: MongoDB 데이터베이스 인스턴스
            collection_name: 컬렉션 이름 (기본값: "articles")
        """
        self._collection: Collection = db[collection_name]

    async def save(self, entity: Article) -> Article:
        """
        기사 저장

        Args:
            entity: 저장할 Article 객체

        Returns:
            Article: 저장된 Article 객체
        """
        data = entity.to_dict()
        await self._collection.replace_one({"id": entity.id}, data, upsert=True)
        return entity

    async def find_by_id(self, id: str) -> Optional[Article]:
        """
        ID로 기사 조회

        Args:
            id: 기사 ID

        Returns:
            Optional[Article]: 조회된 Article 객체 또는 None
        """
        data = await self._collection.find_one({"id": id})
        if not data:
            return None
        return Article.from_dict(data)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Article]:
        """
        모든 기사 조회

        Args:
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        cursor = self._collection.find().skip(skip).limit(limit)
        articles = []
        async for data in cursor:
            articles.append(Article.from_dict(data))
        return articles

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Article]:
        """
        기사 업데이트

        Args:
            id: 기사 ID
            data: 업데이트할 데이터

        Returns:
            Optional[Article]: 업데이트된 Article 객체 또는 None

        Raises:
            EntityNotFoundException: 기사를 찾을 수 없는 경우
        """
        article = await self.find_by_id(id)
        if not article:
            raise EntityNotFoundException("Article", id)

        update_data = {"$set": {}}

        if "title" in data:
            update_data["$set"]["title"] = data["title"]
        if "content" in data:
            update_data["$set"]["content"] = data["content"]
        if "source" in data:
            update_data["$set"]["source"] = data["source"]
        if "url" in data:
            update_data["$set"]["url"] = data["url"]
        if "metadata" in data:
            update_data["$set"]["metadata"] = data["metadata"]

        update_data["$set"]["updated_at"] = datetime.utcnow().isoformat()

        await self._collection.update_one({"id": id}, update_data)
        return await self.find_by_id(id)

    async def delete(self, id: str) -> bool:
        """
        기사 삭제

        Args:
            id: 기사 ID

        Returns:
            bool: 삭제 성공 여부
        """
        result = await self._collection.delete_one({"id": id})
        return result.deleted_count > 0

    async def find_by_status(
        self, status: ArticleStatus, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        상태별 기사 조회

        Args:
            status: 조회할 기사 상태
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        cursor = self._collection.find({"status": status.value}).skip(skip).limit(limit)
        articles = []
        async for data in cursor:
            articles.append(Article.from_dict(data))
        return articles

    async def find_by_author(
        self, author_id: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        작성자별 기사 조회

        Args:
            author_id: 작성자 ID
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        cursor = self._collection.find({"author_id": author_id}).skip(skip).limit(limit)
        articles = []
        async for data in cursor:
            articles.append(Article.from_dict(data))
        return articles

    async def find_by_source(
        self, source: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        출처별 기사 조회

        Args:
            source: 뉴스 출처
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 조회된 기사 목록
        """
        cursor = self._collection.find({"source": source}).skip(skip).limit(limit)
        articles = []
        async for data in cursor:
            articles.append(Article.from_dict(data))
        return articles

    async def search(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Article]:
        """
        기사 검색

        Args:
            query: 검색 쿼리
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            List[Article]: 검색된 기사 목록
        """
        # 텍스트 인덱스가 있다고 가정
        cursor = (
            self._collection.find({"$text": {"$search": query}}).skip(skip).limit(limit)
        )

        articles = []
        async for data in cursor:
            articles.append(Article.from_dict(data))
        return articles

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        기사 수 조회

        Args:
            filters: 필터 조건

        Returns:
            int: 조회된 기사 수
        """
        if not filters:
            return await self._collection.count_documents({})
        return await self._collection.count_documents(filters)

    async def find_with_pagination(
        self, filters: Optional[Dict[str, Any]] = None, page: int = 1, size: int = 10
    ) -> Tuple[List[Article], int]:
        """
        페이지네이션을 적용한 기사 조회

        Args:
            filters: 필터 조건
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            Tuple[List[Article], int]: 조회된 기사 목록과 전체 기사 수
        """
        if not filters:
            filters = {}

        skip = (page - 1) * size
        cursor = self._collection.find(filters).skip(skip).limit(size)

        articles = []
        async for data in cursor:
            articles.append(Article.from_dict(data))

        total = await self.count(filters)
        return articles, total
