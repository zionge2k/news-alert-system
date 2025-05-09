"""
ArticleModel 테스트.
"""

from datetime import datetime

import pytest

from app.models.article import ArticleModel, MongoArticleMetadata
from app.schemas.article import ArticleDTO, ArticleMetadata


@pytest.mark.unit
class TestArticleModel:
    """ArticleModel 클래스 테스트."""

    def test_from_article_dto(self):
        """ArticleDTO에서 ArticleModel으로 변환하는 기능 테스트."""
        # ArticleDTO 생성
        metadata = ArticleMetadata(
            platform="TEST",
            category="정치",
            tags=["테스트", "뉴스"],
            published_at=datetime.now(),
        )

        dto = ArticleDTO(
            title="테스트 기사",
            url="https://example.com/test",
            author="테스트 작성자",
            content="테스트 내용",
            metadata=metadata,
        )

        # ArticleModel로 변환
        model = ArticleModel.from_article_dto(dto)

        # 변환 결과 검증
        assert model.title == "테스트 기사"
        assert model.url == "https://example.com/test"
        assert model.author == "테스트 작성자"
        assert model.content == "테스트 내용"
        assert model.metadata.platform == "TEST"
        assert model.metadata.category == "정치"
        assert model.metadata.tags == ["테스트", "뉴스"]
        assert model.unique_id.startswith("TEST_")

    def test_to_document(self):
        """ArticleModel을 MongoDB 문서로 변환하는 기능 테스트."""
        # ArticleModel 생성
        metadata = MongoArticleMetadata(
            platform="TEST",
            category="경제",
            tags=["주식", "시장"],
            published_at=datetime.now(),
        )

        model = ArticleModel(
            title="주식시장 동향",
            url="https://example.com/stock",
            author="경제 기자",
            content="주식시장이 상승세를 보이고 있습니다.",
            metadata=metadata,
            unique_id="TEST_123456",
        )

        # 문서로 변환
        doc = model.to_document()

        # 변환 결과 검증
        assert isinstance(doc, dict)
        assert doc["title"] == "주식시장 동향"
        assert doc["url"] == "https://example.com/stock"
        assert doc["author"] == "경제 기자"
        assert doc["content"] == "주식시장이 상승세를 보이고 있습니다."
        assert doc["unique_id"] == "TEST_123456"
        assert "metadata" in doc
        assert doc["metadata"]["platform"] == "TEST"
