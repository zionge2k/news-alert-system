from datetime import datetime
from typing import Any, Dict, List, Optional, Self, TypedDict

import aiohttp
from pydantic import Field

from app.crawler.base import BaseNewsCrawler
from app.schemas.api_models import BaseApiModel
from app.schemas.article import ArticleDTO, ArticleMetadata
from common.utils.logger import get_logger

# 직접 서비스 계층 임포트
from services.crawler import default_registry as crawler_registry

logger = get_logger(__name__)


# JTBC 카테고리 코드 매핑
CATEGORY_MAP = {
    10: "정치",
    20: "경제",
    30: "사회",
    40: "국제",
    50: "문화",
    60: "연예",
    70: "스포츠",
    80: "날씨",
}


class JtbcArticle(BaseApiModel):
    """JTBC 기사 API 응답 데이터 구조"""

    article_idx: str = Field(..., alias="articleIdx", description="기사 고유 ID")
    article_title: str = Field(..., alias="articleTitle", description="기사 제목")
    article_inner_text_content: str = Field(
        "", alias="articleInnerTextContent", description="기사 내용"
    )
    publication_date: str = Field("", alias="publicationDate", description="발행일")
    journalist_name: str = Field("", alias="journalistName", description="기자 이름")
    is_video_view: bool = Field(False, alias="isVideoView", description="비디오 여부")
    vod_info: dict = Field(
        default_factory=dict, alias="vodInfo", description="비디오 정보"
    )

    _default_values = {
        "articleInnerTextContent": "",
        "publicationDate": "",
        "journalistName": "",
        "isVideoView": False,
        "vodInfo": {},
    }


class JtbcArticleMetadata(ArticleMetadata):
    """JTBC 뉴스 메타데이터 모델"""

    article_id: str  # 기사 고유 ID
    has_video: bool = False  # 비디오 포함 여부
    video_id: Optional[str] = None  # 비디오 ID


class JTBCNewsApiCrawler(BaseNewsCrawler):
    """
    JTBC 뉴스 API 크롤러
    """

    BASE_URL = "https://news-api.jtbc.co.kr/v1/get/contents/section/list/articles"

    def __init__(self):
        """
        JTBC 뉴스 크롤러 초기화
        """
        # 서비스 어댑터 관련 코드 제거
        pass

    # set_service_adapter 메서드 제거

    async def fetch_articles_by_category(
        self, category_code: int
    ) -> list[ArticleDTO[JtbcArticleMetadata]]:
        """
        특정 카테고리(섹션)의 뉴스 기사 수집

        Args:
            category_code: 카테고리 코드 (예: 10 - 정치)

        Returns:
            list[ArticleDTO[JtbcArticleMetadata]]: 수집된 기사 목록
        """
        # 카테고리명 조회
        category_name = CATEGORY_MAP.get(category_code, f"카테고리{category_code}")

        logger.info(
            f"[JTBC] '{category_name}({category_code})' 카테고리 기사 수집 시작"
        )

        articles: list[ArticleDTO[JtbcArticleMetadata]] = []

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "pageNo": 1,
                    "pageSize": 10,
                    "articleListType": "ARTICLE",
                    "sectionIdx": category_code,
                }

                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        logger.error(
                            f"[JTBC] '{category_name}' 카테고리 요청 실패 - 상태 코드: {response.status}"
                        )
                        return articles

                    data = await response.json()
                    news_list = data.get("data", {}).get("list", [])

                    for item in news_list:
                        try:
                            # 필수 필드 확인
                            title = item.get("articleTitle")
                            article_idx = item.get("articleIdx")

                            if not title or not article_idx:
                                continue

                            # Pydantic 모델 변환 (BaseApiModel에서 자동으로 None 값 처리)
                            article = JtbcArticle.model_validate(item)

                            # 메타데이터 및 컨텐츠 추출
                            url = (
                                f"https://news.jtbc.co.kr/article/{article.article_idx}"
                            )
                            content = self._extract_content(
                                article.article_inner_text_content
                            )
                            published_at = self._parse_date(article.publication_date)
                            author = article.journalist_name

                            # 비디오 정보 추출
                            has_video = article.is_video_view
                            video_id = None
                            if vod_info := article.vod_info:
                                has_video = True
                                video_id = vod_info.get("videoIdx")

                            # 메타데이터 생성
                            metadata = JtbcArticleMetadata(
                                platform="JTBC",
                                category=category_name,
                                article_id=article.article_idx,
                                published_at=published_at,
                                collected_at=datetime.now(),
                                updated_at=datetime.now(),
                                has_video=has_video,
                                video_id=video_id,
                            )

                            # ArticleDTO 생성
                            article_dto = ArticleDTO[JtbcArticleMetadata](
                                title=article.article_title,
                                url=url,
                                content=content,
                                author=author,
                                metadata=metadata,
                            )

                            articles.append(article_dto)

                        except Exception as e:
                            logger.warning(f"[JTBC] 기사 정보 처리 중 오류: {str(e)}")

        except Exception as e:
            logger.error(
                f"[JTBC] '{category_name}' 카테고리 뉴스 수집 중 오류 발생: {str(e)}"
            )

        logger.info(
            f"[JTBC] '{category_name}' 카테고리 총 {len(articles)}개의 기사 수집 완료"
        )
        return articles

    def _parse_date(self, date_str: str) -> datetime | None:
        """발행일 문자열을 datetime 객체로 파싱"""
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            logger.warning(f"[JTBC] 발행일 파싱 실패: {date_str}")
            return None

    def _extract_content(self, text: str, max_length: int = 200) -> str:
        """기사 내용에서 요약 추출"""
        if not text:
            return ""

        if len(text) <= max_length:
            return text

        return text[:max_length] + "..."

    async def fetch_articles(self) -> list[ArticleDTO[JtbcArticleMetadata]]:
        """
        JTBC 뉴스 기사 수집
        모든 카테고리의 기사를 수집합니다.

        Returns:
            list[ArticleDTO[JtbcArticleMetadata]]: 수집된 기사 목록
        """
        all_articles: list[ArticleDTO[JtbcArticleMetadata]] = []

        # 주요 카테고리만 수집 (정치, 경제, 사회)
        main_categories = [10, 20, 30]

        for category_code in main_categories:
            articles = await self.fetch_articles_by_category(category_code)
            all_articles.extend(articles)

        return all_articles

    async def fetch_via_direct_service(self) -> List[Dict[str, Any]]:
        """
        서비스 계층을 직접 사용하여 JTBC 뉴스 기사 수집

        Returns:
            List[Dict[str, Any]]: 수집된 기사 데이터 목록
        """
        try:
            # 서비스 계층에서 JTBC 크롤러 가져오기
            crawler = crawler_registry.get("JTBC")
            if not crawler:
                logger.error("JTBC 크롤러를 찾을 수 없습니다.")
                return []

            # 크롤러를 통해 뉴스 수집
            news = await crawler.crawl()

            if isinstance(news, list):
                return news
            elif isinstance(news, dict):
                return [news]
            else:
                return []

        except Exception as e:
            logger.error(f"JTBC 뉴스 크롤링 실패: {e}")
            return []

    async def convert_adapter_data_to_dto(
        self, adapter_data: Dict[str, Any]
    ) -> Optional[ArticleDTO[JtbcArticleMetadata]]:
        """
        서비스 계층에서 받은 데이터를 ArticleDTO로 변환

        Args:
            adapter_data: 서비스 계층에서 받은 데이터

        Returns:
            Optional[ArticleDTO]: 변환된 ArticleDTO 객체
        """
        try:
            # 필수 필드 확인
            title = adapter_data.get("title")
            article_id = adapter_data.get("id")

            if not title or not article_id:
                logger.warning("[JTBC] 변환 실패: 필수 필드 누락")
                return None

            # 메타데이터 생성
            metadata = JtbcArticleMetadata(
                platform="JTBC",
                category=adapter_data.get("category", "기타"),
                article_id=article_id,
                published_at=adapter_data.get("published_at") or datetime.now(),
                collected_at=datetime.now(),
                updated_at=datetime.now(),
                has_video=adapter_data.get("has_video", False),
                video_id=adapter_data.get("video_id"),
            )

            # ArticleDTO 생성
            return ArticleDTO[JtbcArticleMetadata](
                title=title,
                url=adapter_data.get(
                    "url", f"https://news.jtbc.co.kr/article/{article_id}"
                ),
                content=adapter_data.get("content", ""),
                author=adapter_data.get("author", ""),
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"[JTBC] DTO 변환 중 오류: {str(e)}")
            return None
