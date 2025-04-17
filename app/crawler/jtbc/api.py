from datetime import datetime
from typing import Dict, List, Optional, TypedDict

import aiohttp

from app.crawler.base import BaseNewsCrawler
from app.schemas.article import ArticleDTO, ArticleMetadata
from common.utils.logger import get_logger

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


class JtbcArticle(TypedDict):
    """JTBC 기사 API 응답 데이터 구조"""

    articleIdx: str  # 기사 고유 ID
    articleTitle: str  # 기사 제목
    articleInnerTextContent: str  # 기사 내용
    publicationDate: str  # 발행일
    journalistName: str  # 기자 이름
    isVideoView: bool  # 비디오 여부
    vodInfo: dict  # 비디오 정보


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

                            # 메타데이터 및 컨텐츠 추출
                            url = f"https://news.jtbc.co.kr/article/{article_idx}"
                            content = self._extract_content(
                                item.get("articleInnerTextContent", "")
                            )
                            published_at = self._parse_date(item.get("publicationDate"))
                            author = item.get("journalistName")

                            # 비디오 정보 추출
                            has_video = item.get("isVideoView", False)
                            video_id = None
                            if vod_info := item.get("vodInfo"):
                                has_video = True
                                video_id = vod_info.get("videoIdx")

                            # 메타데이터 생성
                            metadata = JtbcArticleMetadata(
                                platform="JTBC",
                                category=category_name,
                                article_id=article_idx,
                                published_at=published_at,
                                collected_at=datetime.now(),
                                updated_at=datetime.now(),
                                has_video=has_video,
                                video_id=video_id,
                            )

                            # ArticleDTO 생성
                            article_dto = ArticleDTO[JtbcArticleMetadata](
                                title=title,
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

        # CATEGORY_MAP의 모든 카테고리에 대해 기사 수집
        for category_code in CATEGORY_MAP:
            category_articles = await self.fetch_articles_by_category(category_code)
            all_articles.extend(category_articles)

        logger.info(f"[JTBC] 전체 {len(all_articles)}개의 기사 수집 완료")
        return all_articles
