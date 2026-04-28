from typing import Annotated

from pydantic import BaseModel, BeforeValidator


def normalize_tgt(target_minions: list | str) -> list[str]:
    if isinstance(target_minions, list):
        return [m for m in target_minions if str(m).strip()]
    return [m for m in str(target_minions).split(',') if m.strip()]


class TaskMetricEventMixin(BaseModel):
    tid: str
    jid: str
    master_id: str


class TaskReturnMetricEvent(TaskMetricEventMixin):
    minion_id: str
    job_status: str


TargetNormalized = Annotated[list[str], BeforeValidator(normalize_tgt)]

class TaskNewMetricEvent(TaskMetricEventMixin):
    tgt: TargetNormalized
