import asyncio

from app.crawler.registry import CRAWLERS
from common.utils.logger import get_logger

logger = get_logger(__name__)


async def run_all():
    logger.info("정치 섹션 뉴스 수집 시작")

    for name, crawler in CRAWLERS.items():
        try:
            articles = await crawler.fetch_articles()
            if not articles:
                logger.info("관련 뉴스 없음.")
            else:
                for article in articles:
                    logger.info(f"{article['title']}\n  → {article['link']}")
        except Exception as e:
            logger.error(f" 크롤링 실패: {e}")


if __name__ == "__main__":
    asyncio.run(run_all())
