"""
Published 도메인 서비스 테스트
"""

import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from core.exceptions import (
    BusinessRuleViolationException,
    EntityNotFoundException,
    ValidationException,
)
from core.published.models import PublishedArticle, PublishedStatus
from core.published.schemas import PublishedArticleCreate, PublishedArticleUpdate
from core.published.services import PublishedService


class TestPublishedService(unittest.TestCase):
    """PublishedService 테스트"""

    def setUp(self):
        """테스트 데이터 및 모의 객체 설정"""
        self.mock_repository = Mock()
        self.mock_repository.save = AsyncMock()
        self.mock_repository.find_by_id = AsyncMock()
        self.mock_repository.find_by_article_id = AsyncMock()
        self.mock_repository.update = AsyncMock()
        self.mock_repository.delete = AsyncMock()
        self.mock_repository.exists = AsyncMock()
        self.mock_repository.find_all = AsyncMock()
        self.mock_repository.find_by_platform = AsyncMock()
        self.mock_repository.find_by_status = AsyncMock()
        self.mock_repository.count_by_platform = AsyncMock()
        self.mock_repository.count_by_status = AsyncMock()

        self.service = PublishedService(self.mock_repository)

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

    def test_publish_article(self):
        """기사 발행 기록 테스트"""
        # 모의 객체 설정
        self.mock_repository.exists.return_value = False
        self.mock_repository.save.return_value = self.published_article

        # 테스트 데이터
        create_data = PublishedArticleCreate(
            article_id=self.article_id,
            platform=self.platform,
            channel_id=self.channel_id,
            metadata=self.metadata,
        )

        # 테스트 실행
        result = asyncio.run(self.service.publish_article(create_data))

        # 검증
        self.mock_repository.exists.assert_called_once_with(
            self.article_id, self.platform
        )
        self.mock_repository.save.assert_called_once()
        self.assertEqual(result, self.published_article)

    def test_publish_article_already_exists(self):
        """이미 발행된 기사 발행 시도 시 예외 발생 테스트"""
        # 모의 객체 설정
        self.mock_repository.exists.return_value = True

        # 테스트 데이터
        create_data = PublishedArticleCreate(
            article_id=self.article_id, platform=self.platform
        )

        # 테스트 실행 및 검증
        with self.assertRaises(BusinessRuleViolationException):
            asyncio.run(self.service.publish_article(create_data))

    def test_get_published_article(self):
        """발행 항목 조회 테스트"""
        # 모의 객체 설정
        self.mock_repository.find_by_id.return_value = self.published_article

        # 테스트 실행
        result = asyncio.run(self.service.get_published_article("test-id"))

        # 검증
        self.mock_repository.find_by_id.assert_called_once_with("test-id")
        self.assertEqual(result, self.published_article)

    def test_get_published_article_not_found(self):
        """존재하지 않는 발행 항목 조회 시 예외 발생 테스트"""
        # 모의 객체 설정
        self.mock_repository.find_by_id.return_value = None

        # 테스트 실행 및 검증
        with self.assertRaises(EntityNotFoundException):
            asyncio.run(self.service.get_published_article("non-existent-id"))

    def test_get_published_by_article_id(self):
        """기사 ID로 발행 항목 조회 테스트"""
        # 모의 객체 설정
        self.mock_repository.find_by_article_id.return_value = [self.published_article]

        # 테스트 실행
        result = asyncio.run(self.service.get_published_by_article_id(self.article_id))

        # 검증
        self.mock_repository.find_by_article_id.assert_called_once_with(self.article_id)
        self.assertEqual(result, [self.published_article])

    def test_update_published_article(self):
        """발행 항목 업데이트 테스트"""
        # 업데이트된 객체
        updated_article = PublishedArticle(
            id="test-id",
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.ARCHIVED,
            channel_id="new-channel-id",
            metadata={"key": "new-value"},
        )

        # 모의 객체 설정
        self.mock_repository.update.return_value = updated_article

        # 테스트 데이터
        update_data = PublishedArticleUpdate(
            status=PublishedStatus.ARCHIVED,
            channel_id="new-channel-id",
            metadata={"key": "new-value"},
        )

        # 테스트 실행
        result = asyncio.run(
            self.service.update_published_article("test-id", update_data)
        )

        # 검증
        self.mock_repository.update.assert_called_once()
        self.assertEqual(result, updated_article)

    def test_update_published_article_not_found(self):
        """존재하지 않는 발행 항목 업데이트 시 예외 발생 테스트"""
        # 모의 객체 설정
        self.mock_repository.update.return_value = None

        # 테스트 데이터
        update_data = PublishedArticleUpdate(status=PublishedStatus.ARCHIVED)

        # 테스트 실행 및 검증
        with self.assertRaises(EntityNotFoundException):
            asyncio.run(
                self.service.update_published_article("non-existent-id", update_data)
            )

    def test_archive_published_article(self):
        """발행 항목 보관 테스트"""
        # 모의 객체 설정
        self.mock_repository.find_by_id.return_value = self.published_article
        self.mock_repository.save.return_value = PublishedArticle(
            id="test-id",
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.ARCHIVED,
            archived_at=datetime.now(),
        )

        # 테스트 실행
        result = asyncio.run(self.service.archive_published_article("test-id"))

        # 검증
        self.mock_repository.find_by_id.assert_called_once_with("test-id")
        self.mock_repository.save.assert_called_once()
        self.assertEqual(result.status, PublishedStatus.ARCHIVED)

    def test_delete_published_article(self):
        """발행 항목 삭제 상태 변경 테스트"""
        # 모의 객체 설정
        self.mock_repository.find_by_id.return_value = self.published_article
        self.mock_repository.save.return_value = PublishedArticle(
            id="test-id",
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.DELETED,
            deleted_at=datetime.now(),
        )

        # 테스트 실행
        result = asyncio.run(self.service.delete_published_article("test-id"))

        # 검증
        self.mock_repository.find_by_id.assert_called_once_with("test-id")
        self.mock_repository.save.assert_called_once()
        self.assertEqual(result.status, PublishedStatus.DELETED)

    def test_restore_published_article(self):
        """발행 항목 복원 테스트"""
        # 모의 객체 설정
        archived_article = PublishedArticle(
            id="test-id",
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.ARCHIVED,
            archived_at=datetime.now(),
        )

        self.mock_repository.find_by_id.return_value = archived_article
        self.mock_repository.save.return_value = PublishedArticle(
            id="test-id",
            article_id=self.article_id,
            platform=self.platform,
            status=PublishedStatus.PUBLISHED,
        )

        # 테스트 실행
        result = asyncio.run(self.service.restore_published_article("test-id"))

        # 검증
        self.mock_repository.find_by_id.assert_called_once_with("test-id")
        self.mock_repository.save.assert_called_once()
        self.assertEqual(result.status, PublishedStatus.PUBLISHED)

    def test_remove_published_article(self):
        """발행 항목 영구 삭제 테스트"""
        # 모의 객체 설정
        self.mock_repository.find_by_id.return_value = self.published_article
        self.mock_repository.delete.return_value = True

        # 테스트 실행
        result = asyncio.run(self.service.remove_published_article("test-id"))

        # 검증
        self.mock_repository.find_by_id.assert_called_once_with("test-id")
        self.mock_repository.delete.assert_called_once_with("test-id")
        self.assertTrue(result)

    def test_remove_published_article_not_found(self):
        """존재하지 않는 발행 항목 영구 삭제 시 예외 발생 테스트"""
        # 모의 객체 설정
        self.mock_repository.find_by_id.return_value = None

        # 테스트 실행 및 검증
        with self.assertRaises(EntityNotFoundException):
            asyncio.run(self.service.remove_published_article("non-existent-id"))

    def test_list_published_articles(self):
        """발행 항목 목록 조회 테스트"""
        # 모의 객체 설정
        self.mock_repository.find_all.return_value = [self.published_article]
        self.mock_repository.find_by_platform.return_value = [self.published_article]
        self.mock_repository.find_by_status.return_value = [self.published_article]
        self.mock_repository.count_by_platform.return_value = 1
        self.mock_repository.count_by_status.return_value = 1

        # 테스트 실행 - 필터 없음
        result1 = asyncio.run(self.service.list_published_articles())

        # 테스트 실행 - 플랫폼 필터
        result2 = asyncio.run(self.service.list_published_articles(platform="discord"))

        # 테스트 실행 - 상태 필터
        result3 = asyncio.run(
            self.service.list_published_articles(status=PublishedStatus.PUBLISHED)
        )

        # 검증
        self.mock_repository.find_all.assert_called_once()
        self.mock_repository.find_by_platform.assert_called_once_with("discord", 0, 10)
        self.mock_repository.find_by_status.assert_called_once_with(
            PublishedStatus.PUBLISHED, 0, 10
        )

        self.assertEqual(len(result1.items), 1)
        self.assertEqual(len(result2.items), 1)
        self.assertEqual(len(result3.items), 1)

    def test_is_article_published(self):
        """기사 발행 여부 확인 테스트"""
        # 모의 객체 설정
        self.mock_repository.exists.return_value = True

        # 테스트 실행
        result = asyncio.run(
            self.service.is_article_published(self.article_id, self.platform)
        )

        # 검증
        self.mock_repository.exists.assert_called_once_with(
            self.article_id, self.platform
        )
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
