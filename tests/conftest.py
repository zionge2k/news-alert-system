# 이 파일은 임시로 비활성화되었습니다.
# poetry를 사용하여 모듈 경로를 관리하기 위해 원래 conftest.py의 내용을 주석 처리했습니다.
# 필요한 경우 이 파일을 conftest.py로 이름을 변경하고 내용을 수정하여 활성화할 수 있습니다.

"""
테스트를 위한 공통 Pytest 설정 및 픽스처를 정의합니다.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Python 경로에 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 비활성화된 임포트
# from infra.database.mongodb import MongoDB
# from infra.database.repository.factory import create_article_repository

# Python 경로 조작 코드 제거 (Poetry를 사용하여 패키지를 관리하므로 필요 없음)

# .env 파일 경로
ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")


@pytest.fixture(scope="session")
def event_loop():
    """전체 테스트 세션 동안 공유되는 이벤트 루프 생성"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 비활성화된 MongoDB 관련 픽스처
"""
@pytest_asyncio.fixture
async def mongodb_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    # 테스트용 MongoDB 클라이언트 픽스처
    # 테스트용 MongoDB 연결 문자열 - 실제 DB 대신 테스트 DB 사용
    mongo_uri = os.environ.get("MONGODB_TEST_URI", "mongodb://localhost:27017/test_db")
    client = AsyncIOMotorClient(mongo_uri)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def mongodb(mongodb_client) -> AsyncGenerator[MongoDB, None]:
    # 테스트용 MongoDB 인스턴스 픽스처
    db_name = "test_db"
    mongodb = MongoDB(client=mongodb_client, db_name=db_name)
    # 테스트 전에 컬렉션 비우기
    await mongodb_client[db_name].articles.delete_many({})
    await mongodb_client[db_name].queue.delete_many({})
    
    yield mongodb
    
    # 테스트 후 정리
    await mongodb_client[db_name].articles.delete_many({})
    await mongodb_client[db_name].queue.delete_many({})


@pytest_asyncio.fixture
async def article_repository(mongodb):
    # 기사 리포지토리 픽스처
    repository = create_article_repository(mongodb)
    return repository
"""
