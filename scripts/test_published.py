#!/usr/bin/env python
"""
발행된 기사 테스트 스크립트

이 스크립트는 발행된 기사 기능을 테스트하기 위한 간단한 도구입니다.
"""
import argparse
import asyncio
import sys
from pathlib import Path

# 상위 디렉토리를 모듈 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

# 발행된 기사 서비스
from app.storage.published.services import published_article_service

# 로깅
from common.utils.logger import get_logger

# MongoDB 연결 관리
from db.mongodb import close_mongodb, init_mongodb

# 로거 설정
logger = get_logger(__name__)


def parse_arguments():
    """명령줄 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(description="발행된 기사 테스트 스크립트")
    parser.add_argument(
        "--action",
        choices=["status", "clean"],
        default="status",
        help="수행할 작업 (status: 상태 확인, clean: 오래된 항목 정리)",
    )
    parser.add_argument(
        "--days", type=int, default=30, help="정리할 오래된 항목의 기간 (일)"
    )
    return parser.parse_args()


async def show_published_status():
    """발행된 기사 상태를 출력합니다."""
    status = await published_article_service.get_count_by_platform()

    print("\n===== 발행된 기사 상태 =====")
    total = 0
    for platform, count in status.items():
        print(f"{platform}: {count}개")
        total += count
    print(f"총계: {total}개")
    print("=========================\n")


async def clean_old_published(days):
    """오래된 발행 기록을 정리합니다."""
    cleaned_count = await published_article_service.clean_old_published(days)
    print(f"\n{cleaned_count}개 오래된 발행 기록이 정리되었습니다.\n")


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
            await show_published_status()
        elif args.action == "clean":
            await clean_old_published(args.days)
            await show_published_status()

    except Exception as e:
        logger.error(f"실행 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)

    finally:
        # MongoDB 연결 종료
        await close_mongodb()
        logger.info("MongoDB 연결 종료")


if __name__ == "__main__":
    asyncio.run(main())
