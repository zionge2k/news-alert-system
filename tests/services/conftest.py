import asyncio
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_db():
    # DB 또는 저장소를 모킹
    return MagicMock(name="MockDB")


@pytest.fixture
def mock_news():
    # 샘플 뉴스 데이터
    return {
        "id": 1,
        "title": "테스트 뉴스 제목",
        "content": "테스트 본문 내용",
        "source": "JTBC",
        "published_at": "2024-06-01T12:00:00Z",
    }


# pytest에서 비동기 함수를 실행하기 위한 헬퍼 함수
@pytest.fixture(scope="session")
def event_loop():
    """pytest-asyncio 플러그인용 이벤트 루프 생성"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 비동기 함수를 동기적으로 실행하는 헬퍼 함수
def run_async(coro):
    """비동기 코루틴을 동기적으로 실행"""
    return asyncio.get_event_loop().run_until_complete(coro)


# pytest 모듈에 헬퍼 함수 추가
pytest.run_async = run_async
