import re

from prometheus_client import Summary

from saltbox_metric.config import logger
from saltbox_metric.metrics.base_metric import BaseMetric
from saltbox_metric.metrics.event.event_schema import PayloadSizeEventSchema
from saltbox_metric.metrics.types import MessageDataType


class EventPayloadSizeMetric(BaseMetric):

    _tag_pattern = re.compile(r'^metrics:salt_message$')

    @property
    def labels(self) -> list[str]:
        return ['master']

    def _create(self) -> Summary:
        return Summary(
            name=self.name,
            documentation=self.desc,
            labelnames=self.labels,
            registry=self.registry
        )

    async def aggregate(self, tag: str, data: MessageDataType) -> None:
        event = PayloadSizeEventSchema.model_validate(data)
        log_msg =(
            f'Aggregating payload size { event.payload_size!r } '
            f'to master { event.master_id!r }'
        )
        logger.debug(log_msg)
        self.metric.labels(master=event.master_id).observe(event.payload_size)  # type: ignore[attr-defined]
