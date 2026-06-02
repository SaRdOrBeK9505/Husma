from django.contrib import admin
from .models import Hudud


@admin.register(Hudud)
class HududAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'shahar', 'is_active', 'created_at']
    list_filter = ['shahar', 'is_active']
    search_fields = ['nomi', 'shahar']
    list_editable = ['is_active']