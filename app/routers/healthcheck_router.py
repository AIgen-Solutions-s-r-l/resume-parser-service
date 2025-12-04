# app/routers/healthcheck_router.py
"""
Health check endpoint router.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.healthcheck import (
    HealthCheckResponse,
    HealthCheckRunner,
    HealthStatus,
    MongoDBHealthCheck,
)

router = APIRouter(tags=["healthcheck"])


@router.get(
    "/healthcheck",
    response_model=HealthCheckResponse,
    responses={
        200: {"description": "All health checks passed"},
        503: {"description": "One or more health checks failed"},
    },
)
async def health_check() -> JSONResponse:
    """
    Perform health checks on service dependencies.

    Returns:
        Health check results for all registered checks.
    """
    runner = HealthCheckRunner()
    runner.add(MongoDBHealthCheck())

    result = await runner.run()

    status_code = (
        status.HTTP_200_OK
        if result.status == HealthStatus.HEALTHY
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=status_code,
        content=result.model_dump(),
    )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"},
    },
)
async def health() -> JSONResponse:
    """
    Simple health endpoint (alias for /healthcheck).

    Returns:
        Health check results.
    """
    return await health_check()


@router.get(
    "/ready",
    responses={
        200: {"description": "Service is ready to accept requests"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness() -> JSONResponse:
    """
    Kubernetes readiness probe endpoint.

    Checks if the service is ready to accept traffic.

    Returns:
        Readiness status.
    """
    runner = HealthCheckRunner()
    runner.add(MongoDBHealthCheck())

    result = await runner.run()

    if result.status == HealthStatus.HEALTHY:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready"},
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "not ready", "reason": "dependency check failed"},
    )


@router.get(
    "/live",
    responses={
        200: {"description": "Service is alive"},
    },
)
async def liveness() -> JSONResponse:
    """
    Kubernetes liveness probe endpoint.

    Simple check that the service process is running.

    Returns:
        Liveness status.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "alive"},
    )
