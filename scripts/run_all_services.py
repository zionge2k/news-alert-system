#!/usr/bin/env python
"""
뉴스 알림 시스템 통합 서비스 실행 스크립트

이 스크립트는 다음 작업들을 순차적으로 실행합니다:
1. 뉴스 크롤링 및 MongoDB 저장
2. 저장된 기사를 큐에 추가
3. Discord 발행 서비스 실행

모든 서비스가 하나의 스크립트로 통합되어 있어 시스템을 쉽게 시작할 수 있습니다.
"""
import argparse
import asyncio
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# 상위 디렉토리를 모듈 경로에 추가
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.append(project_root)

# Discord 발행 서비스
from app.pipelines.discord_publisher.service import (
    discord_publisher_service,
    start_discord_publisher,
)

# 큐 서비스
from app.storage.queue.services import queue_service

# 로깅
from common.utils.logger import get_logger

# MongoDB 연결 관리 - 경로 수정 및 전역 인스턴스 임포트
from infra.database.mongodb import (
    MongoDB,
    create_mongodb_connection,
    global_mongodb_instance,
)

# 크롤링/저장 모듈 임포트
from scripts.crawl import crawl_all_sources
from scripts.save import save_to_database

# 로거 설정
logger = get_logger(__name__)


async def init_mongodb(mongodb_url=None, db_name=None):
    """MongoDB 연결을 초기화합니다."""
    global global_mongodb_instance

    # 환경변수나 명령행 인자에서 연결 정보 가져오기
    uri = mongodb_url or os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    database = db_name or os.environ.get("MONGODB_DATABASE", "news_system")

    try:
        # MongoDB 인스턴스 생성 및 연결
        mongodb = create_mongodb_connection(uri=uri, database=database)
        await mongodb.connect()

        # 전역 인스턴스에 할당
        global_mongodb_instance = mongodb

        logger.info(f"MongoDB 연결 성공: {database}")
        return True
    except Exception as e:
        logger.error(f"MongoDB 연결 실패: {str(e)}")
        return False


async def close_mongodb():
    """MongoDB 연결을 종료합니다."""
    global global_mongodb_instance

    if global_mongodb_instance:
        await global_mongodb_instance.disconnect()
        global_mongodb_instance = None
        logger.info("MongoDB 연결 종료")


def parse_arguments():
    """명령줄 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(description="뉴스 알림 시스템 통합 서비스")

    # 기본 옵션
    parser.add_argument("--no-crawl", action="store_true", help="크롤링 단계 건너뛰기")
    parser.add_argument("--no-queue", action="store_true", help="큐 추가 단계 건너뛰기")
    parser.add_argument(
        "--no-discord", action="store_true", help="Discord 발행 단계 건너뛰기"
    )

    # MongoDB 옵션
    parser.add_argument(
        "--mongodb-url", help="MongoDB 연결 URL (기본값: 환경변수 또는 기본값 사용)"
    )
    parser.add_argument(
        "--db-name", help="데이터베이스 이름 (기본값: 환경변수 또는 기본값 사용)"
    )

    # 큐 옵션
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
    parser.add_argument(
        "--hours", type=int, default=24, help="DB에서 가져올 기사의 시간 범위 (시간)"
    )
    parser.add_argument(
        "--limit", type=int, default=80, help="큐에 추가할 최대 기사 수"
    )

    # 실행 모드
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="대몬 모드로 실행 (백그라운드에서 계속 실행)",
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="대몬 모드에서 실행 주기 (초)"
    )

    return parser.parse_args()


async def run_crawling_pipeline():
    """크롤링 및 DB 저장 파이프라인을 실행합니다."""
    logger.info("====== 뉴스 크롤링 및 DB 저장 작업 시작 ======")

    try:
        # 1. 크롤링
        logger.info("1단계: 뉴스 기사 크롤링 시작")
        articles = await crawl_all_sources()

        # 크롤링된 기사가 없으면 중단
        if not articles:
            logger.warning("크롤링된 기사가 없습니다.")
            return 0

        # 2. DB 저장
        logger.info("2단계: 기사 데이터베이스 저장 시작")
        saved_count = await save_to_database(articles, global_mongodb_instance)
        logger.info(f"{saved_count}개 기사가 성공적으로 저장되었습니다")

        return saved_count

    except Exception as e:
        logger.error(f"크롤링 및 저장 중 오류 발생: {str(e)}", exc_info=True)
        return 0


async def add_to_queue(platform, category, limit, hours):
    """DB에서 기사를 가져와 큐에 추가합니다."""
    logger.info("====== DB 기사 큐 추가 작업 시작 ======")
    logger.info(f"플랫폼: {platform or '모든 플랫폼'}")
    logger.info(f"카테고리: {category or '모든 카테고리'}")
    logger.info(f"최대 항목 수: {limit}")
    logger.info(f"시간 범위: 최근 {hours}시간")

    try:
        added_count = await queue_service.add_articles_from_db(
            platform=platform,
            category=category,
            limit=limit,
            hours=hours,
            mongodb_instance=global_mongodb_instance,
        )

        logger.info(f"{added_count}개 기사가 큐에 추가되었습니다")
        return added_count

    except Exception as e:
        logger.error(f"큐 추가 중 오류 발생: {str(e)}", exc_info=True)
        return 0


async def show_queue_status():
    """큐 상태를 출력합니다."""
    try:
        status = await queue_service.get_queue_status()

        logger.info("===== 큐 상태 =====")
        logger.info(f"대기 중: {status.get('pending', 0)}개")
        logger.info(f"처리 중: {status.get('processing', 0)}개")
        logger.info(f"완료: {status.get('completed', 0)}개")
        logger.info(f"실패: {status.get('failed', 0)}개")
        logger.info(f"총계: {status.get('total', 0)}개")

        return status
    except Exception as e:
        logger.error(f"큐 상태 조회 중 오류 발생: {str(e)}")
        return {}


async def check_env_variables():
    """필수 환경 변수가 설정되어 있는지 확인합니다."""
    # Discord 환경 변수 확인
    discord_vars = ["DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_DEFAULT"]
    missing_vars = [var for var in discord_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        logger.error("환경변수를 설정하거나 .env 파일을 생성하세요.")
        return False

    return True


async def run_single_cycle(args):
    """하나의 전체 실행 주기를 실행합니다."""
    saved_count = 0
    queued_count = 0

    # 1. 크롤링 및 저장 단계
    if not args.no_crawl:
        saved_count = await run_crawling_pipeline()
    else:
        logger.info("크롤링 단계를 건너뜁니다 (--no-crawl 옵션 사용)")

    # 2. 큐 추가 단계
    if not args.no_queue:
        queued_count = await add_to_queue(
            args.platform, args.category, args.limit, args.hours
        )
    else:
        logger.info("큐 추가 단계를 건너뜁니다 (--no-queue 옵션 사용)")

    # 3. 완료된 기사 정리
    cleaned_count = await queue_service.clean_old_articles()
    if cleaned_count > 0:
        logger.info(f"{cleaned_count}개의 완료된 기사가 큐에서 제거되었습니다")

    return saved_count, queued_count


async def shutdown_services(discord_running, loop=None):
    """서비스를 안전하게 종료합니다."""
    # 1. Discord 서비스 종료
    if discord_running:
        logger.info("Discord 발행 서비스 종료 중...")
        await discord_publisher_service.stop()

    # 2. 나머지 작업 정리
    if loop:
        tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]

        if tasks:
            logger.info(f"{len(tasks)}개 태스크 종료 중...")
            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

    # 3. MongoDB 연결 종료
    await close_mongodb()
    logger.info("MongoDB 연결 종료")

    logger.info("모든 서비스가 정상적으로 종료되었습니다.")


async def run_daemon_mode(args):
    """대몬 모드로 실행합니다."""
    logger.info(f"대몬 모드로 실행합니다. 실행 주기: {args.interval}초")

    # daemon 모드 옵션 조정 - 항상 크롤링과 큐 추가 수행
    daemon_args = args
    daemon_args.no_crawl = False  # 크롤링 항상 실행
    daemon_args.no_queue = False  # 큐 추가 항상 실행

    logger.info("대몬 모드에서는 크롤링 및 큐 추가 단계가 항상 실행됩니다")

    # Discord 서비스 시작
    discord_running = False
    if not args.no_discord:
        # 환경 변수 확인
        if not await check_env_variables():
            return

        logger.info("Discord 발행 서비스 시작 중...")
        success = await start_discord_publisher()
        discord_running = success

        if not success:
            logger.error("Discord 발행 서비스 시작 실패")
            return

    # 종료 시그널 핸들러 설정
    loop = asyncio.get_running_loop()

    def signal_handler(sig):
        logger.info(f"종료 신호 {sig} 수신됨")
        asyncio.create_task(shutdown_services(discord_running, loop))
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    # 주기적 작업 실행
    try:
        while True:
            cycle_start = time.time()

            # 한 주기 실행 (daemon_args 사용)
            await run_single_cycle(daemon_args)

            # 기사 발행 후 큐 상태 확인 (Discord 기사 발행이 완료된 후 상태 표시)
            # Discord 발행 서비스가 기사를 처리할 충분한 시간을 제공
            await asyncio.sleep(5)
            await show_queue_status()

            # 다음 주기까지 대기
            elapsed = time.time() - cycle_start
            sleep_time = max(1, args.interval - elapsed)
            logger.info(f"다음 실행까지 {sleep_time:.1f}초 대기")
            await asyncio.sleep(sleep_time)

    except asyncio.CancelledError:
        logger.info("대몬 작업이 취소되었습니다.")
    except Exception as e:
        logger.error(f"대몬 모드 실행 중 오류 발생: {str(e)}", exc_info=True)
    finally:
        await shutdown_services(discord_running)


async def main():
    """메인 실행 함수"""
    # 명령줄 인자 파싱
    args = parse_arguments()

    start_time = datetime.now()
    logger.info("====== 뉴스 알림 시스템 통합 서비스 시작 ======")

    try:
        # MongoDB 연결
        await init_mongodb(mongodb_url=args.mongodb_url, db_name=args.db_name)
        logger.info("MongoDB 연결 성공")

        # 실행 모드에 따라 처리
        if args.daemon:
            await run_daemon_mode(args)
        else:
            # 단일 실행 모드
            # 1-2. 크롤링, 큐 추가
            await run_single_cycle(args)

            # 3. Discord 발행 (필요한 경우)
            if not args.no_discord:
                # 환경 변수 확인
                if not await check_env_variables():
                    return

                logger.info("Discord 발행 서비스 시작 중...")
                discord_running = await start_discord_publisher()

                if discord_running:
                    logger.info(
                        "Discord 발행 서비스가 실행 중입니다. Ctrl+C를 눌러 종료하세요."
                    )

                    try:
                        # 사용자 입력 대기 (서비스 계속 실행)
                        while True:
                            await asyncio.sleep(3600)
                    except asyncio.CancelledError:
                        pass
                    finally:
                        await discord_publisher_service.stop()
                else:
                    logger.error("Discord 발행 서비스 시작 실패")
            else:
                logger.info("Discord 발행 단계를 건너뜁니다 (--no-discord 옵션 사용)")

        # 실행 시간 계산
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"작업 완료! 소요시간: {elapsed:.2f}초")

    except KeyboardInterrupt:
        logger.info("사용자에 의해 작업이 중단되었습니다")
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # MongoDB 연결 종료
        await close_mongodb()
        logger.info("MongoDB 연결 종료")
        logger.info("====== 뉴스 알림 시스템 통합 서비스 종료 ======")


if __name__ == "__main__":
    asyncio.run(main())
