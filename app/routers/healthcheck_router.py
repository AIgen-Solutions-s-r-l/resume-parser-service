from fastapi import APIRouter, HTTPException, status
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.routers.healthchecks.fastapi_healthcheck import HealthCheckFactory, healthCheckRoute
from app.routers.healthchecks.fastapi_healthcheck_mongodb import HealthCheckMongoDB
from app.core.config import settings


router = APIRouter(tags=["healthcheck"])


@router.get(
    "/healthcheck",
    description="Health check endpoint",
    responses={
        200: {"description": "Health check passed"},
        503: {"description": "Service unavailable - health check failed"},
    },
)
async def health_check():
    """
    Perform health checks on service dependencies.

    Returns:
        Health check results for all registered checks.

    Raises:
        HTTPException: 503 if health checks fail
    """
    _healthChecks = HealthCheckFactory()
    _healthChecks.add(
        HealthCheckMongoDB(
            connection_uri=settings.mongodb,
            alias="mongo db",
            tags=("mongo", "db"),
        )
    )

    try:
        return await healthCheckRoute(factory=_healthChecks)
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {e}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check configuration error: {e}",
        )
