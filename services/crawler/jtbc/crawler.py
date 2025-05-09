import logging
from typing import Any, Dict, Optional

import aiohttp
from bs4 import BeautifulSoup

from services.crawler.base import BaseCrawler

logger = logging.getLogger(__name__)


class JTBCCrawler(BaseCrawler):
    """
    JTBC 뉴스 크롤러
    JTBC 뉴스 사이트에서 뉴스를 수집
    """

    def __init__(self, base_url: str = "https://news.jtbc.co.kr"):
        """
        JTBC 크롤러 초기화

        Args:
            base_url (str): JTBC 뉴스 기본 URL
        """
        self.base_url = base_url

    async def fetch(self) -> str:
        """
        JTBC 뉴스 사이트에서 최신 뉴스 HTML을 가져옴

        Returns:
            str: 수집된 HTML 콘텐츠
        """
        url = f"{self.base_url}/section/index.aspx"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.text()
        except Exception as e:
            logger.error(f"JTBC 뉴스 가져오기 실패: {e}")
            raise

    def parse(self, html: str) -> Dict[str, Any]:
        """
        HTML에서 뉴스 정보를 추출

        Args:
            html (str): 파싱할 HTML 콘텐츠

        Returns:
            Dict[str, Any]: 추출된 뉴스 정보
        """
        soup = BeautifulSoup(html, "html.parser")

        # 첫 번째 뉴스 항목 선택 (실제 구현에서는 선택기 조정 필요)
        news_item = soup.select_one("div.news_article")
        if not news_item:
            logger.warning("JTBC 뉴스 항목을 찾을 수 없음")
            return {}

        title_element = news_item.select_one("h3.title")
        content_element = news_item.select_one("p.text")
        date_element = news_item.select_one("span.date")

        title = title_element.text.strip() if title_element else "제목 없음"
        content = content_element.text.strip() if content_element else "내용 없음"
        published_at = date_element.text.strip() if date_element else None

        return {
            "title": title,
            "content": content,
            "source": "JTBC",
            "published_at": published_at,
            "url": self._extract_article_url(news_item),
        }

    def _extract_article_url(self, news_item: BeautifulSoup) -> Optional[str]:
        """
        뉴스 항목에서 기사 URL 추출

        Args:
            news_item (BeautifulSoup): 뉴스 항목 요소

        Returns:
            Optional[str]: 기사 URL 또는 None
        """
        link = news_item.select_one("a")
        if link and link.has_attr("href"):
            url = link["href"]
            if url.startswith("/"):
                return f"{self.base_url}{url}"
            return url
        return None

    async def crawl(self) -> Dict[str, Any]:
        """
        뉴스를 크롤링하는 비동기 워크플로우

        Returns:
            Dict[str, Any]: 추출된 뉴스 정보
        """
        html = await self.fetch()
        return self.parse(html)
