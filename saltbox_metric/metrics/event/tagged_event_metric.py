import re

from prometheus_client import Summary

from saltbox_metric.config import logger
from saltbox_metric.metrics.base_metric import BaseMetric
from saltbox_metric.metrics.types import MessageDataType


class TaggedEventCountMetric(BaseMetric):
    """
    A metric that counts salt but events grouped by tag type
    and counts the msg size in bytes (e.g. job_ret, job_new, etc...)
    """

    _tag_pattern = re.compile(r'^metrics:salt_message$')

    @property
    def labels(self) -> list[str]:
        return ['master', 'tag']

    def _create(self) -> Summary:
        return Summary(name=self.name, documentation=self.desc, labelnames=self.labels, registry=self.registry)

    async def aggregate(self, tag: str, data: MessageDataType) -> None:
        logger.debug('Tagged event count: %s', data['tag'])

        self.metric.labels(master=data['master_id'], tag=data['tag_name']).observe(data['payload_size'])  # type: ignore[attr-defined]
