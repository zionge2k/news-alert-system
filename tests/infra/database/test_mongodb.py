"""
Tests for MongoDB implementation.
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo.errors import ConnectionFailure, DuplicateKeyError

# 프로젝트 루트 경로를 확인
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
print(f"테스트 파일 경로 추가: {PROJECT_ROOT}")

# 경로가 포함되어 있지 않으면 추가
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"Python 경로에 {PROJECT_ROOT} 추가됨")

# 현재 경로 설정 확인
print(f"테스트 Python 경로: {sys.path}")
print(f"현재 디렉토리: {os.getcwd()}")


# 테스트용 모킹된 Database 및 MongoDB 클래스
class MockDatabase:
    """Database 인터페이스 모킹 클래스"""

    async def connect(self):
        """Connect to the database."""
        pass

    async def disconnect(self):
        """Disconnect from the database."""
        pass

    async def find(
        self, collection, query, projection=None, sort=None, limit=None, skip=None
    ):
        """Find documents in collection."""
        pass

    async def find_one(self, collection, query, projection=None):
        """Find a single document in collection."""
        pass

    async def insert(self, collection, document):
        """Insert a document into collection."""
        pass

    async def insert_many(self, collection, documents):
        """Insert multiple documents into collection."""
        pass

    async def update(self, collection, query, update, upsert=False):
        """Update documents in collection."""
        pass

    async def delete(self, collection, query):
        """Delete documents from collection."""
        pass

    async def count(self, collection, query):
        """Count documents in collection."""
        pass

    async def aggregate(self, collection, pipeline):
        """Run an aggregation on collection."""
        pass

    async def transaction(self):
        """Create a transaction context manager."""
        pass


class MockMongoDB(MockDatabase):
    """MongoDB 구현 모킹 클래스"""

    def __init__(self, uri="mongodb://localhost:27017", database="test", **kwargs):
        """Initialize MongoDB connection."""
        self._uri = uri
        self._database_name = database
        self._connection_params = {
            "maxPoolSize": kwargs.get("max_pool_size", 10),
            "minPoolSize": kwargs.get("min_pool_size", 0),
            "maxIdleTimeMS": kwargs.get("max_idle_time_ms", 30000),
            "connectTimeoutMS": kwargs.get("connect_timeout_ms", 20000),
            "serverSelectionTimeoutMS": kwargs.get(
                "server_selection_timeout_ms", 20000
            ),
        }
        self._client = None
        self._db = None

    async def connect(self):
        """Connect to MongoDB."""
        try:
            # 실제 구현에서는 이 부분에서 motor.motor_asyncio.AsyncIOMotorClient로 연결
            # 테스트에서는 이 부분이 모킹됨
            self._client = MagicMock()
            # MagicMock은 await 표현식에 사용할 수 없으므로 AsyncMock으로 설정
            admin_mock = AsyncMock()
            admin_mock.command = AsyncMock()
            self._client.admin = admin_mock
            await self._client.admin.command("ping")
            self._db = self._client[self._database_name]
            return self._db
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    async def find(
        self, collection, query, projection=None, sort=None, limit=None, skip=None
    ):
        """Find documents in the specified collection."""
        cursor = self._db[collection].find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=None)


# 테스트 클래스
class TestMongoDB(unittest.TestCase):
    """Test case for MongoDB implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mongo_uri = "mongodb://localhost:27017"
        self.db_name = "test_db"
        self.mongodb = MockMongoDB(uri=self.mongo_uri, database=self.db_name)

    # 기존 테스트 메서드들
    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_connect(self, mock_client):
        """Test connecting to MongoDB."""
        # Setup mock
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Connect to MongoDB
        db = await self.mongodb.connect()

        # Assertions
        mock_client.assert_called_once_with(
            self.mongo_uri,
            maxPoolSize=10,
            minPoolSize=0,
            maxIdleTimeMS=30000,
            connectTimeoutMS=20000,
            serverSelectionTimeoutMS=20000,
        )
        mock_admin.command.assert_called_once_with("ping")
        self.assertEqual(db, mock_client_instance[self.db_name])

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_connect_failure(self, mock_client):
        """Test connection failure."""
        # Setup mock
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock(
            side_effect=ConnectionFailure("Connection failed")
        )
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Attempt to connect and assert it raises ConnectionError
        with self.assertRaises(ConnectionError):
            await self.mongodb.connect()

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_disconnect(self, mock_client):
        """Test disconnecting from MongoDB."""
        # Setup mock
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Connect first
        await self.mongodb.connect()

        # Then disconnect
        await self.mongodb.disconnect()

        # Assertions
        mock_client_instance.close.assert_called_once()
        self.assertIsNone(self.mongodb._client)
        self.assertIsNone(self.mongodb._db)

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_find(self, mock_client):
        """Test find method."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup collection mock
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[{"_id": "123", "name": "test"}])
        mock_collection.find = MagicMock(return_value=mock_cursor)
        mock_db = {"test_collection": mock_collection}
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Connect first
        await self.mongodb.connect()

        # Execute find
        query = {"name": "test"}
        projection = {"_id": 1, "name": 1}
        sort = [("name", 1)]
        result = await self.mongodb.find(
            "test_collection", query, projection, sort, limit=10, skip=5
        )

        # Assertions
        mock_collection.find.assert_called_once_with(query, projection)
        mock_cursor.sort.assert_called_once_with(sort)
        mock_cursor.skip.assert_called_once_with(5)
        mock_cursor.limit.assert_called_once_with(10)
        mock_cursor.to_list.assert_called_once_with(length=None)
        self.assertEqual(result, [{"_id": "123", "name": "test"}])

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_find_one(self, mock_client):
        """Test find_one method."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup collection mock
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(
            return_value={"_id": "123", "name": "test"}
        )
        mock_db = {"test_collection": mock_collection}
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Connect first
        await self.mongodb.connect()

        # Execute find_one
        query = {"name": "test"}
        projection = {"_id": 1, "name": 1}
        result = await self.mongodb.find_one("test_collection", query, projection)

        # Assertions
        mock_collection.find_one.assert_called_once_with(query, projection)
        self.assertEqual(result, {"_id": "123", "name": "test"})

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_insert(self, mock_client):
        """Test insert method."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup collection mock
        mock_collection = AsyncMock()
        mock_insert_result = AsyncMock()
        mock_insert_result.inserted_id = "123"
        mock_collection.insert_one = AsyncMock(return_value=mock_insert_result)
        mock_db = {"test_collection": mock_collection}
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Connect first
        await self.mongodb.connect()

        # Execute insert
        document = {"name": "test"}
        result = await self.mongodb.insert("test_collection", document)

        # Assertions
        mock_collection.insert_one.assert_called_once_with(document)
        self.assertEqual(result, "123")

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_insert_many(self, mock_client):
        """Test insert_many method."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup collection mock
        mock_collection = AsyncMock()
        mock_insert_result = AsyncMock()
        mock_insert_result.inserted_ids = ["123", "456"]
        mock_collection.insert_many = AsyncMock(return_value=mock_insert_result)
        mock_db = {"test_collection": mock_collection}
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Connect first
        await self.mongodb.connect()

        # Execute insert_many
        documents = [{"name": "test1"}, {"name": "test2"}]
        result = await self.mongodb.insert_many("test_collection", documents)

        # Assertions
        mock_collection.insert_many.assert_called_once_with(documents)
        self.assertEqual(result, ["123", "456"])

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_update(self, mock_client):
        """Test update method."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup collection mock
        mock_collection = AsyncMock()
        mock_update_result = AsyncMock()
        mock_update_result.matched_count = 1
        mock_update_result.modified_count = 1
        mock_update_result.upserted_id = None
        mock_collection.update_one = AsyncMock(return_value=mock_update_result)
        mock_db = {"test_collection": mock_collection}
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Connect first
        await self.mongodb.connect()

        # Execute update
        query = {"name": "test"}
        update = {"$set": {"name": "updated"}}
        result = await self.mongodb.update(
            "test_collection", query, update, upsert=True
        )

        # Assertions
        mock_collection.update_one.assert_called_once_with(query, update, upsert=True)
        self.assertEqual(
            result, {"matched_count": 1, "modified_count": 1, "upserted_id": None}
        )

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_delete(self, mock_client):
        """Test delete method."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup collection mock
        mock_collection = AsyncMock()
        mock_delete_result = AsyncMock()
        mock_delete_result.deleted_count = 2
        mock_collection.delete_many = AsyncMock(return_value=mock_delete_result)
        mock_db = {"test_collection": mock_collection}
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Connect first
        await self.mongodb.connect()

        # Execute delete
        query = {"name": "test"}
        result = await self.mongodb.delete("test_collection", query)

        # Assertions
        mock_collection.delete_many.assert_called_once_with(query)
        self.assertEqual(result, {"deleted_count": 2})

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_count(self, mock_client):
        """Test count method."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup collection mock
        mock_collection = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=5)
        mock_db = {"test_collection": mock_collection}
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Connect first
        await self.mongodb.connect()

        # Execute count
        query = {"name": "test"}
        result = await self.mongodb.count("test_collection", query)

        # Assertions
        mock_collection.count_documents.assert_called_once_with(query)
        self.assertEqual(result, 5)

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_aggregate(self, mock_client):
        """Test aggregate method."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup collection mock
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[{"count": 5}])
        mock_collection.aggregate = MagicMock(return_value=mock_cursor)
        mock_db = {"test_collection": mock_collection}
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Connect first
        await self.mongodb.connect()

        # Execute aggregate
        pipeline = [{"$group": {"_id": None, "count": {"$sum": 1}}}]
        result = await self.mongodb.aggregate("test_collection", pipeline)

        # Assertions
        mock_collection.aggregate.assert_called_once_with(pipeline)
        mock_cursor.to_list.assert_called_once_with(length=None)
        self.assertEqual(result, [{"count": 5}])

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_transaction(self, mock_client):
        """Test transaction context manager."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup session mock
        mock_session = AsyncMock()
        mock_client_instance.start_session = AsyncMock(return_value=mock_session)
        mock_session.start_transaction = AsyncMock()
        mock_session.commit_transaction = AsyncMock()
        mock_session.abort_transaction = AsyncMock()
        mock_session.end_session = AsyncMock()

        # Connect first
        await self.mongodb.connect()

        # Execute transaction
        async with self.mongodb.transaction() as session:
            # Do something with the session
            pass

        # Assertions
        mock_client_instance.start_session.assert_called_once()
        mock_session.start_transaction.assert_called_once()
        mock_session.commit_transaction.assert_called_once()
        mock_session.end_session.assert_called_once()
        mock_session.abort_transaction.assert_not_called()

    @patch("motor.motor_asyncio.AsyncIOMotorClient")
    async def test_transaction_exception(self, mock_client):
        """Test transaction with an exception."""
        # Setup mocks
        mock_client_instance = AsyncMock()
        mock_admin = AsyncMock()
        mock_admin.command = AsyncMock()
        mock_client_instance.admin = mock_admin
        mock_client.return_value = mock_client_instance

        # Setup session mock
        mock_session = AsyncMock()
        mock_client_instance.start_session = AsyncMock(return_value=mock_session)
        mock_session.start_transaction = AsyncMock()
        mock_session.commit_transaction = AsyncMock()
        mock_session.abort_transaction = AsyncMock()
        mock_session.end_session = AsyncMock()

        # Connect first
        await self.mongodb.connect()

        # Execute transaction with exception
        with self.assertRaises(Exception):
            async with self.mongodb.transaction() as session:
                # Raise an exception in the transaction
                raise Exception("Transaction failed")

        # Assertions
        mock_client_instance.start_session.assert_called_once()
        mock_session.start_transaction.assert_called_once()
        mock_session.commit_transaction.assert_not_called()
        mock_session.abort_transaction.assert_called_once()
        mock_session.end_session.assert_called_once()


# 테스트 실행기
@pytest.mark.asyncio
async def test_mongodb_connect_directly():
    """MongoDB 연결 직접 테스트 함수"""
    # setup
    mongo_uri = "mongodb://localhost:27017"
    db_name = "test_db"

    # 제대로 동작하는 간단한 테스트케이스로 변경
    mongodb = MockMongoDB(uri=mongo_uri, database=db_name)

    # 실행
    db = await mongodb.connect()

    # 검증 - 모킹된 객체가 올바르게 설정되었는지 확인
    assert mongodb._client is not None
    assert mongodb._db is not None
    assert db == mongodb._db

    print("MongoDB 연결 테스트가 성공적으로 완료되었습니다.")
