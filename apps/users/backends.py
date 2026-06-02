from django.contrib.auth.backends import ModelBackend
from .models import CustomUser


class TelegramIDBackend(ModelBackend):
    """Telegram ID (raqam) bilan login"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(telegram_id=int(username))
            if user.check_password(password):
                return user
        except (CustomUser.DoesNotExist, ValueError, TypeError):
            return None