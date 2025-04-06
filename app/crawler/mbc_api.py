from typing import Any
import aiohttp
import json
from datetime import date
from app.crawler.base import BaseNewsCrawler, Article
from app.crawler.utils.json_cleaner import sanitize_js_style_json
from common.utils.logger import get_logger

logger = get_logger(__name__)


class MbcNewsApiCrawler(BaseNewsCrawler):
    async def fetch_articles(self) -> list[Article]:
        logger.info("[MBC API] fetch_articles 시작")
        current_id, data_id = await self._get_today_ids()
        return await self._fetch_news(current_id, data_id)

    async def _get_today_ids(self) -> tuple[str, str]:
        cal_url = "https://imnews.imbc.com/news/2025/politics/cal_data.js"
        logger.info(f"[MBC API] cal_data.js 요청: {cal_url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(cal_url) as response:
                raw = await response.text()

        try:
            cleaned = sanitize_js_style_json(raw)
            cal_data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"[MBC API] cal_data.js JSON 파싱 실패: {e}")
            raise ValueError(
                f"cal_data.js 파싱 실패: {e}\n"
                "서버 응답은 JSON이 아니라 JavaScript일 수 있으며, "
                "Content-Type: application/javascript 이기 때문에 "
                "response.json()이 아닌 수동 파싱이 필요합니다."
            )

        today = date.today().strftime("%Y%m%d")
        for item in cal_data.get("DateList", []):
            if item["Day"] == today:
                logger.info(f"[MBC API] 오늘 날짜({today})에 해당하는 ID 찾음: {item['CurrentID']}, {cal_data['DataId']}")
                return item["CurrentID"], cal_data["DataId"]

        logger.warning(f"[MBC API] 오늘 날짜({today})에 해당하는 정보 없음")
        raise ValueError(f"{today}에 해당하는 날짜 정보가 없습니다 (cal_data.js 내)")

    async def _fetch_news(self, current_id: str, data_id: str) -> list[Article]:
        filename = f"{current_id}_{data_id}.js"
        url = f"https://imnews.imbc.com/news/2025/politics/{filename}"
        logger.info(f"[MBC API] 뉴스 데이터 요청 URL: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                raw = await response.text()

        cleaned = sanitize_js_style_json(raw)

        try:
            json_data: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"[MBC API] 뉴스 JSON 파싱 실패: {e}")
            raise ValueError(f".js 파일 JSON 파싱 실패: {e}")

        articles = []
        for group in json_data.get("Data", []):
            for item in group.get("List", []):
                title = item.get("Title")
                link = item.get("Link")
                articles.append({"title": title, "link": link})

        logger.info(f"[MBC API] 뉴스 {len(articles)}건 수집 완료")
        return articles
