# app/core/healthcheck.py
"""
Consolidated health check module.

Provides a simple, unified interface for service health checks.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class HealthStatus(str, Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheckResult(BaseModel):
    """Result of a single health check."""

    name: str
    status: HealthStatus = HealthStatus.HEALTHY
    duration_ms: float = 0.0
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Overall health check response."""

    status: HealthStatus = HealthStatus.HEALTHY
    total_duration_ms: float = 0.0
    checks: List[HealthCheckResult] = []
    timestamp: str = ""


class HealthCheck(ABC):
    """Abstract base class for health checks."""

    def __init__(self, name: str):
        """
        Initialize health check.

        Args:
            name: Display name for this check
        """
        self.name = name

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """
        Perform the health check.

        Returns:
            HealthCheckResult with status and details
        """
        pass


class MongoDBHealthCheck(HealthCheck):
    """Health check for MongoDB connection."""

    def __init__(self, name: str = "mongodb"):
        """
        Initialize MongoDB health check.

        Args:
            name: Display name for this check
        """
        super().__init__(name)

    async def check(self) -> HealthCheckResult:
        """Check MongoDB connection health."""
        from app.core.dependencies import DatabaseManager

        start_time = datetime.now()

        try:
            db_manager = DatabaseManager.get_instance()

            if not db_manager.is_connected:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    duration_ms=0.0,
                    error="Database not connected",
                )

            # Ping the database
            await db_manager.client.admin.command("ping")

            duration = datetime.now() - start_time
            duration_ms = duration.total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                duration_ms=round(duration_ms, 2),
                details={"database": db_manager.database.name},
            )

        except Exception as e:
            duration = datetime.now() - start_time
            duration_ms = duration.total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                duration_ms=round(duration_ms, 2),
                error=str(e),
            )


class HealthCheckRunner:
    """Runner for executing multiple health checks."""

    def __init__(self):
        """Initialize the health check runner."""
        self._checks: List[HealthCheck] = []

    def add(self, check: HealthCheck) -> "HealthCheckRunner":
        """
        Add a health check.

        Args:
            check: Health check to add

        Returns:
            Self for chaining
        """
        self._checks.append(check)
        return self

    async def run(self) -> HealthCheckResponse:
        """
        Run all health checks.

        Returns:
            HealthCheckResponse with aggregated results
        """
        start_time = datetime.now()
        results: List[HealthCheckResult] = []
        overall_status = HealthStatus.HEALTHY

        for check in self._checks:
            result = await check.check()
            results.append(result)

            # Update overall status
            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

        total_duration = datetime.now() - start_time
        total_duration_ms = total_duration.total_seconds() * 1000

        return HealthCheckResponse(
            status=overall_status,
            total_duration_ms=round(total_duration_ms, 2),
            checks=results,
            timestamp=datetime.now().isoformat(),
        )


def create_default_health_runner() -> HealthCheckRunner:
    """
    Create a health check runner with default checks.

    Returns:
        HealthCheckRunner with MongoDB check
    """
    runner = HealthCheckRunner()
    runner.add(MongoDBHealthCheck())
    return runner
