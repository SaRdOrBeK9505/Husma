from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['telegram_id', 'full_name', 'telegram_username', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['telegram_id', 'full_name', 'telegram_username']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('telegram_id', 'password')}),
        ('Ma\'lumotlar', {'fields': ('full_name', 'telegram_username', 'phone', 'role')}),
        ('Huquqlar', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('telegram_id', 'full_name', 'role'),
        }),
    )