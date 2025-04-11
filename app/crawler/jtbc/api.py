from datetime import datetime
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

        # 오늘 날짜 가져오기
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"[JTBC] 오늘 날짜: {today}")

        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=10, ssl=False)

        try:
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as session:
                params = {"pageNo": 1, "pageSize": 20, "articleListType": "ARTICLE"}

                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        news_list = data["data"]["list"]
                        for item in news_list:
                            # 오늘 날짜의 기사만 추가
                            pub_date = item.get("publicationDate", "").split("T")[0]
                            if pub_date == today:
                                title = item.get("articleTitle")
                                article_idx = item.get("articleIdx")
                                if title and article_idx:
                                    link = (
                                        f"https://news.jtbc.co.kr/article/{article_idx}"
                                    )
                                    articles.append({"title": title, "link": link})
                    else:
                        logger.error(f"[JTBC] 요청 실패 - 상태 코드: {response.status}")

        except Exception as e:
            logger.error(f"[JTBC] 뉴스 수집 중 오류 발생: {str(e)}")

        logger.info(f"[JTBC] 총 {len(articles)}개의 기사 수집 완료")
        return articles
