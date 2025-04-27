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
from common.utils.logger import get_logger
from storage.published.services import published_article_service
from storage.queue.mongodb_queue import mongodb_queue
from storage.queue.services import QueueService

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
            logger.error(error_message)

            try:
                await self.queue_service.mark_article_failed(
                    article.unique_id, error_message
                )

                # 오류 로깅
                error_embed = ArticleFormatter.create_error_embed(
                    error_message, article
                )
                await self.client.send_error_message(error_embed)

            except Exception as inner_e:
                logger.error(f"오류 처리 중 추가 예외 발생: {str(inner_e)}")

    async def retry_failed_articles(self):
        """
        실패한 기사를 재시도합니다.
        """
        try:
            count = await self.queue_service.retry_failed_articles(
                max_retries=self.settings.MAX_RETRIES
            )

            if count > 0:
                logger.info(f"{count}개 실패 기사가 재시도 큐에 추가되었습니다.")

            return count

        except Exception as e:
            logger.error(f"실패 기사 재시도 중 오류 발생: {str(e)}")
            return 0

    async def publish_single_article(self, article_id: str) -> bool:
        """
        특정 기사 ID를 즉시 발행합니다.

        Args:
            article_id: 발행할 기사의 고유 ID

        Returns:
            bool: 발행 성공 여부
        """
        try:
            # MongoDB에서 해당 기사 조회
            db = mongodb_queue.collection
            doc = await db.find_one({"unique_id": article_id})

            if not doc:
                logger.error(f"기사 ID {article_id}를 찾을 수 없습니다.")
                return False

            # QueueItem으로 변환
            article = QueueItem.from_document(doc)

            # 발행 처리
            await self._publish_article(article)
            return True

        except Exception as e:
            logger.error(f"단일 기사 발행 중 오류 발생: {str(e)}")
            return False

    async def get_queue_status(self) -> dict:
        """
        현재 큐 상태를 조회합니다.

        Returns:
            dict: 상태별 기사 수
        """
        try:
            return await self.queue_service.get_queue_status()
        except Exception as e:
            logger.error(f"큐 상태 조회 중 오류 발생: {str(e)}")
            return {}


# 싱글톤 인스턴스
discord_publisher_service = DiscordPublisherService()


async def start_discord_publisher():
    """
    Discord 발행 서비스를 시작하는 유틸리티 함수

    애플리케이션 시작 시 호출됩니다.
    """
    global discord_publisher_service

    try:
        # 서비스 초기화 및 시작
        await discord_publisher_service.initialize()
        await discord_publisher_service.start()

        logger.info("Discord 발행 서비스가 실행 중입니다.")
        return True

    except Exception as e:
        logger.error(f"Discord 발행 서비스 시작 중 오류 발생: {str(e)}")
        return False
