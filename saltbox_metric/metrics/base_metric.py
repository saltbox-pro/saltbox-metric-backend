import abc
import re

import redis.asyncio as redis
from prometheus_client import CollectorRegistry
from prometheus_client.metrics import MetricWrapperBase

from saltbox_metric.metrics.types import MessageDataType, RedisKeyTTL


class BaseMetric(abc.ABC):
    """
    A base class for handling prometheus metrics

    Attributes
    ----------
        - registry: Registry of acceptable metrics
        - name: Metric name
        - desc: Description of the metric
        - redis_client: Redis client
        - labels: Labels displayed in Grafana UI
    """

    def __init__(
        self,
        registry: CollectorRegistry,
        name: str,
        desc: str,
        redis_client: redis.Redis,
        labels: list[str] | None,
        redis_key_ttl: RedisKeyTTL = 172800
    ) -> None:
        self.registry = registry
        self.name = name
        self.desc = desc
        self._labels = labels
        self.redis_client = redis_client
        self.metric = self._create()
        self.redis_key_ttl = redis_key_ttl

    @property
    @abc.abstractmethod
    def _tag_pattern(self) -> re.Pattern: ...

    @property
    def tag_pattern(self) -> re.Pattern:
        return self._tag_pattern

    def can_handle(self, tag: str) -> bool:
        """
        Determine this metric should process an event with the given tag

        Parameters
        ----------
            - tag: The event tag from the salt bus (e.g., 'salt/job/<jid>/...')
        """
        return bool(self.tag_pattern.match(tag))

    @property
    @abc.abstractmethod
    def labels(self) -> list[str]:
        """
        Displayed metric labels on the Grafana side

        Returns
        -------
            - list[str]: List of metric labels
        """
        ...

    @abc.abstractmethod
    def _create(self) -> MetricWrapperBase:
        """
        Creates Prometheus metrics

        Returns
        -------
            - MetricWrapperBase: Specific impl of the Prometheus metric
        """
        ...

    @abc.abstractmethod
    async def aggregate(self, tag: str, data: MessageDataType) -> None: ...
