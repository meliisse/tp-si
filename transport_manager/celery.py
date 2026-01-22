import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transport_manager.settings')

app = Celery('transport_manager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Periodic tasks
app.conf.beat_schedule = {
    'send-daily-reports': {
        'task': 'apps.dashboard.tasks.send_daily_reports',
        'schedule': crontab(hour=8, minute=0),  # Every day at 8:00 AM
    },
    'cleanup-old-logs': {
        'task': 'apps.core.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2:00 AM
    },
    'update-shipment-statuses': {
        'task': 'apps.logistics.tasks.update_shipment_statuses',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
