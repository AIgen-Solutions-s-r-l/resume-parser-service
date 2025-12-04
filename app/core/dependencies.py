# app/core/dependencies.py
"""
Dependency injection module for FastAPI.

Provides centralized dependency management for services, database connections,
and other shared resources.
"""
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Optional

from fastapi import Depends, Request

from app.core.config import Settings, settings


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached).

    Returns:
        Settings instance
    """
    return settings


def get_executor(request: Request) -> ThreadPoolExecutor:
    """
    Get the shared ThreadPoolExecutor from app state.

    Args:
        request: FastAPI request object

    Returns:
        ThreadPoolExecutor instance
    """
    return request.app.state.executor


class DatabaseManager:
    """
    Manages database connections with proper lifecycle.

    This class handles MongoDB connection initialization, health checks,
    and cleanup. It's designed to be used with FastAPI's lifespan.
    """

    _instance: Optional["DatabaseManager"] = None

    def __init__(self):
        from motor.motor_asyncio import AsyncIOMotorClient

        self._client: Optional[AsyncIOMotorClient] = None
        self._database = None
        self._is_connected = False

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """Get singleton instance of DatabaseManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect(self) -> None:
        """
        Initialize database connection.

        Raises:
            ConnectionError: If connection fails
        """
        from motor.motor_asyncio import AsyncIOMotorClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

        from app.core.logging_config import LogConfig

        logger = LogConfig.get_logger()

        try:
            self._client = AsyncIOMotorClient(
                settings.mongodb,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                retryWrites=True,
                w="majority",
                connectTimeoutMS=5000,
            )

            # Verify connection
            await self._client.admin.command("ping")

            self._database = self._client[settings.mongodb_database]
            self._is_connected = True

            logger.info(
                "MongoDB connection established",
                extra={
                    "event_type": "mongodb_connected",
                    "database": settings.mongodb_database,
                },
            )

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(
                "MongoDB connection failed",
                extra={
                    "event_type": "mongodb_error",
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                },
            )
            await self.disconnect()
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected

    @property
    def database(self):
        """Get database instance."""
        if not self._is_connected:
            raise RuntimeError("Database not connected")
        return self._database

    @property
    def client(self):
        """Get client instance."""
        if not self._is_connected:
            raise RuntimeError("Database not connected")
        return self._client

    def get_collection(self, name: str):
        """
        Get a collection by name.

        Args:
            name: Collection name

        Returns:
            AsyncIOMotorCollection instance
        """
        return self.database.get_collection(name)


def get_database_manager() -> DatabaseManager:
    """
    Get the database manager instance.

    Returns:
        DatabaseManager singleton instance
    """
    return DatabaseManager.get_instance()


async def get_resume_collection(
    db_manager: DatabaseManager = Depends(get_database_manager),
):
    """
    Get the resumes collection.

    Args:
        db_manager: Database manager instance

    Returns:
        AsyncIOMotorCollection for resumes
    """
    return db_manager.get_collection("resumes")
