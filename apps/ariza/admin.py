from django.contrib import admin
from django.utils.html import format_html
from .models import Ariza, ArizaMakler


class ArizaRieltorInline(admin.TabularInline):
    model = ArizaMakler
    extra = 0
    readonly_fields = ['rieltor', 'holat', 'korilgan_vaqt', 'created_at']


@admin.register(Ariza)
class ArizaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'mulk_turi', 'viloyat', 'hudud', 'ariza_turi_badge',
        'xonalar_soni', 'narx_diapazoni', 'valyuta',
        'holat_badge', 'created_at'
    ]
    list_filter = ['mulk_turi', 'viloyat', 'ariza_turi', 'xonalar_soni', 'holat', 'hudud']
    search_fields = ['user__full_name', 'user__telegram_username', 'telefon', 'ism']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['user', 'mulk_turi', 'viloyat', 'hudud']
    inlines = [ArizaRieltorInline]

    _ARIZA_TURI_RANG = {
        'ijara':        ('#1976d2', 'Ijaraga olish'),
        'sotib_olish':  ('#388e3c', 'Sotib olish'),
        'ijara_berish': ('#f57c00', 'Ijaraga berish'),
        'sotish':       ('#c62828', 'Sotish'),
    }

    _HOLAT_RANG = {
        'yangi':      ('#1976d2', 'Yangi'),
        'korilmoqda': ('#f57c00', "Ko'rilmoqda"),
        'yopilgan':   ('#757575', 'Yopilgan'),
    }

    @admin.display(description='Ariza turi', ordering='ariza_turi')
    def ariza_turi_badge(self, obj):
        rang, label = self._ARIZA_TURI_RANG.get(
            obj.ariza_turi, ('#9e9e9e', obj.get_ariza_turi_display())
        )
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>', rang, label
        )

    @admin.display(description='Holat', ordering='holat')
    def holat_badge(self, obj):
        rang, label = self._HOLAT_RANG.get(
            obj.holat, ('#9e9e9e', obj.get_holat_display())
        )
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>', rang, label
        )

    @admin.display(description='Narx')
    def narx_diapazoni(self, obj):
        if obj.narx_max is not None:
            return f"{obj.narx_min:,} – {obj.narx_max:,}"
        return f"{obj.narx_min:,}+"


@admin.register(ArizaMakler)
class ArizaRieltorAdmin(admin.ModelAdmin):
    list_display = ['ariza', 'rieltor', 'holat', 'created_at']
    list_filter = ['holat']
    list_select_related = ['ariza', 'rieltor']