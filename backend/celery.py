from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(['myapp'])

app.conf.update(
    worker_max_tasks_per_child=100,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    task_acks_late=True,
)
app.conf.beat_schedule = {
    'clean-old-simulations': {
        'task': 'myapp.tasks.maintenance_tasks.clean_old_simulations',
        'schedule': 86400*2,
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')