from typing import Any, Dict, List, Optional

from app.models.article import ArticleModel

from ..mongodb import MongoDB
from .interfaces.article_repository import BaseArticleRepository


class MongoArticleRepository(BaseArticleRepository):
    """
    MongoDB를 사용하여 기사 데이터를 저장하고 조회하는 저장소

    BaseArticleRepository 인터페이스를 구현하며, MongoDB에 특화된 구현을 제공합니다.
    """

    collection_name = ArticleModel.collection_name

    async def save_article(self, article: ArticleModel) -> Any:
        """MongoDB에 기사를 저장하고 ObjectId를 반환합니다."""
        db = MongoDB.get_database()
        result = await db[self.collection_name].insert_one(article.model_dump())
        return result.inserted_id

    async def find_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """MongoDB에서 특정 플랫폼의 기사를 조회합니다."""
        db = MongoDB.get_database()
        cursor = db[self.collection_name].find({"metadata.platform": platform})
        return await cursor.to_list(length=100)

    async def find_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """MongoDB 텍스트 인덱스를 사용하여 키워드가 포함된 기사를 검색합니다."""
        db = MongoDB.get_database()
        cursor = db[self.collection_name].find({"$text": {"$search": keyword}})
        return await cursor.to_list(length=100)

    async def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """MongoDB에서 URL로 기사를 조회합니다."""
        db = MongoDB.get_database()
        result = await db[self.collection_name].find_one({"url": url})
        return result

    async def find_by_unique_id(self, unique_id: str) -> Optional[Dict[str, Any]]:
        """MongoDB에서 unique_id로 기사를 조회합니다. (복합키 기반 중복 검사)"""
        db = MongoDB.get_database()
        result = await db[self.collection_name].find_one({"unique_id": unique_id})
        return result

    async def find_by_platform_and_article_id(
        self, platform: str, article_id: str
    ) -> Optional[Dict[str, Any]]:
        """플랫폼과 기사ID 조합으로 기사를 조회합니다."""
        unique_id = f"{platform}_{article_id}"
        return await self.find_by_unique_id(unique_id)


# 싱글톤 인스턴스 생성
article_repository = MongoArticleRepository()
