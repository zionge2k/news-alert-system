import asyncio

from app.crawler.registry import CRAWLERS
from common.utils.logger import get_logger

logger = get_logger(__name__)


async def run_crawler(name, crawler):
    try:
        articles = await crawler.fetch_articles()
        if not articles:
            logger.info(f"{name}: 관련 뉴스 없음.")
        else:
            for article in articles:
                logger.info(f"{name}: {article['title']}\n  → {article['link']}")
    except Exception as e:
        logger.error(f"{name} 크롤링 실패: {e}")


async def run_all():
    logger.info("정치 섹션 뉴스 수집 시작")

    # 모든 크롤러를 동시에 실행
    tasks = [run_crawler(name, crawler) for name, crawler in CRAWLERS.items()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(run_all())
