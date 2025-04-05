import aiohttp
from bs4 import BeautifulSoup
from app.crawler.base import BaseNewsCrawler, Article

class MbcHtmlCrawler(BaseNewsCrawler):
    """
    MBC 정치 섹션을 크롤링하는 클래스.
    """

    BASE_URL = "https://imnews.imbc.com"
    TARGET_URL = f"{BASE_URL}/news/2025/politics/"

    async def fetch_articles(self, keyword: str) -> list[Article]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.TARGET_URL) as response:
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        articles: list[Article] = []

        for item in soup.select(".list_area li a"):
            title_tag = item.select_one(".tit.ellipsis2")
            title = title_tag.get_text(strip=True) if title_tag else None
            href = item.get("href")

            if not title or not href:
                continue

            if keyword in title:
                articles.append({"title": title, "link": href})

        return articles