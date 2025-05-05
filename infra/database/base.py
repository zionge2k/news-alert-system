"""
Database abstraction module.

This module defines the interface for all database implementations.
All concrete database implementations should inherit from `Database` class.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class Database(ABC):
    """Base abstract class for database implementations."""

    @abstractmethod
    async def connect(self) -> None:
        """
        Connect to the database.

        Raises:
            ConnectionError: If connection to the database fails.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the database.

        Raises:
            ConnectionError: If disconnection from the database fails.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def insert(
        self, collection: str, document: Dict[str, Any]
    ) -> Union[str, Dict[str, Any]]:
        """
        Insert a document into the specified collection.

        Args:
            collection: The name of the collection.
            document: The document to insert.

        Returns:
            The inserted document ID or the entire document with ID.

        Raises:
            Exception: If the insertion fails.
        """
        pass

    @abstractmethod
    async def insert_many(
        self, collection: str, documents: List[Dict[str, Any]]
    ) -> List[Union[str, Dict[str, Any]]]:
        """
        Insert multiple documents into the specified collection.

        Args:
            collection: The name of the collection.
            documents: The list of documents to insert.

        Returns:
            The list of inserted document IDs or documents with IDs.

        Raises:
            Exception: If the insertion fails.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def transaction(self):
        """
        Create a transaction context manager.

        Returns:
            A context manager for transaction execution.

        Raises:
            Exception: If the transaction creation fails.
        """
        pass
