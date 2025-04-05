from typing import Any
import aiohttp
import json
from datetime import date
from app.crawler.base import BaseNewsCrawler, Article


class MbcNewsApiCrawler(BaseNewsCrawler):
    async def fetch_articles(self, keyword: str) -> list[Article]:
        current_id, data_id = await self._get_today_ids()
        return await self._fetch_news(current_id, data_id, keyword)

    async def _get_today_ids(self) -> tuple[str, str]:
        cal_url = "https://imnews.imbc.com/news/2025/politics/cal_data.js"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(cal_url) as response:
                # 해당 파일은 Content-Type이 application/javascript이므로
                # aiohttp의 response.json()을 사용할 수 없습니다.
                # 대신 텍스트로 받고 수동으로 json.loads() 처리해야 함
                raw = await response.text()

        try:
            # BOM(Byte Order Mark, '\ufeff') 제거 후 양쪽 공백 제거
            cleaned = raw.lstrip('\ufeff').strip()

            # JSON이 순수한 객체형이라면 바로 파싱 가능
            # 혹시 JS 변수 선언이 포함되었다면 정규식 추출도 고려해야 함
            cal_data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"cal_data.js 파싱 실패: {e}\n"
                "서버 응답은 JSON이 아니라 JavaScript일 수 있으며, "
                "Content-Type: application/javascript 이기 때문에 "
                "response.json()이 아닌 수동 파싱이 필요합니다."
            )

        # 오늘 날짜에 해당하는 CurrentID 추출
        today = date.today().strftime("%Y%m%d")
        for item in cal_data.get("DateList", []):
            if item["Day"] == today:
                return item["CurrentID"], cal_data["DataId"]

        raise ValueError(f"{today}에 해당하는 날짜 정보가 없습니다 (cal_data.js 내)")


    async def _fetch_news(self, current_id: str, data_id: str, keyword: str) -> list[Article]:
        filename = f"{current_id}_{data_id}.js"
        url = f"https://imnews.imbc.com/news/2025/politics/{filename}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                raw = await response.text()

        # BOM 제거 + 앞뒤 공백 제거
        cleaned = raw.lstrip('\ufeff').strip()

        try:
            # 순수 JSON 파싱
            json_data: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f".js 파일 JSON 파싱 실패: {e}")

        articles = []
        for group in json_data.get("Data", []):
            for item in group.get("List", []):
                title = item.get("Title")
                link = item.get("Link")
                if title and keyword in title:
                    articles.append({
                        "title": title,
                        "link": link
                    })
        return articles
