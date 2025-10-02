import abc

from saltbox_metric.metrics.base_metric import BaseMetric
from saltbox_metric.metrics.types import MessageDataType


class BaseJobMetric(BaseMetric, abc.ABC):
    """
    A base metric class for handling salt job event
    """

    @abc.abstractmethod
    async def _aggregate(self, jid: str, tid: str | None, data: MessageDataType) -> None: ...

    async def aggregate(self, tag: str, data: MessageDataType) -> None:
        jid = data['jid']
        tid = data.get('tid', None)
        await self._aggregate(jid=jid, tid=tid, data=data)
