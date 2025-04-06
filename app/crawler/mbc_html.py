import aiohttp
from bs4 import BeautifulSoup
from app.crawler.base import BaseNewsCrawler, Article
from common.utils.logger import get_logger

logger = get_logger(__name__)

class MbcHtmlCrawler(BaseNewsCrawler):
    """
    MBC 정치 섹션을 크롤링하는 클래스.
    """

    BASE_URL = "https://imnews.imbc.com"
    TARGET_URL = f"{BASE_URL}/news/2025/politics/"

    async def fetch_articles(self) -> list[Article]:
        logger.info(f"[MBC HTML] 페이지 요청: {self.TARGET_URL}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.TARGET_URL) as response:
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        articles: list[Article] = []

        items = soup.select(".list_area li a")
        logger.info(f"[MBC HTML] 기사 후보 {len(items)}건 탐색 시작")

        for item in items:
            title_tag = item.select_one(".tit.ellipsis2")
            title = title_tag.get_text(strip=True) if title_tag else None
            href = item.get("href")

            if not title or not href:
                logger.warning(f"[MBC HTML] title 또는 href 누락된 항목 건너뜀")
                continue

            articles.append({"title": title, "link": href})

        logger.info(f"[MBC HTML] 최종 수집된 기사 수: {len(articles)}건")
        return articles
