# app/crawler/mbc_hybrid.py

from app.crawler.base import BaseNewsCrawler, Article
from app.crawler.mbc_api import MbcNewsApiCrawler
from app.crawler.mbc_html import MbcHtmlCrawler

class HybridMbcCrawler(BaseNewsCrawler):
    """
    MBC 뉴스 크롤러 (API 우선, 실패 시 HTML fallback)
    """

    def __init__(self):
        self.api_crawler = MbcNewsApiCrawler()
        self.html_crawler = MbcHtmlCrawler()

    async def fetch_articles(self, keyword: str) -> list[Article]:
        try:
            print("[Hybrid] Trying API crawler...")
            articles = await self.api_crawler.fetch_articles(keyword)
            if not articles:
                raise ValueError("API 결과 없음")
            return articles
        except Exception as e:
            print(f"[Hybrid] API 실패, HTML fallback: {e}")
            return await self.html_crawler.fetch_articles(keyword)
