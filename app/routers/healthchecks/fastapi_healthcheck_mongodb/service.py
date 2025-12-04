import logging
from typing import List, Optional

from pymongo import AsyncMongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.routers.healthchecks.fastapi_healthcheck.service import HealthCheckBase
from app.routers.healthchecks.fastapi_healthcheck.enum import HealthCheckStatusEnum
from app.routers.healthchecks.fastapi_healthcheck.domain import HealthCheckInterface

logger = logging.getLogger(__name__)


class HealthCheckMongoDB(HealthCheckBase, HealthCheckInterface):
    """Health check implementation for MongoDB connections."""

    _connection_uri: str
    _message: str

    def __init__(
        self,
        connection_uri: str,
        alias: str,
        tags: Optional[List[str]] = None,
    ) -> None:
        self._connection_uri = connection_uri
        self._alias = alias
        self._tags = tags

    async def check_health(self) -> HealthCheckStatusEnum:
        """Check MongoDB connection health."""
        try:
            client: AsyncMongoClient = AsyncMongoClient(
                self._connection_uri,
                serverSelectionTimeoutMS=5000
            )
            if await client.server_info():
                return HealthCheckStatusEnum.HEALTHY
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during MongoDB health check: {e}")
        return HealthCheckStatusEnum.UNHEALTHY
