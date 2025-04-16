import json
from datetime import datetime
from typing import TypedDict

import aiohttp
from pydantic import BaseModel

from app.crawler.base import BaseNewsCrawler
from app.crawler.utils.headers import create_mbc_headers
from app.crawler.utils.json_cleaner import sanitize_js_style_json
from app.schemas.article import ArticleDTO, ArticleMetadata
from common.utils.logger import get_logger

logger = get_logger(__name__)


class HeadlineArticle(TypedDict):
    Section: str
    AId: str
    Title: str
    Desc: str
    Image: str
    Link: str
    IsVod: str


class MbcArticleMetadata(ArticleMetadata):
    """MBC 뉴스 메타데이터 모델"""

    article_id: str
    is_video: bool = False
    image_url: str | None = None


class MbcNewsApiCrawler(BaseNewsCrawler):
    """
    MBC 뉴스 API 크롤러 (헤드라인 API 사용)
    """

    HEADLINE_API_URL = (
        "https://imnews.imbc.com/operate/common/main/topnews/headline_news.js"
    )

    async def fetch_articles(self) -> list[ArticleDTO[MbcArticleMetadata]]:
        """
        MBC 헤드라인 뉴스를 가져옵니다.
        모든 섹션(정치, 경제, 사회, 세계 등)의 주요 뉴스를 수집합니다.
        """
        logger.info("[MBC API] 헤드라인 뉴스 수집 시작")

        # 타임스탬프 파라미터 추가 (YYYYMMDDHHMM 형식)
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        url = f"{self.HEADLINE_API_URL}?{timestamp}="

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=create_mbc_headers()) as response:
                    if response.status != 200:
                        logger.error(
                            f"[MBC API] 요청 실패 - 상태 코드: {response.status}"
                        )
                        return []

                    raw = await response.text()

            # JavaScript 스타일의 JSON 정리
            cleaned = sanitize_js_style_json(raw)
            json_data = json.loads(cleaned)

            articles: list[ArticleDTO[MbcArticleMetadata]] = []
            for item in json_data.get("Data", []):
                try:
                    article = HeadlineArticle(**item)

                    # 이미지 URL 정규화
                    image_url = None
                    if article["Image"]:
                        image_url = (
                            f"https:{article['Image']}"
                            if article["Image"].startswith("//")
                            else article["Image"]
                        )

                    # 메타데이터 생성
                    metadata = MbcArticleMetadata(
                        platform="MBC",
                        category=article["Section"],
                        article_id=article["AId"],
                        is_video=article["IsVod"] == "Y",
                        image_url=image_url,
                        collected_at=datetime.now(),
                    )

                    # ArticleDTO 생성
                    article_dto = ArticleDTO[MbcArticleMetadata](
                        title=article["Title"],
                        url=article["Link"],
                        content=article["Desc"],
                        metadata=metadata,
                    )

                    articles.append(article_dto)

                except Exception as e:
                    logger.warning(f"[MBC API] 기사 데이터 처리 중 오류: {str(e)}")
                    continue

            logger.info(f"[MBC API] 헤드라인 뉴스 {len(articles)}건 수집 완료")
            return articles

        except Exception as e:
            logger.error(f"[MBC API] 헤드라인 뉴스 수집 중 오류 발생: {str(e)}")
            return []
