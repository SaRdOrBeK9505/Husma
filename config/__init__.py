"""
Django loyihasi ishga tushganda Celery'ni avtomatik yuklaymiz.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
