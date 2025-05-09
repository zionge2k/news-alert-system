"""
Published 도메인 저장소 테스트
"""

import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from core.published.models import PublishedArticle, PublishedStatus
from core.published.repositories import InMemoryPublishedRepository


class TestInMemoryPublishedRepository(unittest.TestCase):
    """InMemoryPublishedRepository 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.repository = InMemoryPublishedRepository()

        # 테스트 데이터
        self.article_id = "test-article-id"
        self.platform = "discord"
        self.channel_id = "test-channel-id"
        self.metadata = {"message_id": "test-message-id"}

        # 샘플 PublishedArticle 객체
        self.published_article = PublishedArticle(
            id="test-id",
            article_id=self.article_id,
            platform=self.platform,
            channel_id=self.channel_id,
            metadata=self.metadata,
        )

    def test_save(self):
        """저장소 저장 테스트"""
        # 테스트 실행
        result = asyncio.run(self.repository.save(self.published_article))

        # 검증
        self.assertEqual(result, self.published_article)
        self.assertEqual(self.repository.items["test-id"], self.published_article)

    def test_find_by_id(self):
        """ID로 조회 테스트"""
        # 데이터 설정
        asyncio.run(self.repository.save(self.published_article))

        # 테스트 실행
        result = asyncio.run(self.repository.find_by_id("test-id"))

        # 검증
        self.assertEqual(result, self.published_article)

    def test_find_by_id_not_found(self):
        """존재하지 않는 ID로 조회 테스트"""
        # 테스트 실행
        result = asyncio.run(self.repository.find_by_id("non-existent-id"))

        # 검증
        self.assertIsNone(result)

    def test_find_all(self):
        """모든 항목 조회 테스트"""
        # 데이터 설정
        article1 = PublishedArticle(id="id1", article_id="article1", platform="discord")
        article2 = PublishedArticle(id="id2", article_id="article2", platform="discord")
        article3 = PublishedArticle(id="id3", article_id="article3", platform="slack")

        asyncio.run(self.repository.save(article1))
        asyncio.run(self.repository.save(article2))
        asyncio.run(self.repository.save(article3))

        # 테스트 실행 - 모든 항목
        result1 = asyncio.run(self.repository.find_all())

        # 테스트 실행 - 페이징
        result2 = asyncio.run(self.repository.find_all(skip=1, limit=1))

        # 검증
        self.assertEqual(len(result1), 3)
        self.assertEqual(len(result2), 1)

    def test_update(self):
        """항목 업데이트 테스트"""
        # 데이터 설정
        asyncio.run(self.repository.save(self.published_article))

        # 테스트 실행
        result = asyncio.run(
            self.repository.update(
                "test-id",
                {
                    "status": PublishedStatus.ARCHIVED,
                    "channel_id": "new-channel-id",
                    "metadata": {"key": "new-value"},
                    "archived_at": datetime.now(),
                },
            )
        )

        # 검증
        self.assertEqual(result.status, PublishedStatus.ARCHIVED)
        self.assertEqual(result.channel_id, "new-channel-id")
        self.assertEqual(result.metadata, {"key": "new-value"})
        self.assertIsNotNone(result.archived_at)

    def test_update_not_found(self):
        """존재하지 않는 항목 업데이트 테스트"""
        # 테스트 실행
        result = asyncio.run(
            self.repository.update(
                "non-existent-id", {"status": PublishedStatus.ARCHIVED}
            )
        )

        # 검증
        self.assertIsNone(result)

    def test_delete(self):
        """항목 삭제 테스트"""
        # 데이터 설정
        asyncio.run(self.repository.save(self.published_article))

        # 테스트 실행
        result = asyncio.run(self.repository.delete("test-id"))

        # 검증
        self.assertTrue(result)
        self.assertNotIn("test-id", self.repository.items)

    def test_delete_not_found(self):
        """존재하지 않는 항목 삭제 테스트"""
        # 테스트 실행
        result = asyncio.run(self.repository.delete("non-existent-id"))

        # 검증
        self.assertFalse(result)

    def test_find_by_article_id(self):
        """기사 ID로 조회 테스트"""
        # 데이터 설정
        article1 = PublishedArticle(id="id1", article_id="article1", platform="discord")
        article2 = PublishedArticle(id="id2", article_id="article1", platform="slack")
        article3 = PublishedArticle(id="id3", article_id="article2", platform="discord")

        asyncio.run(self.repository.save(article1))
        asyncio.run(self.repository.save(article2))
        asyncio.run(self.repository.save(article3))

        # 테스트 실행
        result = asyncio.run(self.repository.find_by_article_id("article1"))

        # 검증
        self.assertEqual(len(result), 2)
        self.assertIn(article1, result)
        self.assertIn(article2, result)

    def test_find_by_platform(self):
        """플랫폼으로 조회 테스트"""
        # 데이터 설정
        article1 = PublishedArticle(id="id1", article_id="article1", platform="discord")
        article2 = PublishedArticle(id="id2", article_id="article2", platform="discord")
        article3 = PublishedArticle(id="id3", article_id="article3", platform="slack")

        asyncio.run(self.repository.save(article1))
        asyncio.run(self.repository.save(article2))
        asyncio.run(self.repository.save(article3))

        # 테스트 실행
        result1 = asyncio.run(self.repository.find_by_platform("discord"))
        result2 = asyncio.run(self.repository.find_by_platform("slack"))

        # 검증
        self.assertEqual(len(result1), 2)
        self.assertEqual(len(result2), 1)

    def test_find_by_status(self):
        """상태로 조회 테스트"""
        # 데이터 설정
        article1 = PublishedArticle(
            id="id1",
            article_id="article1",
            platform="discord",
            status=PublishedStatus.PUBLISHED,
        )
        article2 = PublishedArticle(
            id="id2",
            article_id="article2",
            platform="discord",
            status=PublishedStatus.ARCHIVED,
        )
        article3 = PublishedArticle(
            id="id3",
            article_id="article3",
            platform="slack",
            status=PublishedStatus.PUBLISHED,
        )

        asyncio.run(self.repository.save(article1))
        asyncio.run(self.repository.save(article2))
        asyncio.run(self.repository.save(article3))

        # 테스트 실행
        result1 = asyncio.run(self.repository.find_by_status(PublishedStatus.PUBLISHED))
        result2 = asyncio.run(self.repository.find_by_status(PublishedStatus.ARCHIVED))

        # 검증
        self.assertEqual(len(result1), 2)
        self.assertEqual(len(result2), 1)

    def test_exists(self):
        """발행 여부 확인 테스트"""
        # 데이터 설정
        article1 = PublishedArticle(
            id="id1",
            article_id="article1",
            platform="discord",
            status=PublishedStatus.PUBLISHED,
        )
        article2 = PublishedArticle(
            id="id2",
            article_id="article2",
            platform="discord",
            status=PublishedStatus.ARCHIVED,
        )
        article3 = PublishedArticle(
            id="id3",
            article_id="article3",
            platform="slack",
            status=PublishedStatus.PUBLISHED,
        )

        asyncio.run(self.repository.save(article1))
        asyncio.run(self.repository.save(article2))
        asyncio.run(self.repository.save(article3))

        # 테스트 실행
        result1 = asyncio.run(self.repository.exists("article1", "discord"))
        result2 = asyncio.run(self.repository.exists("article2", "discord"))
        result3 = asyncio.run(self.repository.exists("article3", "discord"))

        # 검증
        self.assertTrue(result1)
        self.assertFalse(result2)  # 보관 상태이므로 발행되지 않음
        self.assertFalse(result3)  # 플랫폼이 다름

    def test_count_by_platform(self):
        """플랫폼별 항목 수 테스트"""
        # 데이터 설정
        article1 = PublishedArticle(id="id1", article_id="article1", platform="discord")
        article2 = PublishedArticle(id="id2", article_id="article2", platform="discord")
        article3 = PublishedArticle(id="id3", article_id="article3", platform="slack")

        asyncio.run(self.repository.save(article1))
        asyncio.run(self.repository.save(article2))
        asyncio.run(self.repository.save(article3))

        # 테스트 실행
        result1 = asyncio.run(self.repository.count_by_platform("discord"))
        result2 = asyncio.run(self.repository.count_by_platform("slack"))

        # 검증
        self.assertEqual(result1, 2)
        self.assertEqual(result2, 1)

    def test_count_by_status(self):
        """상태별 항목 수 테스트"""
        # 데이터 설정
        article1 = PublishedArticle(
            id="id1",
            article_id="article1",
            platform="discord",
            status=PublishedStatus.PUBLISHED,
        )
        article2 = PublishedArticle(
            id="id2",
            article_id="article2",
            platform="discord",
            status=PublishedStatus.ARCHIVED,
        )
        article3 = PublishedArticle(
            id="id3",
            article_id="article3",
            platform="slack",
            status=PublishedStatus.PUBLISHED,
        )

        asyncio.run(self.repository.save(article1))
        asyncio.run(self.repository.save(article2))
        asyncio.run(self.repository.save(article3))

        # 테스트 실행
        result1 = asyncio.run(
            self.repository.count_by_status(PublishedStatus.PUBLISHED)
        )
        result2 = asyncio.run(self.repository.count_by_status(PublishedStatus.ARCHIVED))

        # 검증
        self.assertEqual(result1, 2)
        self.assertEqual(result2, 1)


# 몽고DB 저장소 테스트는 모킹을 사용하여 구현
class TestMongoPublishedRepository(unittest.TestCase):
    """MongoPublishedRepository 테스트"""

    @patch("core.published.repositories.Collection")
    def setUp(self, mock_collection):
        """테스트 데이터 및 모의 객체 설정"""
        # 모의 MongoDB 컬렉션 설정
        self.mock_collection = mock_collection
        self.mock_db = Mock()
        self.mock_db.__getitem__.return_value = self.mock_collection

        # 저장소 생성
        from core.published.repositories import MongoPublishedRepository

        self.repository = MongoPublishedRepository(self.mock_db)

        # 테스트 데이터
        self.article_id = "test-article-id"
        self.platform = "discord"
        self.channel_id = "test-channel-id"
        self.metadata = {"message_id": "test-message-id"}

        # 샘플 PublishedArticle 객체
        self.published_article = PublishedArticle(
            id="test-id",
            article_id=self.article_id,
            platform=self.platform,
            channel_id=self.channel_id,
            metadata=self.metadata,
        )

    def test_save(self):
        """저장소 저장 테스트"""
        # 모의 객체 설정
        self.mock_collection.update_one = AsyncMock()

        # 테스트 실행
        result = asyncio.run(self.repository.save(self.published_article))

        # 검증
        self.mock_collection.update_one.assert_called_once()
        self.assertEqual(result, self.published_article)

    def test_find_by_id(self):
        """ID로 조회 테스트"""
        # 모의 객체 설정
        self.mock_collection.find_one = AsyncMock(
            return_value=self.published_article.to_dict()
        )

        # 테스트 실행
        result = asyncio.run(self.repository.find_by_id("test-id"))

        # 검증
        self.mock_collection.find_one.assert_called_once_with({"id": "test-id"})
        self.assertEqual(result.id, self.published_article.id)
        self.assertEqual(result.article_id, self.published_article.article_id)

    def test_find_by_id_not_found(self):
        """존재하지 않는 ID로 조회 테스트"""
        # 모의 객체 설정
        self.mock_collection.find_one = AsyncMock(return_value=None)

        # 테스트 실행
        result = asyncio.run(self.repository.find_by_id("non-existent-id"))

        # 검증
        self.assertIsNone(result)

    def test_delete(self):
        """항목 삭제 테스트"""
        # 모의 객체 설정
        mock_result = Mock()
        mock_result.deleted_count = 1
        self.mock_collection.delete_one = AsyncMock(return_value=mock_result)

        # 테스트 실행
        result = asyncio.run(self.repository.delete("test-id"))

        # 검증
        self.mock_collection.delete_one.assert_called_once_with({"id": "test-id"})
        self.assertTrue(result)

    def test_delete_not_found(self):
        """존재하지 않는 항목 삭제 테스트"""
        # 모의 객체 설정
        mock_result = Mock()
        mock_result.deleted_count = 0
        self.mock_collection.delete_one = AsyncMock(return_value=mock_result)

        # 테스트 실행
        result = asyncio.run(self.repository.delete("non-existent-id"))

        # 검증
        self.assertFalse(result)

    def test_exists(self):
        """발행 여부 확인 테스트"""
        # 모의 객체 설정
        self.mock_collection.count_documents = AsyncMock(return_value=1)

        # 테스트 실행
        result = asyncio.run(self.repository.exists("article1", "discord"))

        # 검증
        self.mock_collection.count_documents.assert_called_once()
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
