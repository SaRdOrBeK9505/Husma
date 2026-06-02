from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'rieltor', 'yulduz', 'created_at']
    list_filter = ['yulduz']
    search_fields = ['user__full_name', 'rieltor__user__full_name']
    readonly_fields = ['created_at']
