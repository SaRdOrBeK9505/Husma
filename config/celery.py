"""
Celery sozlamalari — asinxron vazifalar uchun.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Django settings modulini o'rnatish
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('husma')

# Django settings dan celery sozlamalarini yuklash
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django app'laridan barcha tasks.py fayllarni avtomatik topish
app.autodiscover_tasks()

# Davriy vazifalar (Celery Beat)
app.conf.beat_schedule = {
    'check-pending-subscriptions': {
        'task': 'apps.obuna.tasks.bekor_qilish_kutilayotgan_obunalar',
        'schedule': crontab(minute='*/15'),  # Har 15 daqiqada
    },
}
