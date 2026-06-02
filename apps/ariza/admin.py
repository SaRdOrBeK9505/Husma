from django.contrib import admin
from .models import Ariza, ArizaMakler


class ArizaRieltorInline(admin.TabularInline):
    model = ArizaMakler
    extra = 0
    readonly_fields = ['rieltor', 'holat', 'korilgan_vaqt', 'created_at']


@admin.register(Ariza)
class ArizaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'hudud', 'ariza_turi',
        'xonalar_soni', 'narx_min', 'narx_max',
        'holat', 'created_at'
    ]
    list_filter = ['ariza_turi', 'xonalar_soni', 'holat', 'hudud']
    search_fields = ['user__full_name', 'user__telegram_username', 'telefon']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ArizaRieltorInline]


@admin.register(ArizaMakler)
class ArizaRieltorAdmin(admin.ModelAdmin):
    list_display = ['ariza', 'rieltor', 'holat', 'created_at']
    list_filter = ['holat']