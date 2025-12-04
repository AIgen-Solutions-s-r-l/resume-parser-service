from datetime import datetime, timedelta
from typing import Any, Dict, List, Union

from .domain import HealthCheckInterface
from .enum import HealthCheckStatusEnum
from .model import HealthCheckEntityModel, HealthCheckModel


class HealthCheckFactory:
    """Factory for managing and running health checks."""

    _health_items: List[HealthCheckInterface]
    _health: Union[HealthCheckModel, Dict[str, Any]]
    _entity_start_time: datetime
    _entity_stop_time: datetime
    _total_start_time: datetime
    _total_stop_time: datetime

    def __init__(self) -> None:
        self._health_items = list()

    def add(self, item: HealthCheckInterface) -> None:
        """Add a health check item to the factory."""
        self._health_items.append(item)

    def _start_timer(self, entity_timer: bool) -> None:
        """Start timing for entity or total check."""
        if entity_timer:
            self._entity_start_time = datetime.now()
        else:
            self._total_start_time = datetime.now()

    def _stop_timer(self, entity_timer: bool) -> None:
        """Stop timing for entity or total check."""
        if entity_timer:
            self._entity_stop_time = datetime.now()
        else:
            self._total_stop_time = datetime.now()

    def _get_time_taken(self, entity_timer: bool) -> timedelta:
        """Calculate time taken for entity or total check."""
        if entity_timer:
            return self._entity_stop_time - self._entity_start_time
        return self._total_stop_time - self._total_start_time

    async def _dump_model(self, model: HealthCheckModel) -> Dict[str, Any]:
        """Convert health check model to dictionary for JSON serialization."""
        entities_list = []
        for entity in model.entities:
            entity.status = entity.status.value
            entity.timeTaken = str(entity.timeTaken)
            entities_list.append(dict(entity))

        model.entities = entities_list
        model.status = model.status.value
        model.totalTimeTaken = str(model.totalTimeTaken)

        return dict(model)

    async def check(self) -> Dict[str, Any]:
        """Run all health checks and return aggregated results."""
        self._health = HealthCheckModel()
        self._start_timer(False)

        for item in self._health_items:
            # Generate the model
            if not hasattr(item, "_tags"):
                item._tags = list()
            entity = HealthCheckEntityModel(
                alias=item._alias, tags=item._tags if item._tags else []
            )

            # Track how long the entity took to respond
            self._start_timer(True)
            entity.status = await item.check_health()
            self._stop_timer(True)
            entity.timeTaken = self._get_time_taken(True)

            # If we have one dependency unhealthy, the service is unhealthy
            if entity.status == HealthCheckStatusEnum.UNHEALTHY:
                self._health.status = HealthCheckStatusEnum.UNHEALTHY

            self._health.entities.append(entity)

        self._stop_timer(False)
        self._health.totalTimeTaken = self._get_time_taken(False)
        self._health = await self._dump_model(self._health)

        return self._health


class HealthCheckBase:
    def setConnectionUri(self, value: str) -> None:
        if value == "":
            raise Exception(f"{self._service} ConnectionUri is missing a value.")
        self._connectionUri = value

    def getConnectionUri(self) -> str:
        return self._connectionUri

    def setName(self, value: str) -> str:
        if not value:
            raise Exception("Missing a valid name.")
        self._name = value

    def getService(self) -> str:
        return self._service

    def getTags(self) -> List[str]:
        return self._tags

    def getAlias(self) -> str:
        return self._alias
