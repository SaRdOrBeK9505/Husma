from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    TelegramAuthView,
    MeView,
    RieltorFaollikView,
    RieltorOTPSorovView,
    RieltorOTPVerifyView,
    AdminLoginView,
    AdminMeView,
    AdminChangePasswordView,
)

urlpatterns = [
    # ===== USER AUTH =====
    path('auth/telegram/', TelegramAuthView.as_view(), name='telegram-auth'),

    # ===== RIELTOR REGISTER (OTP) =====
    path('auth/rieltor/otp-sorov/', RieltorOTPSorovView.as_view(), name='rieltor-otp-sorov'),
    path('auth/rieltor/otp-verify/', RieltorOTPVerifyView.as_view(), name='rieltor-otp-verify'),

    # ===== RIELTOR LOGIN (ishlatilmaydi, lekin qoldirildi) =====
    # path('auth/rieltor/login/', RieltorLoginView.as_view(), name='rieltor-login'),
    path('auth/rieltor/faollik/', RieltorFaollikView.as_view(), name='rieltor-faollik'),

    # ===== ADMIN AUTH =====
    path('admin/auth/login/', AdminLoginView.as_view(), name='admin-login'),
    path('admin/auth/me/', AdminMeView.as_view(), name='admin-me'),
    path('admin/auth/change-password/', AdminChangePasswordView.as_view(), name='admin-change-password'),

    # ===== UMUMIY =====
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/me/', MeView.as_view(), name='me'),
    # statistika/ endpoint settings.urls ga ko'chirildi (UserStatistikaView)
]
