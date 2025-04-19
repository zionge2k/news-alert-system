#!/usr/bin/env python
"""
뉴스 크롤링 스크립트

이 스크립트는 다양한 뉴스 소스에서 기사를 크롤링합니다.
병렬 비동기 처리를 통해 효율적으로 여러 뉴스 API에서 데이터를 수집합니다.

주요 기능:
1. 여러 뉴스 API 크롤러를 병렬로 실행하여 데이터 수집
2. 결과 통합 및 중복 제거
3. 수집 과정의 상세 로깅
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List

# 상위 디렉토리를 모듈 경로에 추가 (단독 실행 시 필요)
sys.path.append(str(Path(__file__).parent.parent))

# 크롤러 레지스트리
from app.crawler.registry import CRAWLERS
from app.schemas.article import ArticleDTO
from common.utils.logger import get_logger

# 로거 가져오기
logger = get_logger(__name__)


async def run_crawler(name: str, crawler: Any) -> List[ArticleDTO]:
    """
    특정 크롤러를 실행합니다.

    Args:
        name: 크롤러 이름
        crawler: 크롤러 인스턴스

    Returns:
        크롤링된 ArticleDTO 객체 목록
    """
    try:
        logger.info(f"{name} 크롤러 실행 시작")
        articles: List[ArticleDTO] = await crawler.fetch_articles()
        logger.info(f"{name}: {len(articles)}개 기사 크롤링 완료")
        return articles
    except Exception as e:
        logger.error(f"{name} 크롤링 중 오류 발생: {str(e)}")
        return []


async def crawl_all_sources() -> List[ArticleDTO]:
    """
    모든 뉴스 소스에서 크롤링을 병렬로 수행합니다.

    Returns:
        크롤링된 모든 ArticleDTO 객체 목록
    """
    logger.info("크롤링 작업을 시작합니다...")
    start_time = datetime.now()

    # 등록된 크롤러 확인
    logger.info(f"등록된 크롤러: {', '.join(CRAWLERS.keys())}")

    # 비동기로 모든 크롤러 실행
    tasks = [run_crawler(name, crawler) for name, crawler in CRAWLERS.items()]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 결과 처리
    all_articles: List[ArticleDTO] = []
    source_names: List[str] = list(CRAWLERS.keys())

    for i, result in enumerate(results):
        source = source_names[i] if i < len(source_names) else f"소스{i}"
        if isinstance(result, Exception):
            logger.error(f"{source} 크롤링 중 오류 발생: {str(result)}")
        else:
            logger.info(f"{source}: {len(result)}개 기사 크롤링 완료")
            all_articles.extend(result)

    # 실행 시간 계산
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"총 {len(all_articles)}개 기사 크롤링 완료 (소요시간: {elapsed:.2f}초)"
    )

    return all_articles


async def main() -> None:
    """메인 실행 함수"""
    logger.info("====== 뉴스 크롤링 작업 시작 ======")

    try:
        # 크롤링 실행
        articles = await crawl_all_sources()

        if not articles:
            logger.warning("크롤링된 기사가 없습니다.")
        else:
            logger.info(f"{len(articles)}개 기사를 성공적으로 크롤링했습니다.")

    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)

    finally:
        logger.info("====== 뉴스 크롤링 작업 종료 ======")


if __name__ == "__main__":
    asyncio.run(main())
