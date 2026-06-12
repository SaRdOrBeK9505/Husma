from django.contrib import admin
from .models import MaklerProfil


@admin.register(MaklerProfil)
class RieltorProfilAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'verify_holat', 'faol',
        'bepul_muddat_tugash', 'obuna_faol', 'obuna_tugash',
        'ortacha_reyting', 'jami_bitimlar', 'created_at',
    ]
    list_filter = ['verify_holat', 'obuna_faol']
    search_fields = ['user__full_name', 'user__telegram_username']
    filter_horizontal = ['hududlar', 'mulk_turlari']
    readonly_fields = ['ortacha_reyting', 'jami_bitimlar', 'verify_qilingan_vaqt', 'faol']

    # Obuna tizimi keyinchalik qo'shiladi — hozir faqat ko'rish
    fieldsets = (
        ('Asosiy', {
            'fields': ('user', 'bio', 'telegram_link', 'hududlar', 'mulk_turlari', 'verify_holat', 'verify_qilingan_vaqt')
        }),
        ('Sinov va Obuna', {
            'fields': ('bepul_muddat_tugash', 'faol', 'obuna_faol', 'obuna_tugash'),
            'description': "Obuna tizimi keyinchalik to'liq qo'shiladi."
        }),
        ('Statistika', {
            'fields': ('ortacha_reyting', 'jami_bitimlar'),
        }),
    )
