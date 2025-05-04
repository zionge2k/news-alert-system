#!/usr/bin/env python
"""
MongoDB 큐 테스트 스크립트

이 스크립트는 MongoDB 큐 기능을 테스트하기 위한 간단한 도구입니다.
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 상위 디렉토리를 모듈 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

# 큐 서비스
from app.storage.queue.services import queue_service

# 로깅
from common.utils.logger import get_logger

# MongoDB 연결 관리
from db.mongodb import close_mongodb, init_mongodb

# 로거 설정
logger = get_logger(__name__)


def parse_arguments():
    """명령줄 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(description="MongoDB 큐 테스트 스크립트")
    parser.add_argument(
        "--action",
        choices=["status", "retry", "clean", "add"],
        default="status",
        help="수행할 작업 (status: 상태 확인, retry: 실패 항목 재시도, clean: 오래된 항목 정리, add: DB에서 기사 추가)",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="정리할 오래된 항목의 기간 (일)"
    )
    parser.add_argument(
        "--hours", type=int, default=24, help="DB에서 가져올 기사의 시간 범위 (시간)"
    )
    parser.add_argument("--max-retries", type=int, default=3, help="최대 재시도 횟수")
    parser.add_argument("--limit", type=int, default=50, help="처리할 최대 항목 수")
    parser.add_argument(
        "--platform",
        type=str,
        default=None,
        help="필터링할 플랫폼 (예: YTN, MBC, JTBC)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="필터링할 카테고리 (예: 정치, 경제, 사회)",
    )
    return parser.parse_args()


async def show_queue_status():
    """큐 상태를 출력합니다."""
    status = await queue_service.get_queue_status()

    print("\n===== 큐 상태 =====")
    print(f"대기 중: {status.get('pending', 0)}개")
    print(f"처리 중: {status.get('processing', 0)}개")
    print(f"완료: {status.get('completed', 0)}개")
    print(f"실패: {status.get('failed', 0)}개")
    print(f"총계: {status.get('total', 0)}개")
    print("===================\n")


async def retry_failed_items(max_retries):
    """실패한 항목을 재시도합니다."""
    retry_count = await queue_service.retry_failed_articles(max_retries)
    print(f"\n{retry_count}개 실패 항목이 재시도 큐에 추가되었습니다.\n")


async def clean_old_items(days):
    """오래된 완료 항목을 정리합니다."""
    cleaned_count = await queue_service.clean_old_articles(days)
    print(f"\n{cleaned_count}개 오래된 완료 항목이 정리되었습니다.\n")


async def add_db_articles(platform, category, limit, hours):
    """DB에서 기사를 가져와 큐에 추가합니다."""
    print(f"\n===== DB 기사 큐 추가 =====")
    print(f"플랫폼: {platform or '모든 플랫폼'}")
    print(f"카테고리: {category or '모든 카테고리'}")
    print(f"최대 항목 수: {limit}")
    print(f"시간 범위: 최근 {hours}시간")
    print("=======================")

    added_count = await queue_service.add_articles_from_db(
        platform=platform, category=category, limit=limit, hours=hours
    )

    print(f"\n{added_count}개 기사가 큐에 추가되었습니다.\n")


async def main():
    """
    메인 실행 함수
    """
    # 명령줄 인자 파싱
    args = parse_arguments()

    try:
        # MongoDB 연결
        await init_mongodb()
        logger.info("MongoDB 연결 성공")

        # 작업 선택
        if args.action == "status":
            await show_queue_status()
        elif args.action == "retry":
            await retry_failed_items(args.max_retries)
            await show_queue_status()
        elif args.action == "clean":
            await clean_old_items(args.days)
            await show_queue_status()
        elif args.action == "add":
            await add_db_articles(args.platform, args.category, args.limit, args.hours)
            await show_queue_status()

    except Exception as e:
        logger.error(f"실행 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)

    finally:
        # MongoDB 연결 종료
        await close_mongodb()
        logger.info("MongoDB 연결 종료")


if __name__ == "__main__":
    asyncio.run(main())
