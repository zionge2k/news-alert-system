"""
MongoDB implementation of the Database interface.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

import motor.motor_asyncio
import pymongo
from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError

from infra.database.base import Database

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MongoDB(Database):
    """MongoDB implementation of the Database interface."""

    def __init__(
        self,
        uri: str,
        database: str,
        max_pool_size: int = 10,
        min_pool_size: int = 0,
        max_idle_time_ms: int = 30000,
        connect_timeout_ms: int = 20000,
        server_selection_timeout_ms: int = 20000,
        **kwargs,
    ):
        """
        Initialize MongoDB connection.

        Args:
            uri: MongoDB connection URI.
            database: Database name.
            max_pool_size: Maximum connections in the connection pool.
            min_pool_size: Minimum connections in the connection pool.
            max_idle_time_ms: Maximum idle time for a connection in ms.
            connect_timeout_ms: Timeout for initial connection to MongoDB in ms.
            server_selection_timeout_ms: Timeout for server selection in ms.
            **kwargs: Additional connection arguments.

        Raises:
            ConnectionError: If connection to MongoDB fails.
        """
        self._uri = uri
        self._database_name = database
        self._connection_params = {
            "maxPoolSize": max_pool_size,
            "minPoolSize": min_pool_size,
            "maxIdleTimeMS": max_idle_time_ms,
            "connectTimeoutMS": connect_timeout_ms,
            "serverSelectionTimeoutMS": server_selection_timeout_ms,
            **kwargs,
        }
        self._client = None
        self._db = None

    async def connect(self) -> None:
        """
        Connect to MongoDB.

        Raises:
            ConnectionError: If connection to MongoDB fails.
        """
        try:
            if self._client is None:
                self._client = motor.motor_asyncio.AsyncIOMotorClient(
                    self._uri, **self._connection_params
                )
                # Force connection to verify it's working
                await self._client.admin.command("ping")
                self._db = self._client[self._database_name]
                logger.info(f"Connected to MongoDB database: {self._database_name}")
            return self._db
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while connecting to MongoDB: {e}")
            raise ConnectionError(f"Unexpected error while connecting to MongoDB: {e}")

    async def disconnect(self) -> None:
        """
        Disconnect from MongoDB.

        Raises:
            ConnectionError: If disconnection from MongoDB fails.
        """
        try:
            if self._client:
                self._client.close()
                self._client = None
                self._db = None
                logger.info("Disconnected from MongoDB")
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {e}")
            raise ConnectionError(f"Error disconnecting from MongoDB: {e}")

    async def find(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find documents in the specified collection that match the query.

        Args:
            collection: The name of the collection.
            query: The query criteria.
            projection: The fields to include or exclude from the result.
            sort: The sort order.
            limit: The maximum number of documents to return.
            skip: The number of documents to skip.

        Returns:
            A list of documents that match the query.

        Raises:
            Exception: If the query fails.
        """
        try:
            if not self._db:
                await self.connect()

            cursor = self._db[collection].find(query, projection)

            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)

            return await cursor.to_list(length=None)
        except PyMongoError as e:
            logger.error(f"MongoDB find error: {e}")
            raise Exception(f"MongoDB find error: {e}")

    async def find_one(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document that matches the query.

        Args:
            collection: The name of the collection.
            query: The query criteria.
            projection: The fields to include or exclude from the result.

        Returns:
            The document that matches the query or None if no document matches.

        Raises:
            Exception: If the query fails.
        """
        try:
            if not self._db:
                await self.connect()

            return await self._db[collection].find_one(query, projection)
        except PyMongoError as e:
            logger.error(f"MongoDB find_one error: {e}")
            raise Exception(f"MongoDB find_one error: {e}")

    async def insert(
        self, collection: str, document: Dict[str, Any]
    ) -> Union[str, Dict[str, Any]]:
        """
        Insert a document into the specified collection.

        Args:
            collection: The name of the collection.
            document: The document to insert.

        Returns:
            The inserted document ID.

        Raises:
            Exception: If the insertion fails.
        """
        try:
            if not self._db:
                await self.connect()

            result = await self._db[collection].insert_one(document)
            return str(result.inserted_id)
        except DuplicateKeyError as e:
            logger.error(f"MongoDB duplicate key error: {e}")
            raise Exception(f"Document with the same key already exists: {e}")
        except PyMongoError as e:
            logger.error(f"MongoDB insert error: {e}")
            raise Exception(f"MongoDB insert error: {e}")

    async def insert_many(
        self, collection: str, documents: List[Dict[str, Any]]
    ) -> List[Union[str, Dict[str, Any]]]:
        """
        Insert multiple documents into the specified collection.

        Args:
            collection: The name of the collection.
            documents: The list of documents to insert.

        Returns:
            The list of inserted document IDs.

        Raises:
            Exception: If the insertion fails.
        """
        try:
            if not self._db:
                await self.connect()

            result = await self._db[collection].insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except DuplicateKeyError as e:
            logger.error(f"MongoDB duplicate key error: {e}")
            raise Exception(f"Document with the same key already exists: {e}")
        except PyMongoError as e:
            logger.error(f"MongoDB insert_many error: {e}")
            raise Exception(f"MongoDB insert_many error: {e}")

    async def update(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> Dict[str, Any]:
        """
        Update documents in the specified collection that match the query.

        Args:
            collection: The name of the collection.
            query: The query criteria.
            update: The update operations to apply.
            upsert: If True, create a new document if no documents match the query.

        Returns:
            Information about the update operation result.

        Raises:
            Exception: If the update fails.
        """
        try:
            if not self._db:
                await self.connect()

            result = await self._db[collection].update_one(query, update, upsert=upsert)
            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            }
        except PyMongoError as e:
            logger.error(f"MongoDB update error: {e}")
            raise Exception(f"MongoDB update error: {e}")

    async def delete(self, collection: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete documents in the specified collection that match the query.

        Args:
            collection: The name of the collection.
            query: The query criteria.

        Returns:
            Information about the delete operation result.

        Raises:
            Exception: If the deletion fails.
        """
        try:
            if not self._db:
                await self.connect()

            result = await self._db[collection].delete_many(query)
            return {"deleted_count": result.deleted_count}
        except PyMongoError as e:
            logger.error(f"MongoDB delete error: {e}")
            raise Exception(f"MongoDB delete error: {e}")

    async def count(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Count documents in the specified collection that match the query.

        Args:
            collection: The name of the collection.
            query: The query criteria.

        Returns:
            The number of documents that match the query.

        Raises:
            Exception: If the counting fails.
        """
        try:
            if not self._db:
                await self.connect()

            return await self._db[collection].count_documents(query)
        except PyMongoError as e:
            logger.error(f"MongoDB count error: {e}")
            raise Exception(f"MongoDB count error: {e}")

    async def aggregate(
        self, collection: str, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Perform an aggregation on the specified collection.

        Args:
            collection: The name of the collection.
            pipeline: The aggregation pipeline.

        Returns:
            The result of the aggregation.

        Raises:
            Exception: If the aggregation fails.
        """
        try:
            if not self._db:
                await self.connect()

            cursor = self._db[collection].aggregate(pipeline)
            return await cursor.to_list(length=None)
        except PyMongoError as e:
            logger.error(f"MongoDB aggregate error: {e}")
            raise Exception(f"MongoDB aggregate error: {e}")

    @asynccontextmanager
    async def transaction(self):
        """
        Create a transaction context manager.

        Yields:
            A MongoDB client session.

        Raises:
            Exception: If the transaction creation or execution fails.
        """
        if not self._db:
            await self.connect()

        session = await self._client.start_session()
        try:
            await session.start_transaction()
            yield session
            await session.commit_transaction()
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"MongoDB transaction error: {e}")
            raise Exception(f"MongoDB transaction error: {e}")
        finally:
            await session.end_session()


# Default values
DEFAULT_URI = "mongodb://root:1234@localhost:27017"
DEFAULT_DB_NAME = "news_alert"


def create_mongodb_connection(
    uri: Optional[str] = None, database: Optional[str] = None, **kwargs
) -> MongoDB:
    """
    Create a MongoDB connection with environment variables or defaults.

    Args:
        uri: MongoDB connection URI. If None, uses MONGODB_URL env var or default.
        database: Database name. If None, uses MONGODB_DB_NAME env var or default.
        **kwargs: Additional connection parameters to pass to MongoDB constructor.

    Returns:
        A MongoDB instance.
    """
    # Get connection parameters from environment or defaults
    mongodb_uri = uri or os.getenv("MONGODB_URL", DEFAULT_URI)
    mongodb_db = database or os.getenv("MONGODB_DB_NAME", DEFAULT_DB_NAME)

    # Create and return the MongoDB instance
    return MongoDB(uri=mongodb_uri, database=mongodb_db, **kwargs)
