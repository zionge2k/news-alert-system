"""
뉴스 기사 데이터베이스 저장 모듈

이 모듈은 크롤링된 뉴스 기사를 MongoDB에 저장하는 기능을 제공합니다.
중복 기사 감지 및 필터링을 수행하고, 신규 기사만 저장합니다.

주요 기능:
1. unique_id(platform + article_id) 또는 URL 기반 중복 감지
2. 신규 기사만 MongoDB에 저장
3. 저장 결과 요약 및 로깅

사용법:
    from scripts.save import save_to_database
    saved_count = await save_to_database(articles)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# MongoDB 연결 및 모델
from app.models.article import ArticleModel
from app.schemas.article import ArticleDTO

# 커스텀 로거
from common.utils.logger import get_logger
from infra.database.mongodb import MongoDB
from infra.database.repository.article import ArticleRepository

# 인프라 계층 저장소 임포트
from infra.database.repository.factory import create_article_repository

# 로거 가져오기
logger = get_logger(__name__)


async def save_to_database(
    articles: List[ArticleDTO], mongodb_instance: Optional[MongoDB] = None
) -> int:
    """
    크롤링한 기사를 MongoDB에 저장합니다.
    unique_id(platform + article_id) 기반으로 중복을 확인하여 이미 존재하는 기사는 건너뜁니다.

    Args:
        articles: 저장할 ArticleDTO 객체 목록
        mongodb_instance: MongoDB 인스턴스 (None이면 전역 인스턴스 사용)

    Returns:
        새로 저장된 기사 수
    """
    logger.info("데이터베이스 저장 작업을 시작합니다...")
    start_time = datetime.now()

    # 저장소 인스턴스 생성 - 전역 MongoDB 인스턴스 사용
    article_repository = create_article_repository(mongodb_instance)

    new_count: int = 0
    dup_count: int = 0
    error_count: int = 0

    for idx, article_dto in enumerate(articles, 1):
        try:
            # 진행 상황 출력 (100개마다)
            if idx % 100 == 0:
                logger.info(f"진행 중: {idx}/{len(articles)}개 처리 완료")

            # 플랫폼 정보 가져오기
            platform: str = article_dto.metadata.platform

            # article_id 추출 시도
            article_id: Optional[str] = getattr(
                article_dto.metadata, "article_id", None
            )

            # 문서 존재 여부 확인
            existing: Optional[Dict[str, Any]] = None

            if article_id:
                # article_id가 있는 경우 복합키로 중복 확인
                unique_id: str = f"{platform}_{article_id}"
                existing = await article_repository.find_by_unique_id(unique_id)
            else:
                # article_id가 없는 경우 URL로 검색
                existing = await article_repository.find_by_url(article_dto.url)

            if not existing:
                # DTO → Document 모델 변환
                article_model: ArticleModel = ArticleModel.from_article_dto(article_dto)

                # DB 저장
                await article_repository.save(article_model)
                new_count += 1
            else:
                dup_count += 1

        except Exception as e:
            error_count += 1
            logger.error(f"기사 저장 중 오류 발생: {str(e)}")

    # 실행 시간 계산
    elapsed = (datetime.now() - start_time).total_seconds()

    # 결과 요약
    logger.info("=" * 50)
    logger.info("DB 저장 결과 요약:")
    logger.info(f"- 총 처리 기사: {len(articles)}개")
    logger.info(f"- 신규 저장: {new_count}개")
    logger.info(f"- 중복 감지: {dup_count}개")
    logger.info(f"- 오류 발생: {error_count}개")
    logger.info(f"- 소요 시간: {elapsed:.2f}초")
    logger.info("=" * 50)

    return new_count
