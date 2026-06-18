from django.contrib import admin
from .models import Ariza, ArizaMakler


class ArizaRieltorInline(admin.TabularInline):
    model = ArizaMakler
    extra = 0
    readonly_fields = ['rieltor', 'holat', 'korilgan_vaqt', 'created_at']


@admin.register(Ariza)
class ArizaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'mulk_turi', 'viloyat', 'hudud', 'ariza_turi',
        'xonalar_soni', 'narx_min', 'narx_max',
        'holat', 'created_at'
    ]
    list_filter = ['mulk_turi', 'viloyat', 'ariza_turi', 'xonalar_soni', 'holat', 'hudud']
    search_fields = ['user__full_name', 'user__telegram_username', 'telefon']
    readonly_fields = ['created_at', 'updated_at']
    # list_display dagi FK lar uchun N+1 oldini olish
    list_select_related = ['user', 'mulk_turi', 'viloyat', 'hudud']
    inlines = [ArizaRieltorInline]


@admin.register(ArizaMakler)
class ArizaRieltorAdmin(admin.ModelAdmin):
    list_display = ['ariza', 'rieltor', 'holat', 'created_at']
    list_filter = ['holat']
    list_select_related = ['ariza', 'rieltor']