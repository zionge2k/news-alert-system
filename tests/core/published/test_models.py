"""
Published 도메인 모델 테스트
"""

import unittest
from datetime import datetime
from uuid import uuid4

from core.published.models import PublishedArticle, PublishedStatus


class TestPublishedArticle(unittest.TestCase):
    """PublishedArticle 도메인 모델 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.article_id = str(uuid4())
        self.platform = "discord"
        self.channel_id = "123456789"
        self.metadata = {"message_id": "987654321"}

    def test_create_published_article(self):
        """PublishedArticle 생성 테스트"""
        article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            channel_id=self.channel_id,
            metadata=self.metadata,
        )

        self.assertEqual(article.article_id, self.article_id)
        self.assertEqual(article.platform, self.platform)
        self.assertEqual(article.channel_id, self.channel_id)
        self.assertEqual(article.metadata, self.metadata)
        self.assertEqual(article.status, PublishedStatus.PUBLISHED)
        self.assertIsNotNone(article.id)
        self.assertIsNotNone(article.published_at)
        self.assertIsNone(article.archived_at)
        self.assertIsNone(article.deleted_at)

    def test_archive_published_article(self):
        """PublishedArticle 보관 테스트"""
        article = PublishedArticle(article_id=self.article_id, platform=self.platform)

        article.archive()

        self.assertEqual(article.status, PublishedStatus.ARCHIVED)
        self.assertIsNotNone(article.archived_at)
        self.assertIsNone(article.deleted_at)

    def test_delete_published_article(self):
        """PublishedArticle 삭제 테스트"""
        article = PublishedArticle(article_id=self.article_id, platform=self.platform)

        article.delete()

        self.assertEqual(article.status, PublishedStatus.DELETED)
        self.assertIsNone(article.archived_at)
        self.assertIsNotNone(article.deleted_at)

    def test_restore_published_article(self):
        """PublishedArticle 복원 테스트"""
        # 보관된 기사 복원
        archived_article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.ARCHIVED,
            archived_at=datetime.now(),
        )

        archived_article.restore()

        self.assertEqual(archived_article.status, PublishedStatus.PUBLISHED)

        # 삭제된 기사 복원
        deleted_article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.DELETED,
            deleted_at=datetime.now(),
        )

        deleted_article.restore()

        self.assertEqual(deleted_article.status, PublishedStatus.PUBLISHED)

    def test_update_metadata(self):
        """PublishedArticle 메타데이터 업데이트 테스트"""
        article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            metadata={"key1": "value1"},
        )

        article.update_metadata({"key2": "value2"})

        self.assertEqual(article.metadata, {"key1": "value1", "key2": "value2"})

    def test_is_published(self):
        """PublishedArticle 발행 상태 확인 테스트"""
        published_article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.PUBLISHED,
        )

        archived_article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.ARCHIVED,
        )

        deleted_article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.DELETED,
        )

        self.assertTrue(published_article.is_published())
        self.assertFalse(archived_article.is_published())
        self.assertFalse(deleted_article.is_published())

    def test_to_dict(self):
        """PublishedArticle to_dict 메서드 테스트"""
        now = datetime.now()
        article = PublishedArticle(
            id="test-id",
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.PUBLISHED,
            published_at=now,
            channel_id=self.channel_id,
            metadata=self.metadata,
        )

        data = article.to_dict()

        self.assertEqual(data["id"], "test-id")
        self.assertEqual(data["article_id"], self.article_id)
        self.assertEqual(data["platform"], self.platform)
        self.assertEqual(data["status"], "published")
        self.assertEqual(data["published_at"], now.isoformat())
        self.assertEqual(data["channel_id"], self.channel_id)
        self.assertEqual(data["metadata"], self.metadata)

    def test_from_dict(self):
        """PublishedArticle from_dict 메서드 테스트"""
        now = datetime.now()
        data = {
            "id": "test-id",
            "article_id": self.article_id,
            "platform": self.platform,
            "status": "published",
            "published_at": now.isoformat(),
            "channel_id": self.channel_id,
            "metadata": self.metadata,
        }

        article = PublishedArticle.from_dict(data)

        self.assertEqual(article.id, "test-id")
        self.assertEqual(article.article_id, self.article_id)
        self.assertEqual(article.platform, self.platform)
        self.assertEqual(article.status, PublishedStatus.PUBLISHED)
        self.assertEqual(article.published_at.isoformat(), now.isoformat())
        self.assertEqual(article.channel_id, self.channel_id)
        self.assertEqual(article.metadata, self.metadata)

    def test_archive_invalid_status(self):
        """이미 보관된 기사를 보관하려고 할 때 예외 발생 테스트"""
        article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.ARCHIVED,
        )

        with self.assertRaises(ValueError):
            article.archive()

    def test_delete_already_deleted(self):
        """이미 삭제된 기사를 삭제하려고 할 때 예외 발생 테스트"""
        article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.DELETED,
        )

        with self.assertRaises(ValueError):
            article.delete()

    def test_restore_already_published(self):
        """이미 발행된 기사를 복원하려고 할 때 예외 발생 테스트"""
        article = PublishedArticle(
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.PUBLISHED,
        )

        with self.assertRaises(ValueError):
            article.restore()


if __name__ == "__main__":
    unittest.main()
