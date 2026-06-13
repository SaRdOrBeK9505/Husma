from django.contrib import admin
from .models import MaklerProfil


@admin.register(MaklerProfil)
class RieltorProfilAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'verify_holat', 'faol',
        'bepul_muddat_tugash', 'obuna_faol_display', 'obuna_tugash',
        'ortacha_reyting', 'jami_bitimlar', 'created_at',
    ]
    list_filter = ['verify_holat']
    search_fields = ['user__full_name', 'user__telegram_username']
    filter_horizontal = ['hududlar', 'mulk_turlari']
    readonly_fields = [
        'ortacha_reyting', 'jami_bitimlar', 'verify_qilingan_vaqt',
        'faol', 'obuna_faol_display', 'obuna_tugash',
    ]

    fieldsets = (
        ('Asosiy', {
            'fields': ('user', 'bio', 'telegram_link', 'hududlar', 'mulk_turlari')
        }),
        ('Moderatsiya', {
            'fields': ('verify_holat', 'verify_qilingan_vaqt'),
            'description': (
                "verify_holat = 'Bloklangan' qilinsa, obuna/bepul muddatidan "
                "qat'i nazar rieltor ishlay olmaydi."
            ),
        }),
        ('Sinov va Obuna', {
            'fields': ('bepul_muddat_tugash', 'faol', 'obuna_faol_display', 'obuna_tugash'),
            'description': (
                "Obuna ma'lumotlari 'Obuna' bo'limidan boshqariladi. "
                "Bu yerda faqat hisoblangan holat ko'rsatiladi."
            ),
        }),
    )

    @admin.display(boolean=True, description='Obuna faolmi')
    def obuna_faol_display(self, obj):
        return obj.obuna_faol
