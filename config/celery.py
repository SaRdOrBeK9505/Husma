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
    # Har 15 daqiqada: to'lov kutilayotgan obunalarni bekor qilish
    'check-pending-subscriptions': {
        'task': 'apps.obuna.tasks.bekor_qilish_kutilayotgan_obunalar',
        'schedule': crontab(minute='*/15'),
    },
    # Har kuni 10:00 da: tugagan obunalar va bepul muddatlar uchun xabarnoma
    'notify-expired-subscriptions': {
        'task': 'apps.obuna.tasks.obuna_tugash_xabarnomasi',
        'schedule': crontab(hour=10, minute=0),
    },
    # Har kuni 09:00 da: 3 kun ichida tugaydigan obunalar uchun eslatma
    'remind-expiring-subscriptions': {
        'task': 'apps.obuna.tasks.obuna_tugashidan_oldin_eslatma',
        'schedule': crontab(hour=9, minute=0),
        'kwargs': {'kunlar': 3},  # 3 kun oldin eslatma
    },
}
