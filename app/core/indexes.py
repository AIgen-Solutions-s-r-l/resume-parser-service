# app/core/indexes.py
"""
Database index management for MongoDB.

Defines and creates indexes to optimize query performance.
"""
from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.core.logging_config import LogConfig

logger = LogConfig.get_logger()


# Index definitions for the resumes collection
RESUME_INDEXES: List[IndexModel] = [
    # Primary lookup index - most queries filter by user_id
    IndexModel(
        [("user_id", ASCENDING)],
        name="idx_user_id",
        unique=True,  # One resume per user
        background=True,
    ),
    # Compound index for user + version queries
    IndexModel(
        [("user_id", ASCENDING), ("version", ASCENDING)],
        name="idx_user_version",
        background=True,
    ),
    # Index for listing/sorting by creation date
    IndexModel(
        [("created_at", DESCENDING)],
        name="idx_created_at",
        background=True,
        sparse=True,  # Only index documents with this field
    ),
    # Index for updated_at for tracking changes
    IndexModel(
        [("updated_at", DESCENDING)],
        name="idx_updated_at",
        background=True,
        sparse=True,
    ),
]


async def ensure_indexes(database: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Ensure all required indexes exist on collections.

    Creates indexes if they don't exist. This operation is idempotent -
    existing indexes with the same specification are not recreated.

    Args:
        database: MongoDB database instance

    Returns:
        Dict with index creation results
    """
    results = {}

    # Create indexes on resumes collection
    try:
        collection = database.get_collection("resumes")
        created_indexes = await collection.create_indexes(RESUME_INDEXES)

        results["resumes"] = {
            "status": "success",
            "indexes_ensured": created_indexes,
        }

        logger.info(
            "Database indexes ensured",
            extra={
                "event_type": "indexes_created",
                "collection": "resumes",
                "indexes": created_indexes,
            },
        )

    except Exception as e:
        results["resumes"] = {
            "status": "error",
            "error": str(e),
        }
        logger.error(
            "Failed to create indexes",
            extra={
                "event_type": "index_creation_error",
                "collection": "resumes",
                "error": str(e),
            },
        )

    return results


async def list_indexes(database: AsyncIOMotorDatabase, collection_name: str) -> List[Dict[str, Any]]:
    """
    List all indexes on a collection.

    Args:
        database: MongoDB database instance
        collection_name: Name of the collection

    Returns:
        List of index specifications
    """
    collection = database.get_collection(collection_name)
    indexes = []

    async for index in collection.list_indexes():
        indexes.append(index)

    return indexes


async def drop_index(
    database: AsyncIOMotorDatabase, collection_name: str, index_name: str
) -> bool:
    """
    Drop a specific index from a collection.

    Args:
        database: MongoDB database instance
        collection_name: Name of the collection
        index_name: Name of the index to drop

    Returns:
        True if index was dropped
    """
    try:
        collection = database.get_collection(collection_name)
        await collection.drop_index(index_name)
        logger.info(
            "Index dropped",
            extra={
                "event_type": "index_dropped",
                "collection": collection_name,
                "index": index_name,
            },
        )
        return True
    except Exception as e:
        logger.error(
            "Failed to drop index",
            extra={
                "event_type": "index_drop_error",
                "collection": collection_name,
                "index": index_name,
                "error": str(e),
            },
        )
        return False
