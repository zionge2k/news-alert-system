#!/usr/bin/env python
"""
Discord 발행 서비스 실행 스크립트

이 스크립트는 Discord 발행 서비스를 독립적으로 실행합니다.
"""

import asyncio
import os
import signal
import sys
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가하여 절대 경로 import가 작동하도록 설정
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

# 이제 common 로거 사용
try:
    from common.utils.logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("discord_publisher")
    logger.warning("common.utils.logger를 가져올 수 없어 기본 로거를 사용합니다.")

# 이제 앱 모듈을 임포트
try:
    from app.pipelines.discord_publisher.service import (
        discord_publisher_service,
        start_discord_publisher,
    )
except ImportError as e:
    logger.error(f"필요한 모듈을 가져올 수 없습니다: {str(e)}")
    logger.error("프로젝트 구조를 확인하거나 필요한 패키지를 설치하세요.")
    sys.exit(1)


async def shutdown(signal_type, loop):
    """서비스 종료 핸들러"""
    logger.info(f"종료 신호 {signal_type} 수신됨")

    # 서비스 중단
    await discord_publisher_service.stop()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    if tasks:
        logger.info(f"{len(tasks)}개 태스크 종료 중...")
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

    loop.stop()
    logger.info("서비스가 정상 종료되었습니다.")


async def main():
    """메인 실행 함수"""
    logger.info("Discord 발행 서비스를 시작합니다...")

    # 환경변수 확인
    required_vars = ["DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_DEFAULT"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        logger.error("환경변수를 설정하거나 .env 파일을 생성하세요.")
        return 1

    # 서비스 시작
    success = await start_discord_publisher()

    if not success:
        logger.error("Discord 발행 서비스 시작 실패")
        return 1

    # 종료 시그널 핸들러 등록
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop))
        )

    logger.info("Discord 발행 서비스가 실행 중입니다. Ctrl+C를 눌러 종료하세요.")

    # 무한 실행 (시그널로 종료될 때까지)
    try:
        while True:
            await asyncio.sleep(3600)  # 1시간 대기
    except asyncio.CancelledError:
        pass

    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        logger.info("키보드 인터럽트로 종료")
        sys.exit(1)
    except Exception as e:
        logger.error(f"예기치 않은 오류 발생: {str(e)}")
        sys.exit(2)
