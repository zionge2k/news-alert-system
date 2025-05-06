"""
MongoDB repository base implementation.

This module provides the MongoDB implementation of the Repository interface.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from infra.database.repository.base import Repository

T = TypeVar("T", bound=BaseModel)
ID = TypeVar("ID")


class MongoRepository(Repository[T, ID]):
    """
    MongoDB implementation of the Repository interface.

    This implementation uses a MongoDB database to store and retrieve entities.
    """

    def __init__(self, database, collection_name: str, model_class: Type[T]):
        """
        Initialize the MongoDB repository.

        Args:
            database: The MongoDB database instance
            collection_name: The name of the collection to use
            model_class: The pydantic model class for the entity
        """
        self.db = database
        self.collection_name = collection_name
        self.model_class = model_class

    async def find_by_id(self, id: ID) -> Optional[T]:
        """
        Find an entity by its ID.

        Args:
            id: The ID of the entity to find

        Returns:
            The entity if found, None otherwise
        """
        doc = await self.db.find_one(self.collection_name, {"_id": id})
        if doc:
            return self.model_class.model_validate(doc)
        return None

    async def find_all(self) -> List[T]:
        """
        Find all entities.

        Returns:
            A list of all entities
        """
        docs = await self.db.find(self.collection_name, {})
        return [self.model_class.model_validate(doc) for doc in docs]

    async def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Find entities matching the given criteria.

        Args:
            criteria: Dictionary of field name to value mappings to match

        Returns:
            A list of entities matching the criteria
        """
        docs = await self.db.find(self.collection_name, criteria)
        return [self.model_class.model_validate(doc) for doc in docs]

    async def save(self, entity: T) -> T:
        """
        Save an entity (create or update).

        Args:
            entity: The entity to save

        Returns:
            The saved entity with any updates (e.g., generated ID)
        """
        data = entity.model_dump(exclude_unset=True)
        entity_id = data.get("id") or data.get("_id")

        if entity_id:
            # Update existing entity
            await self.db.update(
                self.collection_name, {"_id": entity_id}, {"$set": data}, upsert=True
            )
        else:
            # Create new entity
            result = await self.db.insert(self.collection_name, data)
            # Set the ID on the entity if it's a string result
            if isinstance(result, str):
                data["_id"] = result

        return self.model_class.model_validate(data)

    async def save_all(self, entities: List[T]) -> List[T]:
        """
        Save multiple entities.

        Args:
            entities: The entities to save

        Returns:
            The saved entities with any updates
        """
        saved_entities = []
        for entity in entities:
            saved_entity = await self.save(entity)
            saved_entities.append(saved_entity)
        return saved_entities

    async def delete(self, entity: T) -> None:
        """
        Delete an entity.

        Args:
            entity: The entity to delete
        """
        data = entity.model_dump()
        entity_id = data.get("id") or data.get("_id")
        if entity_id:
            await self.delete_by_id(entity_id)

    async def delete_by_id(self, id: ID) -> None:
        """
        Delete an entity by its ID.

        Args:
            id: The ID of the entity to delete
        """
        await self.db.delete(self.collection_name, {"_id": id})

    async def count(self) -> int:
        """
        Count all entities.

        Returns:
            The number of entities
        """
        return await self.db.count(self.collection_name, {})
