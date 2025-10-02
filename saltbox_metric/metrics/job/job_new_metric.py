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
        logger.debug('Aggregating new job metrics: %s', jid)

        redis_key = f'job:{jid}{"-t" + tid if tid else ""}:new_time'
        logger.debug(redis_key)

        async with self.redis_client.pipeline() as pipe:
            pipe.set(name=redis_key, value=datetime.fromisoformat(data['stamp']).timestamp())
            pipe.expire(name=redis_key, time=60 * 60 * 24 * 7)

            await pipe.execute()

        self.metric.labels(
            master=data['master_id'],
            fun=data['fun'],
        ).inc()  # type: ignore[attr-defined]
