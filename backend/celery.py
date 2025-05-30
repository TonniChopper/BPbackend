from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Create Celery app
app = Celery('backend')

# Load settings from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks(['myapp'])

# Configure some important settings
app.conf.update(
    worker_max_tasks_per_child=100,
    task_time_limit=3600,  # 1 hour timeout for tasks
    task_soft_time_limit=3000,  # Soft timeout
    task_acks_late=True,  # Tasks acknowledged after execution
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