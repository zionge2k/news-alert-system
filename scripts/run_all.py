#!/usr/bin/env python
"""
뉴스 크롤링 및 MongoDB 저장 통합 스크립트

이 스크립트는 다양한 뉴스 소스에서 기사를 크롤링하고 MongoDB에 저장합니다.
병렬 크롤링으로 효율적으로 처리하며, 중복 기사는 자동으로 필터링합니다.

주요 기능:
1. 여러 뉴스 API 크롤러를 병렬로 실행하여 데이터를 수집
2. 수집된 기사의 URL을 기준으로 중복 확인
3. 신규 기사만 MongoDB에 저장
4. 수집 및 저장 과정에 대한 상세 로깅

사전 요구사항:
- MongoDB 연결 설정 (URL 및 인증 정보)
- 뉴스 크롤러 구현 (app/crawler/ 디렉토리)
- 모델 및 저장소 설정 (app/models/, db/repositories/)

사용법:
    python scripts/run_all.py [--no-save]

옵션:
    --no-save: 크롤링만 실행하고 DB에 저장하지 않음
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 상위 디렉토리를 모듈 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

# 로깅
from common.utils.logger import get_logger

# MongoDB 연결 관리
from db.mongodb import close_mongodb, init_mongodb

# 분리된 크롤링/저장 모듈 임포트
from scripts.crawl import crawl_all_sources
from scripts.save import save_to_database

# 로거 설정
logger = get_logger(__name__)


def parse_arguments():
    """명령줄 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(description="뉴스 크롤링 및 MongoDB 저장 스크립트")
    parser.add_argument(
        "--no-save", action="store_true", help="크롤링만 실행하고 DB에 저장하지 않음"
    )
    return parser.parse_args()


async def main():
    """
    메인 실행 함수

    크롤링과 DB 저장을 연속으로 실행하고 결과를 로깅합니다.
    """
    # 명령줄 인자 파싱
    args = parse_arguments()

    start_time = datetime.now()
    logger.info("====== 뉴스 크롤링 및 DB 저장 통합 작업 시작 ======")

    try:
        # MongoDB 연결
        await init_mongodb()
        logger.info("MongoDB 연결 성공")

        # 1. 크롤링
        logger.info("1단계: 뉴스 기사 크롤링 시작")
        articles = await crawl_all_sources()

        # 크롤링된 기사가 없으면 중단
        if not articles:
            logger.warning("크롤링된 기사가 없습니다.")
            return

        # 2. DB 저장 (--no-save 옵션이 없는 경우)
        if not args.no_save:
            logger.info("2단계: 기사 데이터베이스 저장 시작")
            saved_count = await save_to_database(articles)
            logger.info(f"{saved_count}개 기사가 성공적으로 저장되었습니다")
        else:
            logger.info("DB 저장 단계를 건너뜁니다 (--no-save 옵션 사용)")

        # 실행 시간 계산
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"작업 완료! 소요시간: {elapsed:.2f}초")

    except Exception as e:
        logger.error(f"실행 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)

    finally:
        # MongoDB 연결 종료
        await close_mongodb()
        logger.info("MongoDB 연결 종료")
        logger.info("====== 뉴스 크롤링 및 DB 저장 통합 작업 종료 ======")


if __name__ == "__main__":
    asyncio.run(main())
