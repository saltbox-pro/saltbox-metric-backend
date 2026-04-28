from saltbox_metric.metrics.event.event_payload_size_metric import EventPayloadSizeMetric
from saltbox_metric.metrics.event.tagged_event_metric import TaggedEventCountMetric
from saltbox_metric.metrics.job.job_new_metric import JobNewMetric
from saltbox_metric.metrics.job.job_return_metric import JobReturnMetric
from saltbox_metric.metrics.task.task_metric import TaskMetric

METRIC_SPECIFICATIONS = [
    {
        'key': 'job_new',
        'class': JobNewMetric,
        'desc': 'Total number of new jobs received',
        'labels': JobNewMetric.labels
    },
    {
        'key': 'job_ret',
        'class': JobReturnMetric,
        'desc': 'Total number of job returns',
        'labels': JobReturnMetric.labels
    },
    {
        'key': 'event_total',
        'class': TaggedEventCountMetric,
        'desc': 'Total number of tagged events',
        'labels': TaggedEventCountMetric.labels
    },
    {
        'key': 'event_payload_size',
        'class': EventPayloadSizeMetric,
        'desc': 'Sum of payload sizes for all tagged events',
        'labels': EventPayloadSizeMetric.labels
    },
    {
        'key': 'task_status',
        'class': TaskMetric,
        'desc': 'Metrics related to the execution status of tasks',
        'labels': TaskMetric.labels
    },
]
