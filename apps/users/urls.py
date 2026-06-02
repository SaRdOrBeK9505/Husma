from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    TelegramAuthView,
    MeView,
    StatistikaView,
    RieltorRoliSorovView,
    RieltorRegisterView,
    RieltorLoginView,
    RieltorVerifyHolatView,
)

urlpatterns = [
    # ===== USER AUTH (Telegram) =====
    path('auth/telegram/', TelegramAuthView.as_view(), name='telegram-auth'),
    path('auth/rieltor-sorovi/', RieltorRoliSorovView.as_view(), name='rieltor-sorovi'),

    # ===== RIELTOR AUTH (Username + Parol) =====
    path('auth/rieltor/register/', RieltorRegisterView.as_view(), name='rieltor-register'),
    path('auth/rieltor/login/', RieltorLoginView.as_view(), name='rieltor-login'),
    path('auth/rieltor/verify-holat/', RieltorVerifyHolatView.as_view(), name='rieltor-verify-holat'),

    # ===== UMUMIY =====
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/me/', MeView.as_view(), name='me'),
    path('statistika/', StatistikaView.as_view(), name='statistika'),
]
