# app/crawler/ytn/ytn_api.py

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Self, TypedDict

import aiohttp
from pydantic import Field

from app.crawler.base import BaseNewsCrawler
from app.crawler.utils.headers import create_ytn_headers
from app.crawler.utils.json_cleaner import sanitize_js_style_json
from app.schemas.api_models import BaseApiModel
from app.schemas.article import ArticleDTO, ArticleMetadata
from common.utils.logger import get_logger

logger = get_logger(__name__)


class YtnNewsArticle(BaseApiModel):
    """YTN 뉴스 API 응답 데이터 구조"""

    title: str = Field(..., description="기사 제목")
    mcd: str = Field(..., alias="mcd", description="카테고리 코드")
    join_key: str = Field(..., alias="join_key", description="기사 고유 ID")

    _default_values = {
        "title": "",
        "mcd": "",
        "join_key": "",
    }


class YtnArticleMetadata(ArticleMetadata):
    """YTN 뉴스 메타데이터 모델"""

    article_id: str  # 기사 고유 ID (join_key)
    category_code: str  # 카테고리 코드 (mcd)


# 카테고리 코드 매핑
CATEGORY_MAP = {
    "0101": "정치",
    "0102": "경제",
    "0103": "사회",
    "0104": "국제",
    "0105": "과학",
    "0106": "문화",
    "0107": "스포츠",
}


class YtnNewsApiCrawler(BaseNewsCrawler):
    """
    YTN 뉴스 API 크롤러
    """

    API_URL = "https://www.ytn.co.kr/ajax/getManyNews.php"

    async def fetch_articles(self) -> list[ArticleDTO[YtnArticleMetadata]]:
        """
        YTN 최신 뉴스를 가져옵니다.
        전체 카테고리(total)의 최신 뉴스를 수집합니다.
        """
        logger.info("[YTN API] 최신 뉴스 수집 시작")

        try:
            async with aiohttp.ClientSession() as session:
                # POST 요청 데이터 준비
                payload = {"mcd": "total"}

                # for_post=True로 설정하여 Content-Type 헤더가 포함된 헤더 생성
                headers = create_ytn_headers(for_post=True)

                async with session.post(
                    self.API_URL, data=payload, headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(
                            f"[YTN API] 요청 실패 - 상태 코드: {response.status}"
                        )
                        return []

                    text_response = await response.text()

                    try:
                        # JavaScript 스타일의 JSON 정리 후 파싱
                        cleaned_json = sanitize_js_style_json(text_response)
                        data = json.loads(cleaned_json)
                    except json.JSONDecodeError as e:
                        logger.error(f"[YTN API] JSON 파싱 실패: {str(e)}")
                        return []

            articles: list[ArticleDTO[YtnArticleMetadata]] = []

            for item in data:
                try:
                    # Pydantic 모델 변환 (BaseApiModel에서 자동으로 None 값 처리)
                    article = YtnNewsArticle.model_validate(item)

                    # 필수 필드 확인 (Pydantic이 기본값을 설정했더라도 원래 비어있었는지 확인)
                    if not article.title or not article.mcd or not article.join_key:
                        logger.warning("[YTN API] 필수 필드가 누락된 데이터 건너뜀")
                        continue

                    # 카테고리명 매핑
                    category = CATEGORY_MAP.get(article.mcd, "기타")

                    # URL 생성
                    url = f"https://www.ytn.co.kr/_ln/{article.mcd}_{article.join_key}"

                    # 메타데이터 생성
                    metadata = YtnArticleMetadata(
                        platform="YTN",
                        category=category,
                        article_id=article.join_key,
                        category_code=article.mcd,
                        collected_at=datetime.now(),
                    )

                    # ArticleDTO 생성
                    article_dto = ArticleDTO[YtnArticleMetadata](
                        title=article.title,
                        url=url,
                        content="",  # YTN API에서는 내용 요약을 제공하지 않음
                        metadata=metadata,
                    )

                    articles.append(article_dto)

                except Exception as e:
                    logger.warning(f"[YTN API] 기사 데이터 처리 중 오류: {str(e)}")
                    continue

            logger.info(f"[YTN API] 최신 뉴스 {len(articles)}건 수집 완료")
            return articles

        except Exception as e:
            logger.error(f"[YTN API] 최신 뉴스 수집 중 오류 발생: {str(e)}")
            return []
