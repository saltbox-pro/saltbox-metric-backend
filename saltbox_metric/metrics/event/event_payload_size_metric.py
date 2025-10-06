import re

from prometheus_client import Summary

from saltbox_metric.config import logger
from saltbox_metric.metrics.base_metric import BaseMetric
from saltbox_metric.metrics.types import MessageDataType


class EventPayloadSizeMetric(BaseMetric):

    _tag_pattern = re.compile(r'^metrics:salt_message$')

    @property
    def labels(self) -> list[str]:
        return ['master']

    def _create(self) -> Summary:
        return Summary(name=self.name, documentation=self.desc, labelnames=self.labels, registry=self.registry)

    async def aggregate(self, tag: str, data: MessageDataType) -> None:
        logger.debug('Aggregating payload size %s to master %s', data['payload_size'], data['master_id'])
        self.metric.labels(master=data['master_id']).observe(data['payload_size'])  # type: ignore[attr-defined]
