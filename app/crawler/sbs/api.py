import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Self, TypedDict

import aiohttp
from pydantic import Field

from app.crawler.base import BaseNewsCrawler
from app.crawler.utils.headers import create_sbs_headers
from app.schemas.api_models import BaseApiModel
from app.schemas.article import ArticleDTO, ArticleMetadata
from common.utils.logger import get_logger

logger = get_logger(__name__)


class SbsArticleMetadata(ArticleMetadata):
    """SBS 뉴스 메타데이터 모델"""

    article_id: Optional[str] = None
    category_code: Optional[str] = None
    image_url: Optional[str] = None


class SbsNewsApiCrawler(BaseNewsCrawler):
    """
    SBS 뉴스 크롤러

    HTML 파싱 방식으로 뉴스 기사를 수집합니다.
    """

    # 뉴스 목록 페이지 URL
    BASE_URL = "https://news.sbs.co.kr"

    # 뉴스 검색 API URL (최신 뉴스를 얻기 위해 검색 API 사용)
    SEARCH_API_URL = "https://news.sbs.co.kr/news/search/search_json.do"

    # 카테고리 코드 매핑
    CATEGORY_NAMES = {
        "01": "정치",
        "02": "경제",
        "03": "사회",
        "07": "국제",
        "08": "문화/연예",
        "09": "스포츠",
    }

    def create_metadata(
        self,
        article_id: str,
        category_code: str,
        category_name: str,
        image_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ) -> SbsArticleMetadata:
        """
        SBS 뉴스 메타데이터 객체를 생성합니다.

        Args:
            article_id: 기사 ID
            category_code: 카테고리 코드
            category_name: 카테고리 이름
            image_url: 이미지 URL (없으면 None)
            published_at: 발행 시간 (없으면 현재 시간)

        Returns:
            SbsArticleMetadata: 생성된 메타데이터 객체
        """
        if published_at is None:
            published_at = datetime.now()

        return SbsArticleMetadata(
            platform="SBS",
            category=category_name,
            article_id=article_id,
            category_code=category_code,
            image_url=image_url,
            published_at=published_at,
            collected_at=datetime.now(),
        )

    async def fetch_articles(self) -> list[ArticleDTO[SbsArticleMetadata]]:
        """
        SBS 최신 뉴스를 가져옵니다.
        검색 API를 사용하여 최신 뉴스를 수집합니다.
        """
        logger.info("[SBS 크롤러] 최신 뉴스 수집 시작")

        all_articles: list[ArticleDTO[SbsArticleMetadata]] = []

        try:
            async with aiohttp.ClientSession() as session:
                # 각 카테고리별로 최신 뉴스 수집
                for cat_code, cat_name in self.CATEGORY_NAMES.items():
                    try:
                        logger.info(f"[SBS 크롤러] {cat_name} 카테고리 수집 시작")

                        # 검색 API 파라미터 설정
                        params = {
                            "keyword": "",  # 빈 키워드로 모든 뉴스 검색
                            "disp_cnt": "20",  # 20개 기사 요청
                            "sort": "date",  # 날짜순 정렬
                            "catid": cat_code,  # 카테고리 코드
                            "prddate_all": "y",  # 모든 날짜
                        }

                        async with session.get(
                            self.SEARCH_API_URL,
                            params=params,
                            headers=create_sbs_headers(),
                        ) as response:
                            if response.status != 200:
                                logger.error(
                                    f"[SBS 크롤러] {cat_name} 카테고리 요청 실패 - 상태 코드: {response.status}"
                                )
                                continue

                            # JSON 응답 파싱
                            try:
                                data = await response.json()
                            except Exception as e:
                                logger.error(f"[SBS 크롤러] JSON 파싱 실패: {str(e)}")
                                continue

                            # 검색 결과에서 기사 추출
                            category_articles = self._process_search_results(
                                data, cat_code, cat_name
                            )
                            all_articles.extend(category_articles)
                            logger.info(
                                f"[SBS 크롤러] {cat_name} 카테고리 {len(category_articles)}건 수집"
                            )

                    except Exception as e:
                        logger.error(
                            f"[SBS 크롤러] {cat_name} 카테고리 수집 중 오류: {str(e)}"
                        )
                        continue

            logger.info(f"[SBS 크롤러] 총 {len(all_articles)}건 수집 완료")
            return all_articles

        except Exception as e:
            logger.error(f"[SBS 크롤러] 뉴스 수집 중 오류 발생: {str(e)}")
            return []

    def _process_search_results(
        self, data: Dict[str, Any], category_code: str, category_name: str
    ) -> List[ArticleDTO[SbsArticleMetadata]]:
        """검색 API 결과에서 뉴스 기사 정보를 추출합니다."""
        articles: List[ArticleDTO[SbsArticleMetadata]] = []

        # 검색 결과 목록 추출
        news_list = data.get("SEARCH_RESULT", {}).get("NEWS_LIST", [])

        for item in news_list:
            try:
                # 필수 필드 추출
                news_id = item.get("NEWS_ID", "")
                title = item.get("NEWS_TITLE", "")

                if not news_id or not title:
                    logger.warning("[SBS 크롤러] 필수 필드가 누락된 데이터 건너뜀")
                    continue

                # URL 생성
                url = f"{self.BASE_URL}/news/endPage.do?news_id={news_id}"

                # 요약 추출
                summary = item.get("NEWS_SUMMARY", "")

                # 이미지 URL 추출
                image_url = item.get("THUMB", "")
                if image_url and image_url.startswith("//"):
                    image_url = f"https:{image_url}"

                # 발행 시간 파싱
                published_at = datetime.now()
                date_str = item.get("NEWS_DATE", "")
                if date_str:
                    try:
                        published_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            published_at = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                        except ValueError:
                            pass

                # 메타데이터 생성
                metadata = self.create_metadata(
                    article_id=news_id,
                    category_code=category_code,
                    category_name=category_name,
                    image_url=image_url if image_url else None,
                    published_at=published_at,
                )

                # ArticleDTO 생성
                article_dto = ArticleDTO[SbsArticleMetadata](
                    title=title,
                    url=url,
                    content=summary,
                    metadata=metadata,
                )

                articles.append(article_dto)

            except Exception as e:
                logger.warning(f"[SBS 크롤러] 기사 데이터 처리 중 오류: {str(e)}")
                continue

        return articles
