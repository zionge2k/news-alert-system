"""
MongoDB 연결 및 관리 기능에 대한 테스트 모듈입니다.
이 테스트 모듈은 db.mongodb 모듈의 MongoDB 클래스와 관련 함수를 테스트합니다.
"""

import asyncio
import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from db.mongodb import MongoDB, close_mongodb, init_mongodb


@pytest.fixture
def mock_motor_client():
    """
    motor.motor_asyncio.AsyncIOMotorClient를 모킹하는 픽스처입니다.
    """
    with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock_client:
        # 모의 데이터베이스 객체 설정
        mock_db = AsyncMock(spec=AsyncIOMotorDatabase)
        mock_client.return_value.__getitem__.return_value = mock_db

        # 모의 admin 데이터베이스 설정
        mock_admin_db = AsyncMock()
        mock_client.return_value.admin = mock_admin_db
        mock_admin_db.command = AsyncMock(return_value={"ok": 1})

        # MongoDB 클래스의 상태 초기화 (테스트 간 독립성 보장)
        MongoDB.client = None
        MongoDB.db = None

        yield mock_client


@pytest.mark.asyncio
async def test_mongodb_connect_success(mock_motor_client):
    """
    MongoDB 연결 성공 시나리오를 테스트합니다.
    """
    # 테스트 데이터
    test_url = "mongodb://test-user:password@test-host:27017"
    test_db = "test_db"

    # 테스트 실행
    await MongoDB.connect(mongodb_url=test_url, db_name=test_db)

    # 검증
    mock_motor_client.assert_called_once_with(test_url)
    assert mock_motor_client.return_value.__getitem__.call_args[0][0] == test_db
    mock_motor_client.return_value.admin.command.assert_called_once_with("ping")
    assert MongoDB.client is not None
    assert MongoDB.db is not None


@pytest.mark.asyncio
async def test_mongodb_connect_with_env_vars(mock_motor_client, monkeypatch):
    """
    환경 변수를 사용한 MongoDB 연결을 테스트합니다.
    """
    # 환경 변수 설정
    monkeypatch.setenv("MONGODB_URL", "mongodb://env-user:env-pass@env-host:27017")
    monkeypatch.setenv("MONGODB_DB_NAME", "env_db")

    # 테스트 실행
    await MongoDB.connect()

    # 검증
    mock_motor_client.assert_called_once_with(
        "mongodb://env-user:env-pass@env-host:27017"
    )
    assert mock_motor_client.return_value.__getitem__.call_args[0][0] == "env_db"


@pytest.mark.asyncio
async def test_mongodb_connect_with_default_values(mock_motor_client, monkeypatch):
    """
    기본값을 사용한 MongoDB 연결을 테스트합니다.
    """
    # 환경 변수 제거
    monkeypatch.delenv("MONGODB_URL", raising=False)
    monkeypatch.delenv("MONGODB_DB_NAME", raising=False)

    # 테스트 실행
    await MongoDB.connect()

    # 검증
    mock_motor_client.assert_called_once_with(MongoDB.DEFAULT_URL)
    assert mock_motor_client.return_value.__getitem__.call_args[0][0] == MongoDB.DB_NAME


@pytest.mark.asyncio
async def test_mongodb_connect_error(mock_motor_client):
    """
    MongoDB 연결 실패 시나리오를 테스트합니다.
    """
    # 모의 예외 설정
    mock_motor_client.return_value.admin.command.side_effect = Exception(
        "Connection failed"
    )

    # 테스트 실행 및 예외 검증
    with pytest.raises(Exception) as exc_info:
        await MongoDB.connect()

    # 예외 메시지 검증
    assert "Connection failed" in str(exc_info.value)

    # 상태 검증
    assert MongoDB.client is not None  # client는 생성되지만
    assert MongoDB.db is not None  # db도 생성되지만, ping 명령에서 실패


@pytest.mark.asyncio
async def test_mongodb_close(mock_motor_client):
    """
    MongoDB 연결 종료 기능을 테스트합니다.
    """
    # 먼저 연결을 설정
    await MongoDB.connect()
    assert MongoDB.client is not None
    assert MongoDB.db is not None

    # 연결 종료
    await MongoDB.close()

    # 검증
    mock_motor_client.return_value.close.assert_called_once()
    assert MongoDB.client is None
    assert MongoDB.db is None


@pytest.mark.asyncio
async def test_get_database_without_connection():
    """
    연결 없이 데이터베이스를 가져오려는 시도를 테스트합니다.
    """
    # 기존 연결이 있다면 정리
    if MongoDB.client:
        await MongoDB.close()

    # 연결 없이 데이터베이스 가져오기 시도
    with pytest.raises(ConnectionError) as exc_info:
        MongoDB.get_database()

    # 예외 메시지 검증
    assert "MongoDB에 연결되어 있지 않습니다" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_database_with_connection(mock_motor_client):
    """
    데이터베이스 가져오기 기능을 테스트합니다.
    """
    # 연결 설정
    await MongoDB.connect()

    # 데이터베이스 가져오기
    db = MongoDB.get_database()

    # 검증
    assert db is not None
    assert db == MongoDB.db


@pytest.mark.asyncio
async def test_get_collection(mock_motor_client):
    """
    컬렉션 가져오기 기능을 테스트합니다.
    """
    # 연결 설정
    await MongoDB.connect()

    # 컬렉션 가져오기
    collection_name = "test_collection"
    collection = MongoDB.get_collection(collection_name)

    # 검증
    assert collection is not None
    MongoDB.get_database().__getitem__.assert_called_once_with(collection_name)


@pytest.mark.asyncio
async def test_initialize_indexes(mock_motor_client):
    """
    인덱스 초기화 기능을 테스트합니다.
    """
    # 모의 인덱스 함수 설정
    with (
        patch("app.models.article.create_article_indexes") as mock_article_indexes,
        patch("app.models.queue.create_queue_indexes") as mock_queue_indexes,
        patch(
            "app.models.published.create_published_article_indexes"
        ) as mock_published_indexes,
    ):

        # 연결 설정 (initialize_indexes가 내부적으로 호출됨)
        await MongoDB.connect()

        # 검증
        mock_article_indexes.assert_called_once_with(MongoDB.db)
        mock_queue_indexes.assert_called_once_with(MongoDB.db)
        mock_published_indexes.assert_called_once_with(MongoDB.db)


@pytest.mark.asyncio
async def test_init_mongodb_helper(mock_motor_client):
    """
    init_mongodb 헬퍼 함수를 테스트합니다.
    """
    # init_mongodb 호출
    await init_mongodb("mongodb://helper:password@host:27017", "helper_db")

    # 검증
    mock_motor_client.assert_called_once_with("mongodb://helper:password@host:27017")
    assert mock_motor_client.return_value.__getitem__.call_args[0][0] == "helper_db"
    assert MongoDB.client is not None
    assert MongoDB.db is not None


@pytest.mark.asyncio
async def test_close_mongodb_helper(mock_motor_client):
    """
    close_mongodb 헬퍼 함수를 테스트합니다.
    """
    # 먼저 연결 설정
    await init_mongodb()
    assert MongoDB.client is not None

    # close_mongodb 호출
    await close_mongodb()

    # 검증
    mock_motor_client.return_value.close.assert_called_once()
    assert MongoDB.client is None
    assert MongoDB.db is None


@pytest.mark.asyncio
async def test_mongodb_initialize_indexes_error(mock_motor_client):
    """
    인덱스 초기화 실패 시나리오를 테스트합니다.
    """
    # 모의 인덱스 함수 설정 - 예외 발생
    with patch("app.models.article.create_article_indexes") as mock_article_indexes:
        mock_article_indexes.side_effect = Exception("Index creation failed")

        # 테스트 실행 및 예외 검증
        with pytest.raises(Exception) as exc_info:
            await MongoDB.connect()

        # 예외 메시지 검증
        assert "Index creation failed" in str(exc_info.value)
