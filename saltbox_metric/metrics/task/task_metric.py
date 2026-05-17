import re

from prometheus_client import Gauge

from saltbox_metric.config import logger
from saltbox_metric.metrics.base_metric import BaseMetric
from saltbox_metric.metrics.task.task_schema import TaskNewMetricEvent, TaskReturnMetricEvent
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
            event_new = TaskNewMetricEvent.model_validate(data)
            await self._handle_new_task(event_new)
        elif tag == self._RET_TAG:
            event_ret = TaskReturnMetricEvent.model_validate(data)
            await self._handle_return_task(event_ret)

    async def _handle_new_task(self, event: TaskNewMetricEvent) -> None:
        log_msg = f'Mapping job task (jid={event.jid!r} | tid={event.tid!r}) to target minions: {event.tgt!r}'
        logger.debug(log_msg)

        self.metric.labels(
            master=event.master_id,
            status=self._STATUS_ON_PROCESS,
        ).inc()  # type: ignore[attr-defined] # ty: ignore[unresolved-attribute]

        async with self.redis_client.pipeline() as pipe:
            tgt_r_set_name = f'jid:{event.jid}:tgt'
            pipe.sadd(
                tgt_r_set_name,
                *event.tgt,
            )
            pipe.expire(tgt_r_set_name, self.redis_key_ttl)
            await pipe.execute()

    async def _handle_return_task(self, event: TaskReturnMetricEvent) -> None:

        async with self.redis_client.pipeline() as pipe:
            executed_r_name = f'jid:{event.jid}:executed'
            pipe.sadd(executed_r_name, event.minion_id)
            pipe.expire(executed_r_name, self.redis_key_ttl)

            mid_statuses_r_name = f'tid:{event.tid}:mid_statuses'
            pipe.hset(
                mid_statuses_r_name,
                event.minion_id,
                event.job_status,
            )
            pipe.expire(mid_statuses_r_name, self.redis_key_ttl)
            await pipe.execute()

        log_msg = (
            f'Extracted job(jid={event.jid!r} | tid={event.tid!r}) '
            f'status from mid={event.minion_id!r}: {event.job_status!r}'
        )
        logger.debug(log_msg)

        tgt_r_name = f'jid:{event.jid}:tgt'
        expected_executed_minions = await self.redis_client.smembers(tgt_r_name)

        executed_r_name = f'jid:{event.jid}:executed'
        received_executed_minions = await self.redis_client.smembers(executed_r_name)

        logger.debug(f'Expected minions: {expected_executed_minions} | Received: {received_executed_minions}')

        if len(expected_executed_minions) == len(received_executed_minions):
            task_status = await self._determine_task_status(tid=event.tid)

            task_status_r_name = f'tid:{event.tid}:task_status'
            previous_task_status = await self.redis_client.get(task_status_r_name)

            if previous_task_status and isinstance(previous_task_status, bytes):
                previous_task_status = previous_task_status.decode()

            logger.debug(f'Executed task status: {task_status} | Previous task status: {previous_task_status}')

            if previous_task_status and previous_task_status != self._STATUS_SUCCESS:
                self.metric.labels(
                    master=event.master_id,
                    status=previous_task_status,
                ).dec()  # type: ignore[attr-defined] # ty: ignore[unresolved-attribute]

            self.metric.labels(
                master=event.master_id,
                status=task_status,
            ).inc()  # type: ignore[attr-defined] # ty: ignore[unresolved-attribute]

            self.metric.labels(
                master=event.master_id,
                status=self._STATUS_ON_PROCESS,
            ).dec()  # type: ignore[attr-defined] # ty: ignore[unresolved-attribute]

            await self.redis_client.set(task_status_r_name, task_status, ex=self.redis_key_ttl)

    async def _determine_task_status(self, tid: str) -> str:
        r_name = f'tid:{tid}:mid_statuses'
        statuses: dict[str, bytes] = await self.redis_client.hgetall(r_name)

        unique_statuses = {s.decode() for s in statuses.values()}
        if unique_statuses == {self._STATUS_SUCCESS}:
            return self._STATUS_SUCCESS
        elif unique_statuses == {self._STATUS_FAILED}:
            return self._STATUS_FAILED
        return self._STATUS_PARTIAL_SUCCESS
