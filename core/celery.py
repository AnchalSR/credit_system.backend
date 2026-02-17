"""
Celery configuration for Credit Approval System.
"""

import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Read config from Django settings, namespace='CELERY'
# e.g., CELERY_BROKER_URL in settings.py → broker_url in Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in all installed apps
app.autodiscover_tasks()
