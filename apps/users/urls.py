from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    TelegramAuthView,
    MeView,
    RieltorLoginView,
    RieltorFaollikView,
    RieltorOTPSorovView,
    RieltorOTPVerifyView,
)

urlpatterns = [
    # ===== USER AUTH =====
    path('auth/telegram/', TelegramAuthView.as_view(), name='telegram-auth'),

    # ===== RIELTOR REGISTER (OTP) =====
    path('auth/rieltor/otp-sorov/', RieltorOTPSorovView.as_view(), name='rieltor-otp-sorov'),
    path('auth/rieltor/otp-verify/', RieltorOTPVerifyView.as_view(), name='rieltor-otp-verify'),

    # ===== RIELTOR LOGIN =====
    # path('auth/rieltor/login/', RieltorLoginView.as_view(), name='rieltor-login'),
    path('auth/rieltor/faollik/', RieltorFaollikView.as_view(), name='rieltor-faollik'),

    # ===== UMUMIY =====
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/me/', MeView.as_view(), name='me'),
    # statistika/ endpoint settings.urls ga ko'chirildi (UserStatistikaView)
]
