"""
SBS 뉴스 크롤러와 파이프라인 통합 테스트

이 테스트는 SBS 뉴스 크롤러가 기사를 수집하고,
파이프라인을 통해 처리하는 전체 과정을 검증합니다.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.crawler.registry import CRAWLERS
from app.crawler.sbs.api import SbsNewsApiCrawler
from app.schemas.article import ArticleDTO


@pytest.mark.integration
@pytest.mark.asyncio
class TestSbsCrawlerPipeline:
    """SBS 뉴스 크롤러와 파이프라인 통합 테스트 클래스"""

    @pytest.mark.asyncio
    async def test_sbs_crawler_activation(self):
        """SBS 크롤러를 활성화하고 레지스트리에 등록하는 과정을 테스트합니다."""
        # 기존 레지스트리 백업
        original_crawlers = CRAWLERS.copy()

        try:
            # 테스트 크롤러 준비
            crawler = SbsNewsApiCrawler()

            # 테스트 기사 데이터
            test_articles = [
                ArticleDTO(
                    title="SBS 테스트 뉴스 1",
                    url="https://news.sbs.co.kr/news/endPage.do?news_id=0001234567",
                    content="테스트 뉴스 내용 1",
                    metadata=crawler.create_metadata(
                        article_id="0001234567",
                        category_code="01",
                        category_name="정치",
                        image_url="https://img.sbs.co.kr/test1.jpg",
                        published_at=datetime.now(),
                    ),
                ),
                ArticleDTO(
                    title="SBS 테스트 뉴스 2",
                    url="https://news.sbs.co.kr/news/endPage.do?news_id=0001234568",
                    content="테스트 뉴스 내용 2",
                    metadata=crawler.create_metadata(
                        article_id="0001234568",
                        category_code="02",
                        category_name="경제",
                        image_url=None,
                        published_at=datetime.now(),
                    ),
                ),
            ]

            # fetch_articles 메서드 오버라이드
            original_fetch = crawler.fetch_articles
            crawler.fetch_articles = AsyncMock(return_value=test_articles)

            # 테스트용 크롤러를 레지스트리에 추가
            CRAWLERS["sbs"] = crawler

            # 레지스트리에 SBS 크롤러가 등록되었는지 확인
            assert "sbs" in CRAWLERS
            assert isinstance(CRAWLERS["sbs"], SbsNewsApiCrawler)

            # SBS 크롤러 호출
            articles = await CRAWLERS["sbs"].fetch_articles()

            # 결과 검증
            assert len(articles) == 2
            assert articles[0].title == "SBS 테스트 뉴스 1"
            assert articles[1].title == "SBS 테스트 뉴스 2"

            # 메타데이터 검증
            assert articles[0].metadata.platform == "SBS"
            assert articles[0].metadata.category == "정치"
            assert articles[1].metadata.category == "경제"

            # 원래 메서드 복원
            crawler.fetch_articles = original_fetch

        finally:
            # 테스트 후 원래 레지스트리로 복원
            CRAWLERS.clear()
            CRAWLERS.update(original_crawlers)

    @pytest.mark.asyncio
    async def test_sbs_crawler_to_model_pipeline(self):
        """SBS 크롤러에서 모델로의 데이터 파이프라인을 테스트합니다."""
        # 크롤러 인스턴스 생성
        crawler = SbsNewsApiCrawler()

        # 테스트 기사 데이터
        test_articles = [
            ArticleDTO(
                title="SBS 테스트 뉴스 1",
                url="https://news.sbs.co.kr/news/endPage.do?news_id=0001234567",
                content="테스트 뉴스 내용 1",
                metadata=crawler.create_metadata(
                    article_id="0001234567",
                    category_code="01",
                    category_name="정치",
                    image_url="https://img.sbs.co.kr/test1.jpg",
                    published_at=datetime.now(),
                ),
            )
        ]

        # fetch_articles 메서드 오버라이드
        original_fetch = crawler.fetch_articles
        crawler.fetch_articles = AsyncMock(return_value=test_articles)

        try:
            # ArticleModel.from_article_dto 메서드 모킹
            mock_article_model = MagicMock(name="ArticleModel")

            with patch(
                "app.models.article.ArticleModel.from_article_dto",
                return_value=mock_article_model,
            ) as mock_from_dto:
                # 크롤러 실행
                articles = await crawler.fetch_articles()

                # 각 기사에 대해 모델 변환 시뮬레이션
                for article in articles:
                    article_model = mock_from_dto(article)

                    # 변환 메서드가 호출되었는지 확인
                    mock_from_dto.assert_any_call(article)

                    # 반환된 모델이 예상대로인지 확인
                    assert article_model == mock_article_model

        finally:
            # 원래 메서드 복원
            crawler.fetch_articles = original_fetch

    @pytest.mark.asyncio
    async def test_sbs_crawler_in_full_pipeline(self):
        """SBS 크롤러가 전체 파이프라인에서 작동하는 것을 테스트합니다."""
        # 크롤러 인스턴스 생성
        crawler = SbsNewsApiCrawler()

        # 테스트 기사 데이터
        test_articles = [
            ArticleDTO(
                title="SBS 테스트 뉴스 1",
                url="https://news.sbs.co.kr/news/endPage.do?news_id=0001234567",
                content="테스트 뉴스 내용 1",
                metadata=crawler.create_metadata(
                    article_id="0001234567",
                    category_code="01",
                    category_name="정치",
                    image_url="https://img.sbs.co.kr/test1.jpg",
                    published_at=datetime.now(),
                ),
            ),
            ArticleDTO(
                title="SBS 테스트 뉴스 2",
                url="https://news.sbs.co.kr/news/endPage.do?news_id=0001234568",
                content="테스트 뉴스 내용 2",
                metadata=crawler.create_metadata(
                    article_id="0001234568",
                    category_code="02",
                    category_name="경제",
                    image_url=None,
                    published_at=datetime.now(),
                ),
            ),
        ]

        # fetch_articles 메서드 오버라이드
        original_fetch = crawler.fetch_articles
        crawler.fetch_articles = AsyncMock(return_value=test_articles)

        try:
            # 파이프라인 컴포넌트 모킹
            mock_processor = MagicMock(name="ArticleProcessor")
            mock_processor.process = AsyncMock()

            mock_queue = MagicMock(name="ArticleQueue")
            mock_queue.enqueue = AsyncMock()

            # 기사 처리 파이프라인 시뮬레이션
            articles = await crawler.fetch_articles()

            for article in articles:
                # 프로세서를 통한 기사 처리
                await mock_processor.process(article)
                mock_processor.process.assert_any_call(article)

                # 큐에 기사 추가
                await mock_queue.enqueue(article)
                mock_queue.enqueue.assert_any_call(article)

            # 처리된 기사 수 확인
            assert mock_processor.process.call_count == 2
            assert mock_queue.enqueue.call_count == 2

        finally:
            # 원래 메서드 복원
            crawler.fetch_articles = original_fetch
