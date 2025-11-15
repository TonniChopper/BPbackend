from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(['myapp'])

# Import constants
from myapp.constants import (
    CELERY_WORKER_MAX_TASKS,
    CELERY_TASK_TIME_LIMIT,
    CELERY_TASK_SOFT_TIME_LIMIT,
    CELERY_BEAT_CLEAN_INTERVAL,
)

app.conf.update(
    worker_max_tasks_per_child=CELERY_WORKER_MAX_TASKS,
    task_time_limit=CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=CELERY_TASK_SOFT_TIME_LIMIT,
    task_acks_late=True,
)

app.conf.beat_schedule = {
    'clean-old-simulations': {
        'task': 'myapp.tasks.maintenance_tasks.clean_old_simulations',
        'schedule': CELERY_BEAT_CLEAN_INTERVAL,
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')