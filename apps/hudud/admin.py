from django.contrib import admin
from .models import Hudud, Viloyat, MulkTuri


@admin.register(Viloyat)
class ViloyatAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'tartib', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['nomi']
    list_editable = ['tartib', 'is_active']


@admin.register(MulkTuri)
class MulkTuriAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'kod', 'tartib', 'is_active']
    list_filter = ['is_active']
    search_fields = ['nomi', 'kod']
    list_editable = ['tartib', 'is_active']


@admin.register(Hudud)
class HududAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'viloyat', 'shahar', 'is_active', 'created_at']
    list_filter = ['viloyat', 'is_active']
    search_fields = ['nomi', 'shahar']
    list_editable = ['is_active']
