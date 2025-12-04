from abc import ABC, abstractmethod
from typing import List, Optional
from .enum import HealthCheckStatusEnum


class HealthCheckInterface(ABC):
    """Abstract base class for health check implementations."""

    _connectionUri: str
    _alias: str
    _tags: Optional[List[str]]

    @abstractmethod
    def setConnectionUri(self, value: str) -> None:
        """ConnectionUri will be the value that is requested to check the health of an endpoint."""
        pass

    @abstractmethod
    def setName(self, value: str) -> None:
        """The Name is the friendly name of the health object."""
        pass

    @abstractmethod
    def getService(self) -> str:
        """The Service is a definition of what kind of endpoint we are checking on."""
        pass

    @abstractmethod
    def getTags(self) -> List[str]:
        """Return list of tags associated with this health check."""
        pass

    @abstractmethod
    async def check_health(self) -> HealthCheckStatusEnum:
        """Requests data from the endpoint to validate health."""
        pass

    # Backward compatibility alias
    async def __checkHealth__(self) -> HealthCheckStatusEnum:
        """Deprecated: Use check_health instead."""
        return await self.check_health()
