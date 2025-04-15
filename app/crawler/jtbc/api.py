from typing import List

import aiohttp

from app.crawler.base import Article, BaseNewsCrawler
from common.utils.logger import get_logger

logger = get_logger(__name__)


class JTBCNewsApiCrawler(BaseNewsCrawler):
    """
    JTBC 뉴스 API 크롤러
    """

    BASE_URL = "https://news-api.jtbc.co.kr/v1/get/contents/section/list/articles"

    async def fetch_articles(self) -> List[Article]:
        logger.info("[JTBC] 뉴스 API 요청 시작")

        articles: List[Article] = []
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=10, ssl=False)

        try:
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as session:
                params = {"pageNo": 1, "pageSize": 20, "articleListType": "ARTICLE"}

                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        logger.error(f"[JTBC] 요청 실패 - 상태 코드: {response.status}")
                        return articles

                    data = await response.json()
                    news_list = data.get("data", {}).get("list", [])

                    for item in news_list:
                        try:
                            title = item.get("articleTitle")
                            article_idx = item.get("articleIdx")
                            if not title or not article_idx:
                                continue

                            link = f"https://news.jtbc.co.kr/article/{article_idx}"
                            articles.append({"title": title, "link": link})
                        except Exception as e:
                            logger.warning(f"[JTBC] 기사 정보 처리 중 오류: {str(e)}")

        except Exception as e:
            logger.error(f"[JTBC] 뉴스 수집 중 오류 발생: {str(e)}")

        logger.info(f"[JTBC] 총 {len(articles)}개의 기사 수집 완료")
        return articles
