import re
from datetime import datetime

from prometheus_client import Gauge

from saltbox_metric.config import logger
from saltbox_metric.metrics.job.base_job_metric import BaseJobMetric
from saltbox_metric.metrics.types import MessageDataType


class JobReturnMetric(BaseJobMetric):
    _tag_pattern = re.compile(r'^metrics:job_return$')

    @property
    def labels(self) -> list[str]:
        return ['master', 'minion_id']

    def _create(self) -> Gauge:
        return Gauge(name=self.name, documentation=self.desc, labelnames=self.labels, registry=self.registry)

    async def _aggregate(self, jid: str, tid: str | None, data: MessageDataType) -> None:
        redis_key = f'job:{jid}{"-t" + tid if tid else ""}:new_time'
        job_creation_time = await self.redis_client.get(name=redis_key)

        if job_creation_time is not None:
            job_creation_time = float(job_creation_time)
            duration = await self._set_job_duration(job_creation_time=job_creation_time, data=data)
            logger.debug('Job %s processing time: %f seconds', jid, duration)
        else:
            logger.debug('Failed to extract job creation time from redis | jid=%s, tid=%s', jid, tid)

    async def _set_job_duration(self, job_creation_time: float, data: MessageDataType) -> float:
        job_creation_time = float(job_creation_time)
        job_return_time = datetime.fromisoformat(data['stamp']).timestamp()
        time_diff = job_return_time - job_creation_time

        self.metric.labels(
            master=data['master_id'],
            minion_id=data['minion_id'],
        ).set(value=time_diff)  # type: ignore[attr-defined]

        return time_diff
