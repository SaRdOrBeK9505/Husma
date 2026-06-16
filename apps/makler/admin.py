from django.contrib import admin
from .models import MaklerProfil


@admin.register(MaklerProfil)
class RieltorProfilAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'username_display', 'verify_holat', 'faol',
        'bepul_muddat_tugash', 'obuna_faol_display', 'obuna_tugash',
        'ortacha_reyting', 'jami_bitimlar', 'created_at',
    ]
    list_filter = ['verify_holat']
    search_fields = [
        'user__full_name', 'user__telegram_username',
        'user__username', 'user__phone',
    ]
    filter_horizontal = ['hududlar', 'mulk_turlari']
    readonly_fields = [
        'ortacha_reyting', 'jami_bitimlar', 'verify_qilingan_vaqt',
        'faol', 'obuna_faol_display', 'obuna_tugash', 'login_malumotlari',
    ]

    fieldsets = (
        ('Asosiy', {
            'fields': ('user', 'login_malumotlari', 'bio', 'telegram_link',
                       'hududlar', 'mulk_turlari')
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

    @admin.display(description='Username')
    def username_display(self, obj):
        return obj.user.username or '—'

    @admin.display(description='Login ma\'lumotlari')
    def login_malumotlari(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        if not obj.user_id:
            return '—'
        url = reverse('admin:users_customuser_change', args=[obj.user_id])
        return format_html(
            "Username: <b>{}</b><br>"
            "Username va parolni tahrirlash uchun: "
            "<a href='{}'>foydalanuvchi sahifasi</a>",
            obj.user.username or '(yo\'q)', url,
        )

    @admin.display(boolean=True, description='Obuna faolmi')
    def obuna_faol_display(self, obj):
        return obj.obuna_faol
