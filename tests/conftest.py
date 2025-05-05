"""
테스트를 위한 공통 픽스처와 구성을 정의하는 파일입니다.
이 파일은 pytest에 의해 자동으로 발견되며, 모든 테스트에서 공유됩니다.
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# 프로젝트 루트 경로를 sys.path에 추가하여 어디서든 프로젝트 모듈을 임포트할 수 있게 합니다.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# 비동기 테스트를 위한 설정
@pytest.fixture
def event_loop():
    """전역 이벤트 루프 픽스처를 제공합니다."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# MongoDB 모킹을 위한 픽스처
@pytest.fixture
def mock_mongodb():
    """MongoDB 클라이언트를 모킹하는 픽스처입니다."""
    with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock_client:
        mock_db = MagicMock()
        mock_collection = MagicMock()

        # 모킹된 메서드 설정
        mock_collection.insert_one.return_value.inserted_id = "test_id"
        mock_collection.find_one.return_value = {"_id": "test_id"}

        # 속성 체이닝을 위한 설정
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        yield mock_client


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


# 테스트 데이터 디렉토리 픽스처
@pytest.fixture
def test_data_dir():
    """테스트 데이터 디렉토리 경로를 제공하는 픽스처입니다."""
    return os.path.join(os.path.dirname(__file__), "data")
