import re
from datetime import datetime

from prometheus_client import Counter

from saltbox_metric.config import logger
from saltbox_metric.metrics.job.base_job_metric import BaseJobMetric
from saltbox_metric.metrics.types import MessageDataType


class JobNewMetric(BaseJobMetric):

    _tag_pattern = re.compile(r'^metrics:new_job$')

    @property
    def labels(self) -> list[str]:
        return ['master', 'fun']

    def _create(self) -> Counter:
        return Counter(name=self.name, documentation=self.desc, labelnames=self.labels, registry=self.registry)

    async def _aggregate(self, jid: str, tid: str | None, data: MessageDataType) -> None:
        redis_key = f'job:{jid}{"-t" + tid if tid else ""}:new_time'
        formatted_time: float = datetime.fromisoformat(data['stamp']).timestamp()
        logger.debug("Aggregating new job metrics: '%s' | KEY: '%s'", jid, redis_key)
        await self.redis_client.set(name=redis_key, value=formatted_time, ex=60)
        self.metric.labels(
            master=data['master_id'],
            fun=data['fun'],
        ).inc()  # type: ignore[attr-defined]
