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

# 확실하게 프로젝트 루트를 Python path에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
print(f"Test file adding path: {project_root}")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 테스트 실행 전 경로 출력
print(f"Python path in test: {sys.path}")
print(f"Current directory: {os.getcwd()}")

try:
    # MongoDB 임포트 시도
    from infra.database.mongodb import MongoDB

    print("Successfully imported MongoDB class")
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying absolute import...")
    sys.path.append(os.getcwd())
    from infra.database.mongodb import MongoDB


class TestMongoDB(unittest.TestCase):
    """Test case for MongoDB implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mongo_uri = "mongodb://localhost:27017"
        self.db_name = "test_db"
        self.mongodb = MongoDB(uri=self.mongo_uri, database=self.db_name)

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


@pytest.mark.asyncio
async def test_mongodb_async():
    """Run all async tests."""
    test_instance = TestMongoDB()
    test_instance.setUp()
    await test_instance.test_connect(AsyncMock())
    await test_instance.test_connect_failure(AsyncMock())
    await test_instance.test_disconnect(AsyncMock())
    await test_instance.test_find(AsyncMock())
    await test_instance.test_find_one(AsyncMock())
    await test_instance.test_insert(AsyncMock())
    await test_instance.test_insert_many(AsyncMock())
    await test_instance.test_update(AsyncMock())
    await test_instance.test_delete(AsyncMock())
    await test_instance.test_count(AsyncMock())
    await test_instance.test_aggregate(AsyncMock())
    await test_instance.test_transaction(AsyncMock())
    with pytest.raises(Exception):
        await test_instance.test_transaction_exception(AsyncMock())
