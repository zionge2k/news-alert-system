"""
Repository pattern interfaces.

This module provides abstract repository interfaces.
The repository pattern abstracts the data access layer and provides a more
object-oriented view of the persistence layer.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
ID = TypeVar("ID")


class Repository(Generic[T, ID], ABC):
    """
    Generic repository interface for CRUD operations.

    Type parameters:
        T: The entity type this repository manages, must be a Pydantic model
        ID: The type of the entity's ID (str, int, etc.)
    """

    @abstractmethod
    async def find_by_id(self, id: ID) -> Optional[T]:
        """
        Find an entity by its ID.

        Args:
            id: The ID of the entity to find

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_all(self) -> List[T]:
        """
        Find all entities.

        Returns:
            A list of all entities
        """
        pass

    @abstractmethod
    async def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Find entities matching the given criteria.

        Args:
            criteria: Dictionary of field name to value mappings to match

        Returns:
            A list of entities matching the criteria
        """
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        Save an entity (create or update).

        Args:
            entity: The entity to save

        Returns:
            The saved entity with any updates (e.g., generated ID)
        """
        pass

    @abstractmethod
    async def save_all(self, entities: List[T]) -> List[T]:
        """
        Save multiple entities.

        Args:
            entities: The entities to save

        Returns:
            The saved entities with any updates
        """
        pass

    @abstractmethod
    async def delete(self, entity: T) -> None:
        """
        Delete an entity.

        Args:
            entity: The entity to delete
        """
        pass

    @abstractmethod
    async def delete_by_id(self, id: ID) -> None:
        """
        Delete an entity by its ID.

        Args:
            id: The ID of the entity to delete
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Count all entities.

        Returns:
            The number of entities
        """
        pass
