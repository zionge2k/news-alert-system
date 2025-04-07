from app.crawler.base import Article, BaseNewsCrawler
from app.crawler.mbc.api import MbcNewsApiCrawler
from app.crawler.mbc.html import MbcHtmlCrawler
from common.utils.logger import get_logger

logger = get_logger(__name__)


class HybridMbcCrawler(BaseNewsCrawler):
    """
    MBC 뉴스 크롤러 (API 우선, 실패 시 HTML fallback)
    """

    def __init__(self):
        self.api_crawler = MbcNewsApiCrawler()
        self.html_crawler = MbcHtmlCrawler()

    async def fetch_articles(self) -> list[Article]:
        try:
            logger.info("[Hybrid] Trying API crawler...\n")
            return await self.api_crawler.fetch_articles()

        except Exception as e:
            logger.warning(f"[Hybrid] API 크롤링 실패. HTML fallback 시도 중... → {e}")

            try:
                articles = await self.html_crawler.fetch_articles()
                if not articles:
                    logger.warning("[Hybrid] HTML fallback에서도 기사 수집 실패")
                    return []
                return articles
            except Exception as e:
                logger.error(f"[Hybrid] HTML fallback 중 오류 발생: {e}")
                raise e
