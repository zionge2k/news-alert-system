"""
테스트를 위한 공통 픽스처와 구성을 정의하는 파일입니다.
이 파일은 pytest에 의해 자동으로 발견되며, 모든 테스트에서 공유됩니다.
"""

import asyncio
import json

# 시스템 모듈 임포트
import os
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# 프로젝트 루트 경로를 명확하게 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print(f"프로젝트 루트 경로: {PROJECT_ROOT}")

# Python 경로에 프로젝트 루트 추가
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"Python 경로에 {PROJECT_ROOT} 추가됨")

# 환경 변수에 PYTHONPATH 설정
os.environ["PYTHONPATH"] = PROJECT_ROOT

# 현재 경로 출력
print(f"conftest.py의 현재 디렉토리: {os.getcwd()}")
print(f"conftest.py의 Python 경로: {sys.path}")

# pytest 임포트
import pytest

# 테스트 헬퍼 임포트
from tests.helpers import dummy_article_dto, load_test_data


# 비동기 테스트를 위한 이벤트 루프 픽스처
@pytest.fixture
def event_loop():
    """비동기 테스트를 위한 이벤트 루프 설정"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# MongoDB 픽스처
@pytest.fixture
async def mongodb():
    """MongoDB 연결 픽스처"""
    from infra.database.mongodb import MongoDB

    mongodb = MongoDB(uri="mongodb://localhost:27017", database="test_db")
    await mongodb.connect()
    yield mongodb
    await mongodb.disconnect()


# 데이터베이스 모의 픽스처
@pytest.fixture
def mock_db():
    """데이터베이스 모의 픽스처"""
    mock = MagicMock()
    return mock


# 비동기 클라이언트 모의 픽스처
@pytest.fixture
def mock_async_client():
    """비동기 클라이언트 모의 픽스처"""
    mock = AsyncMock()
    return mock


# 향상된 MongoDB 컬렉션 모킹 픽스처
@pytest.fixture
def mock_article_collection():
    """기사 컬렉션에 대한 고급 모킹 픽스처입니다."""
    with patch("motor.motor_asyncio.AsyncIOMotorCollection") as mock_collection:
        # 저장할 문서들 (메모리 내 "데이터베이스")
        in_memory_docs = []

        # insert_one 메서드 모킹
        async def mock_insert_one(document):
            doc_id = f"test_id_{len(in_memory_docs) + 1}"
            document["_id"] = doc_id
            in_memory_docs.append(document)

            mock_result = MagicMock()
            mock_result.inserted_id = doc_id
            return mock_result

        # find_one 메서드 모킹
        async def mock_find_one(filter_dict=None, *args, **kwargs):
            if not filter_dict or not in_memory_docs:
                return None

            # 간단한 필터링 로직 구현
            if "_id" in filter_dict:
                for doc in in_memory_docs:
                    if doc.get("_id") == filter_dict["_id"]:
                        return doc

            # unique_id를 이용한 검색
            if "unique_id" in filter_dict:
                for doc in in_memory_docs:
                    if doc.get("unique_id") == filter_dict["unique_id"]:
                        return doc

            return None

        # find 메서드 모킹
        async def mock_find(filter_dict=None, *args, **kwargs):
            # 목 커서 만들기
            mock_cursor = AsyncMock()

            # 필터링된 문서 목록
            filtered_docs = in_memory_docs
            if filter_dict:
                # 간단한 필터링 구현
                if "metadata.platform" in filter_dict:
                    platform = filter_dict["metadata.platform"]
                    filtered_docs = [
                        doc
                        for doc in in_memory_docs
                        if doc.get("metadata", {}).get("platform") == platform
                    ]

            # to_list 메서드 모킹
            mock_cursor.to_list.return_value = filtered_docs
            return mock_cursor

        # 목 메서드 할당
        mock_collection.insert_one = mock_insert_one
        mock_collection.find_one = mock_find_one
        mock_collection.find = mock_find

        # 추가 헬퍼 메서드 (테스트에서 직접 데이터 조작용)
        mock_collection.get_all_docs = lambda: in_memory_docs
        mock_collection.clear_docs = lambda: in_memory_docs.clear()

        yield mock_collection


# HTTP 요청 모킹을 위한 픽스처
@pytest.fixture
def mock_http_response():
    """HTTP 응답을 모킹하는 픽스처입니다."""

    class MockResponse:
        def __init__(self, json_data=None, status=200, text=""):
            self.json_data = json_data or {}
            self.status = status
            self.text = text

        async def json(self):
            return self.json_data

        async def text(self):
            return self.text

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def __aenter__(self):
            return self

    return MockResponse


# 고급 HTTP 클라이언트 모킹 픽스처
@pytest.fixture
def mock_aiohttp_client():
    """aiohttp.ClientSession을 모킹하는 고급 픽스처입니다."""
    with patch("aiohttp.ClientSession") as mock_session:
        # 응답 저장을 위한 딕셔너리
        responses = {}

        # 기본 응답 준비
        try:
            default_response = load_test_data("sample_news_response.json")
        except FileNotFoundError:
            default_response = {
                "items": [
                    {
                        "title": "기본 테스트 뉴스",
                        "link": "https://example.com/default",
                        "description": "기본 테스트 데이터입니다.",
                        "pubDate": "2023-01-01T00:00:00+09:00",
                    }
                ]
            }

        # get 메서드 모킹
        async def mock_get(url, *args, **kwargs):
            # URL에 따라 다른 응답 반환
            response_data = responses.get(url, default_response)

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json.return_value = response_data
            mock_resp.text.return_value = json.dumps(response_data)
            mock_resp.__aenter__.return_value = mock_resp

            return mock_resp

        # post 메서드 모킹
        async def mock_post(url, *args, **kwargs):
            # 요청 본문에 따라 다른 응답 반환 가능
            response_data = responses.get(url, default_response)

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json.return_value = response_data
            mock_resp.text.return_value = json.dumps(response_data)
            mock_resp.__aenter__.return_value = mock_resp

            return mock_resp

        # 목 메서드 할당
        mock_instance = mock_session.return_value
        mock_instance.get = mock_get
        mock_instance.post = mock_post

        # 테스트에서 응답 설정을 위한 헬퍼 메서드
        mock_instance.set_response = lambda url, data: responses.update({url: data})

        # 세션이 비동기 컨텍스트 매니저로 작동하도록 설정
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None

        yield mock_instance


# 테스트 데이터 디렉토리 픽스처
@pytest.fixture
def test_data_dir():
    """테스트 데이터 디렉토리 경로를 제공하는 픽스처입니다."""
    return os.path.join(os.path.dirname(__file__), "data")


# 더미 기사 데이터 픽스처
@pytest.fixture
def dummy_articles(request):
    """
    지정된 수의 더미 기사 DTO 객체 목록을 제공하는 픽스처입니다.

    사용 예:
        def test_something(dummy_articles):
            articles = dummy_articles(5)  # 5개의 더미 기사 생성
    """

    def _create_dummy_articles(count: int = 3, platform: str = "TEST") -> List[Any]:
        return [
            dummy_article_dto(
                metadata=dummy_article_dto().metadata.model_copy(
                    update={"platform": platform}
                )
            )
            for _ in range(count)
        ]

    return _create_dummy_articles
