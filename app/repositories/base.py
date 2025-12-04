# app/repositories/base.py
"""
Base repository with common CRUD operations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from pymongo.errors import ConnectionFailure, OperationFailure, PyMongoError

from app.core.exceptions import DatabaseOperationError
from app.core.logging_config import LogConfig

logger = LogConfig.get_logger()

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository providing common database operations.

    This class implements the Repository pattern, abstracting database
    operations and providing a consistent interface for data access.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Initialize repository with collection.

        Args:
            collection: MongoDB collection instance
        """
        self._collection = collection

    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Get the underlying collection."""
        return self._collection

    async def find_one(
        self, query: Dict[str, Any], projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document matching the query.

        Args:
            query: MongoDB query filter
            projection: Optional fields to include/exclude

        Returns:
            Document if found, None otherwise

        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            result = await self._collection.find_one(query, projection=projection)
            if result and "_id" in result:
                result["_id"] = str(result["_id"])
            return result
        except ConnectionFailure as e:
            logger.error(
                "Database connection failed",
                extra={"event_type": "database_connection_error", "error": str(e)},
            )
            raise DatabaseOperationError("Database connection failed")
        except OperationFailure as e:
            logger.error(
                "Database operation failed",
                extra={"event_type": "database_operation_error", "error": str(e)},
            )
            raise DatabaseOperationError(f"Database query failed: {e}")

    async def find_many(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents matching the query.

        Args:
            query: MongoDB query filter
            projection: Optional fields to include/exclude
            limit: Maximum number of documents to return
            skip: Number of documents to skip

        Returns:
            List of matching documents

        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            cursor = self._collection.find(query, projection=projection)
            cursor = cursor.skip(skip).limit(limit)
            results = await cursor.to_list(length=limit)
            for doc in results:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            return results
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(
                "Database operation failed",
                extra={"event_type": "database_error", "error": str(e)},
            )
            raise DatabaseOperationError(f"Database query failed: {e}")

    async def insert_one(self, document: Dict[str, Any]) -> str:
        """
        Insert a single document.

        Args:
            document: Document to insert

        Returns:
            Inserted document ID as string

        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            result = await self._collection.insert_one(document)
            return str(result.inserted_id)
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(
                "Database insert failed",
                extra={"event_type": "database_error", "error": str(e)},
            )
            raise DatabaseOperationError(f"Database insert failed: {e}")

    async def update_one(
        self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False
    ) -> bool:
        """
        Update a single document.

        Args:
            query: MongoDB query filter
            update: Update operations
            upsert: Whether to insert if not found

        Returns:
            True if document was modified

        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            result = await self._collection.update_one(query, update, upsert=upsert)
            return result.modified_count > 0 or result.upserted_id is not None
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(
                "Database update failed",
                extra={"event_type": "database_error", "error": str(e)},
            )
            raise DatabaseOperationError(f"Database update failed: {e}")

    async def find_one_and_update(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Find and update a document atomically.

        Args:
            query: MongoDB query filter
            update: Update operations
            return_document: If True, return updated document

        Returns:
            Updated document if found

        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            result = await self._collection.find_one_and_update(
                query,
                update,
                return_document=ReturnDocument.AFTER if return_document else ReturnDocument.BEFORE,
            )
            if result and "_id" in result:
                result["_id"] = str(result["_id"])
            return result
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(
                "Database find_one_and_update failed",
                extra={"event_type": "database_error", "error": str(e)},
            )
            raise DatabaseOperationError(f"Database update failed: {e}")

    async def delete_one(self, query: Dict[str, Any]) -> bool:
        """
        Delete a single document.

        Args:
            query: MongoDB query filter

        Returns:
            True if document was deleted

        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            result = await self._collection.delete_one(query)
            return result.deleted_count > 0
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(
                "Database delete failed",
                extra={"event_type": "database_error", "error": str(e)},
            )
            raise DatabaseOperationError(f"Database delete failed: {e}")

    async def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the query.

        Args:
            query: Optional MongoDB query filter

        Returns:
            Number of matching documents

        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            return await self._collection.count_documents(query or {})
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(
                "Database count failed",
                extra={"event_type": "database_error", "error": str(e)},
            )
            raise DatabaseOperationError(f"Database count failed: {e}")

    async def exists(self, query: Dict[str, Any]) -> bool:
        """
        Check if a document exists.

        Args:
            query: MongoDB query filter

        Returns:
            True if document exists

        Raises:
            DatabaseOperationError: If database operation fails
        """
        result = await self.find_one(query, projection={"_id": 1})
        return result is not None
