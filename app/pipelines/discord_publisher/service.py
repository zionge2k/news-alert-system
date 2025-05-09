"""
Discord 발행 서비스 모듈

이 모듈은 MongoDB 큐에서 뉴스 기사를 가져와 Discord에 발행하는 서비스를 제공합니다.
발행 주기, 재시도 로직 및 오류 처리를 포함한 전체 파이프라인을 관리합니다.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.models.queue import QueueItem, QueueStatus
from app.pipelines.discord_publisher.client import DiscordClient, get_discord_client
from app.pipelines.discord_publisher.config import discord_settings
from app.pipelines.discord_publisher.formatters import ArticleFormatter
from app.storage.published.services import published_article_service
from app.storage.queue.mongodb_queue import mongodb_queue
from app.storage.queue.services import QueueService
from common.utils.logger import get_logger

# 직접 서비스 계층 임포트
from services.notifier import NotifierFactory

logger = get_logger(__name__)


class DiscordPublisherService:
    """
    Discord 발행 서비스

    MongoDB 큐에서 기사를 가져와 Discord에 발행하는 서비스입니다.
    주기적으로 큐를 확인하고 처리할 기사를 Discord로 전송합니다.
    """

    def __init__(self, queue_service: QueueService = None, settings=discord_settings):
        """
        Discord 발행 서비스 초기화

        Args:
            queue_service: 큐 서비스 인스턴스
            settings: Discord 설정
        """
        self.queue_service = queue_service or QueueService()
        self.settings = settings
        self.formatter = ArticleFormatter()
        self.client = None
        self.running = False
        self.publish_task = None

        # 서비스 어댑터 대신 직접 Discord 알림 서비스 생성
        if self.settings.WEBHOOK_URL:
            self.discord_notifier = NotifierFactory.create(
                "discord", webhook_url=self.settings.WEBHOOK_URL
            )
        else:
            self.discord_notifier = None
            logger.warning(
                "Discord webhook URL이 설정되지 않아 webhook 알림 기능이 비활성화됩니다."
            )

    async def initialize(self):
        """
        서비스를 초기화합니다.

        이 메서드는 Discord 클라이언트를 초기화하고 필요한 설정을 로드합니다.
        """
        try:
            # Discord 클라이언트 초기화
            self.client = await get_discord_client()
            logger.info("Discord 발행 서비스가 초기화되었습니다.")
            return True
        except Exception as e:
            logger.error(f"Discord 발행 서비스 초기화 중 오류 발생: {str(e)}")
            return False

    async def start(self):
        """
        발행 서비스를 시작합니다.

        주기적으로 큐에서 기사를 가져와 Discord로 발행하는 태스크를 시작합니다.
        """
        if self.running:
            logger.warning("이미 실행 중인 발행 서비스입니다.")
            return

        # 초기화 확인
        if not self.client:
            success = await self.initialize()
            if not success:
                logger.error("초기화 실패로 발행 서비스를 시작할 수 없습니다.")
                return

        self.running = True
        self.publish_task = asyncio.create_task(self._publish_loop())
        logger.info("Discord 발행 서비스가 시작되었습니다.")

    async def stop(self):
        """
        발행 서비스를 중지합니다.

        진행 중인 태스크를 정상적으로 종료합니다.
        """
        if not self.running:
            return

        self.running = False

        # 태스크가 실행 중이면 취소
        if self.publish_task and not self.publish_task.done():
            self.publish_task.cancel()
            try:
                await self.publish_task
            except asyncio.CancelledError:
                pass

        logger.info("Discord 발행 서비스가 중지되었습니다.")

    async def _publish_loop(self):
        """
        주기적으로 큐에서 기사를 가져와 발행하는 비동기 루프
        """
        while self.running:
            try:
                # 기사 발행 처리
                await self._process_articles()

                # 다음 실행까지 대기
                await asyncio.sleep(self.settings.PUBLISH_INTERVAL)

            except asyncio.CancelledError:
                # 태스크 취소 시 종료
                logger.info("발행 루프가 취소되었습니다.")
                break

            except Exception as e:
                # 예상치 못한 오류 처리
                logger.error(f"발행 루프 실행 중 오류 발생: {str(e)}")

                # 오류 발생 시 짧은 시간 대기 후 다시 시도
                await asyncio.sleep(5)

    async def _process_articles(self):
        """
        큐에서 기사를 가져와 Discord에 발행하는 메인 로직
        """
        try:
            # 처리할 기사 가져오기
            articles = await self.queue_service.get_pending_articles(
                limit=self.settings.BATCH_SIZE
            )

            if not articles:
                logger.debug("처리할 기사가 없습니다.")
                return

            logger.info(f"{len(articles)}개 기사 처리 시작")

            # 각 기사 발행
            for article in articles:
                await self._publish_article(article)

            logger.info(f"{len(articles)}개 기사 처리 완료")

        except Exception as e:
            logger.error(f"기사 처리 중 오류 발생: {str(e)}")

            # 오류 임베드 생성 및 전송
            error_embed = ArticleFormatter.create_error_embed(
                f"기사 처리 중 오류 발생: {str(e)}"
            )
            await self.client.send_error_message(error_embed)

    async def _publish_article(self, article: QueueItem):
        """
        단일 기사를 Discord에 발행합니다.

        Args:
            article: 발행할 QueueItem
        """
        try:
            # 카테고리에 맞는 채널 ID 가져오기
            channel_id = self.settings.get_channel_for_category(article.category)

            # 임베드 생성
            embed = ArticleFormatter.create_article_embed(article)

            # Discord에 메시지 전송
            message = await self.client.send_message(channel_id=channel_id, embed=embed)

            if message:
                # 성공 시 완료 상태로 변경
                success = await self.queue_service.mark_article_published(
                    article.unique_id
                )

                # 발행 이력 기록
                await published_article_service.mark_as_published(
                    unique_id=article.unique_id,
                    platform="discord",
                    channel_id=channel_id,
                )

                logger.info(f"기사 발행 성공: {article.title}")
            else:
                # 메시지 전송 실패 시 실패 상태로 변경
                success = await self.queue_service.mark_article_failed(
                    article.unique_id, "Discord 메시지 전송 실패"
                )
                logger.error(f"기사 발행 실패: {article.title}")

        except Exception as e:
            # 예외 발생 시 실패 상태로 변경
            error_message = f"기사 발행 중 오류 발생: {str(e)}"
            await self.queue_service.mark_article_failed(
                article.unique_id, error_message
            )
            logger.error(f"{error_message}: {article.title}")

    async def publish_via_webhook(self, article: QueueItem) -> bool:
        """
        Discord webhook을 통해 기사를 발행합니다.
        직접 Discord 알림 서비스를 사용합니다.

        Args:
            article: 발행할 QueueItem

        Returns:
            bool: 발행 성공 여부
        """
        # Discord 알림 서비스 확인
        if not self.discord_notifier:
            logger.error("Discord 알림 서비스가 설정되지 않았습니다.")
            return False

        try:
            # QueueItem을 알림 서비스가 기대하는 형식으로 변환
            news_data = {
                "title": article.title,
                "content": article.content,
                "source": article.source,
                "url": article.url,
                "published_at": (
                    article.published_at.isoformat() if article.published_at else None
                ),
                "category": article.category,
            }

            # 알림 서비스를 통해 알림 전송
            message = self.discord_notifier.format_message(news_data)
            success = await self.discord_notifier.send(message)

            if success:
                # 성공 시 완료 상태로 변경
                await self.queue_service.mark_article_published(article.unique_id)

                # 발행 이력 기록
                await published_article_service.mark_as_published(
                    unique_id=article.unique_id,
                    platform="discord",
                    channel_id="webhook",  # webhook을 통한 발행은 채널 ID 대신 "webhook" 표시
                )

                logger.info(f"webhook을 통한 기사 발행 성공: {article.title}")
                return True
            else:
                # 실패 시 실패 상태로 변경
                await self.queue_service.mark_article_failed(
                    article.unique_id, "Discord webhook 메시지 전송 실패"
                )
                logger.error(f"webhook을 통한 기사 발행 실패: {article.title}")
                return False

        except Exception as e:
            # 예외 발생 시 실패 상태로 변경
            error_message = f"webhook을 통한 기사 발행 중 오류 발생: {str(e)}"
            await self.queue_service.mark_article_failed(
                article.unique_id, error_message
            )
            logger.error(f"{error_message}: {article.title}")
            return False

    async def retry_failed_articles(self):
        """
        실패한 기사를 재시도합니다.

        일정 시간이 지난 후 실패한 기사를 다시 발행 시도합니다.
        """
        try:
            # 실패한 기사 가져오기
            failed_articles = await self.queue_service.get_failed_articles(
                max_retries=self.settings.MAX_RETRIES,
                min_age_seconds=self.settings.RETRY_INTERVAL,
            )

            if not failed_articles:
                logger.debug("재시도할 실패한 기사가 없습니다.")
                return

            logger.info(f"{len(failed_articles)}개 실패한 기사 재시도 시작")

            # 각 기사 재시도
            for article in failed_articles:
                # 재시도 카운트 증가
                await self.queue_service.increment_retry_count(article.unique_id)

                # 발행 시도
                await self._publish_article(article)

            logger.info(f"{len(failed_articles)}개 실패한 기사 재시도 완료")

        except Exception as e:
            logger.error(f"실패한 기사 재시도 중 오류 발생: {str(e)}")

    async def publish_single_article(self, article_id: str) -> bool:
        """
        특정 ID의 기사를 Discord에 발행합니다.

        Args:
            article_id: 발행할 기사의 고유 ID

        Returns:
            bool: 발행 성공 여부
        """
        try:
            # 기사 가져오기
            article = await self.queue_service.get_article_by_id(article_id)

            if not article:
                logger.error(f"기사를 찾을 수 없음: {article_id}")
                return False

            # 발행 시도
            await self._publish_article(article)

            # 발행 후 상태 확인
            updated_article = await self.queue_service.get_article_by_id(article_id)
            if updated_article and updated_article.status == QueueStatus.PUBLISHED:
                logger.info(f"단일 기사 발행 성공: {article_id}")
                return True
            else:
                logger.error(f"단일 기사 발행 실패: {article_id}")
                return False

        except Exception as e:
            logger.error(f"단일 기사 발행 중 오류 발생: {str(e)}")
            return False

    async def get_queue_status(self) -> dict:
        """
        큐 상태를 가져옵니다.

        Returns:
            dict: 상태별 기사 수 정보
        """
        try:
            return await self.queue_service.get_queue_status()
        except Exception as e:
            logger.error(f"큐 상태 조회 중 오류 발생: {str(e)}")
            return {}


# 전역 서비스 인스턴스 생성
discord_publisher_service = DiscordPublisherService()


async def start_discord_publisher():
    """
    Discord 발행 서비스를 시작합니다.

    이 함수는 메인 애플리케이션에서 호출되어 서비스를 초기화하고 시작합니다.
    """
    try:
        # 서비스 인스턴스 생성
        publisher = DiscordPublisherService()

        # 서비스 초기화
        success = await publisher.initialize()
        if not success:
            logger.error("Discord 발행 서비스 초기화 실패")
            return None

        # 서비스 시작
        await publisher.start()
        logger.info("Discord 발행 서비스가 시작되었습니다.")

        return publisher

    except Exception as e:
        logger.error(f"Discord 발행 서비스 시작 중 오류 발생: {str(e)}")
        return None
