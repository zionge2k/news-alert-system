# app/crawler/ytn/ytn_api.py

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import fake_useragent

from app.crawler.base import Article, BaseNewsCrawler
from common.utils.logger import get_logger

logger = get_logger(__name__)


class YtnNewsApiCrawler(BaseNewsCrawler):
    """
    YTN 정치 뉴스 크롤러
    """

    API_URL = "https://www.ytn.co.kr/ajax/getMoreNews.php"
    USER_AGENT = fake_useragent.UserAgent()

    @staticmethod
    def random_user_agent() -> str:
        return YtnNewsApiCrawler.USER_AGENT.random

    async def fetch_articles(self) -> List[Article]:
        logger.info("[YTN] 정치 뉴스 API 요청 시작")

        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=10, ssl=False)

        articles: List[Article] = []

        # 오늘 날짜 가져오기
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"[YTN] 오늘 날짜: {today}")

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            tasks = []
            for i in range(1, 4):  # 1~3 페이지 요청
                tasks.append(self._fetch_news(session, i))

            results = await asyncio.gather(*tasks)

            for result in results:
                if result and "data" in result:
                    page_data = result["data"]
                    for item in page_data.get("data", []):
                        title = item.get("title")
                        join_key = item.get("join_key")
                        # 날짜 정보 추출 ('3' 키에 날짜가 저장되어 있음)
                        date_str = item.get("3", "")

                        # 오늘 날짜의 기사만 추가
                        if date_str == today:
                            if title and join_key:
                                link = f"https://www.ytn.co.kr/_ln/0101_{join_key}"
                                articles.append(
                                    {"title": title, "link": link, "date": date_str}
                                )
                        else:
                            logger.debug(
                                f"[YTN] 다른 날짜 기사 무시: {date_str} - {title}"
                            )

        logger.info(f"[YTN] 총 {len(articles)}개의 기사 수집 완료")
        return articles

    async def _fetch_news(
        self, session: aiohttp.ClientSession, page_number: int
    ) -> Optional[Dict[str, Any]]:
        formdata = aiohttp.FormData()
        formdata.add_field("mcd", "0101")
        formdata.add_field("page", str(page_number))

        headers = {
            "Referer": "https://www.ytn.co.kr/news/list.php?mcd=0101",
            "User-Agent": self.random_user_agent(),
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh;q=0.5",
        }

        try:
            async with session.post(
                self.API_URL, data=formdata, headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.text()
                    json_data = json.loads(data)
                    if json_data:
                        logger.info(f"[YTN] 페이지 {page_number} 데이터 수집 성공")
                        return {"page": page_number, "data": json_data}
                    else:
                        logger.warning(
                            f"[YTN] 페이지 {page_number}에 데이터가 없습니다"
                        )
                        return None
                else:
                    logger.error(
                        f"[YTN] 페이지 {page_number} 요청 실패 - 상태 코드: {response.status}"
                    )
                    return None
        except Exception as e:
            logger.error(f"[YTN] 페이지 {page_number} 처리 중 오류 발생: {str(e)}")
            return None
