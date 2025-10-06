import re

from prometheus_client import Gauge

from saltbox_metric.config import logger
from saltbox_metric.metrics.base_metric import BaseMetric
from saltbox_metric.metrics.types import MessageDataType


class TaskMetric(BaseMetric):
    """
    A metric for tracking the status of distributed tasks

    Collects and aggregates real-time information about tasks,
    including task creation, execution by minions, and completion status
    """

    _tag_pattern = re.compile(r'^metrics:task:(new_job|job_return)+$')
    _NEW_TAG = 'metrics:task:new_job'
    _RET_TAG = 'metrics:task:job_return'

    _STATUS_ON_PROCESS = 'on_process'
    _STATUS_SUCCESS = 'success'
    _STATUS_PARTIAL_SUCCESS = 'partial_success'
    _STATUS_FAILED = 'failed'

    @property
    def labels(self) -> list[str]:
        return ['master', 'status']

    def _create(self) -> Gauge:
        return Gauge(name=self.name, documentation=self.desc, labelnames=self.labels, registry=self.registry)

    async def aggregate(self, tag: str, data: MessageDataType) -> None:
        if tag == self._NEW_TAG:
            await self._handle_new_task(data=data)
        elif tag == self._RET_TAG:
            await self._handle_ret_task(data=data)

    async def _handle_new_task(self, data: MessageDataType) -> None:
        tid = data['tid']
        jid = data['jid']
        tgt = data['tgt']

        if isinstance(tgt, str):
            tgt = [minion for minion in tgt.split(',') if minion.strip()]
        else:
            tgt = list(tgt)

        logger.debug('Mapping job task (jid=%s | tid=%s) to target minions: %r', jid, tid, tgt)
        self.metric.labels(master=data['master_id'], status=self._STATUS_ON_PROCESS).inc()  # type: ignore[attr-defined]
        _ = await self.redis_client.sadd(f'jid:{jid}:tgt', *tgt)

    async def _handle_ret_task(self, data: MessageDataType) -> None:
        jid = data['jid']
        tid = data['tid']
        mid = data['minion_id']

        _ = await self.redis_client.sadd(f'jid:{jid}:executed', mid)

        job_status = data['job_status']
        _ = await self.redis_client.hset(f'tid:{tid}:mid_statuses', mid, job_status)
        logger.debug('Extracted job(jid=%s | tid=%s) status from mid=%s: %s', jid, tid, mid, job_status)

        expected_executed_minions = await self.redis_client.smembers(f'jid:{jid}:tgt')
        received_executed_minions = await self.redis_client.smembers(f'jid:{jid}:executed')
        logger.debug('Expected minions: %r | Received: %s', expected_executed_minions, received_executed_minions)

        if len(expected_executed_minions) == len(received_executed_minions):
            task_status = await self._determine_task_status(tid=tid)
            previous_task_status = await self.redis_client.get(f'tid:{tid}:task_status')

            if previous_task_status and isinstance(previous_task_status, bytes):
                previous_task_status = previous_task_status.decode()
            logger.debug('Executed task status: %s | Previous task status: %s', task_status, previous_task_status)

            if previous_task_status and previous_task_status != self._STATUS_SUCCESS:
                self.metric.labels(master=data['master_id'], status=previous_task_status).dec()  # type: ignore[attr-defined]
            self.metric.labels(master=data['master_id'], status=task_status).inc()  # type: ignore[attr-defined]

            self.metric.labels(master=data['master_id'], status=self._STATUS_ON_PROCESS).dec()  # type: ignore[attr-defined]
            await self.redis_client.set(f'tid:{tid}:task_status', task_status)

    async def _determine_task_status(self, tid: str) -> str:
        statuses: dict[str, bytes] = await self.redis_client.hgetall(f'tid:{tid}:mid_statuses')
        unique_statuses = {s.decode() for s in statuses.values()}
        if unique_statuses == {self._STATUS_SUCCESS}:
            return self._STATUS_SUCCESS
        elif unique_statuses == {self._STATUS_FAILED}:
            return self._STATUS_FAILED
        return self._STATUS_PARTIAL_SUCCESS
