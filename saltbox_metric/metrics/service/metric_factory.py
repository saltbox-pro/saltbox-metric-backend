from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from exceptions import InvalidMetricClassError  # type: ignore[import-not-found]

from prometheus_client import CollectorRegistry
from redis import asyncio as aioredis

from saltbox_metric.metrics.base_metric import BaseMetric
from saltbox_metric.metrics.metric_specification import METRIC_SPECIFICATIONS


class MetricFactory:
    def __init__(
        self,
        registry: CollectorRegistry,
        redis_client: aioredis.Redis,
    ) -> None:
        self._registry = registry
        self._redis_client = redis_client
        self._instances: dict[str, BaseMetric] = {}

    def _create_metric(self, specification: dict[str, Any]) -> BaseMetric:
        metric_class = specification['class']
        if issubclass(metric_class, BaseMetric):
            key = specification['key']
            self._instances[key] = metric_class(
                registry=self._registry,
                name=key,
                desc=specification['desc'],
                labels=specification['labels'],
                redis_client=self._redis_client,
            )
        else:
            msg = f'Metric class {metric_class} does not extend BaseMetric class'
            raise InvalidMetricClassError(msg)
        return self._instances[specification['key']]

    def create_all(self) -> list[BaseMetric]:
        return [self._create_metric(specification=s) for s in METRIC_SPECIFICATIONS]
