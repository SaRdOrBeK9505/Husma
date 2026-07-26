from django.contrib import admin
from django.utils import timezone
from .models import MaklerProfil


class ObunaHolatFilter(admin.SimpleListFilter):
    """
    Rieltorlarni obuna/muddat holati bo'yicha filtrlash.

    Variantlar:
      - faol_obuna       : hozir to'langan (faol) obunasi bor
      - bepul_muddat     : bepul sinov muddati ichida (hali tugamagan)
      - qoshimcha_bepul  : 14 kunlik qo'shimcha aksiya berilgan
      - muddat_tugagan   : ishlash huquqi yo'q (bepul ham, obuna ham yo'q)
    """
    title = "Obuna / muddat holati"
    parameter_name = 'obuna_holat'

    def lookups(self, request, model_admin):
        return (
            ('faol_obuna', 'Faol obunasi bor'),
            ('bepul_muddat', 'Bepul sinov muddati ichida'),
            ('qoshimcha_bepul', '14 kunlik aksiya berilgan'),
            ('muddat_tugagan', 'Muddati tugagan (huquqi yo\'q)'),
        )

    def queryset(self, request, queryset):
        from apps.obuna.models import Obuna
        now = timezone.now()

        faol_obuna_idlari = Obuna.objects.filter(
            holat=Obuna.Holat.FAOL,
            tugash_vaqti__gt=now,
        ).values_list('rieltor_id', flat=True)

        val = self.value()

        if val == 'faol_obuna':
            return queryset.filter(id__in=list(faol_obuna_idlari))

        if val == 'bepul_muddat':
            return queryset.filter(
                bepul_muddat_tugash__gt=now,
                bepul_muddat_tugash__isnull=False,
            )

        if val == 'qoshimcha_bepul':
            return queryset.filter(qoshimcha_bepul_muddat_berildi=True)

        if val == 'muddat_tugagan':
            # Bepul muddati tugagan YOKI yo'q, VA faol obunasi yo'q
            return queryset.exclude(
                bepul_muddat_tugash__gt=now,
            ).exclude(
                id__in=list(faol_obuna_idlari),
            )

        return queryset


@admin.register(MaklerProfil)
class RieltorProfilAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'username_display', 'verify_holat', 'faol',
        'bepul_muddat_tugash', 'qoshimcha_bepul_muddat_berildi',
        'obuna_faol_display', 'obuna_tugash',
        'ortacha_reyting', 'jami_bitimlar', 'created_at',
    ]
    list_filter = [
        'verify_holat',
        ObunaHolatFilter,
        'qoshimcha_bepul_muddat_berildi',
        'promo_xabar_yuborildi',
    ]
    search_fields = [
        'user__full_name', 'user__telegram_username',
        'user__username', 'user__phone',
    ]
    filter_horizontal = ['hududlar', 'mulk_turlari']
    readonly_fields = [
        'ortacha_reyting', 'jami_bitimlar', 'verify_qilingan_vaqt',
        'faol', 'obuna_faol_display', 'obuna_tugash', 'login_malumotlari',
        'qoshimcha_bepul_muddat_vaqti', 'promo_xabar_vaqti',
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
            'fields': (
                'bepul_muddat_tugash', 'faol',
                'qoshimcha_bepul_muddat_berildi', 'qoshimcha_bepul_muddat_vaqti',
                'promo_xabar_yuborildi', 'promo_xabar_vaqti',
                'obuna_faol_display', 'obuna_tugash',
            ),
            'description': (
                "Obuna ma'lumotlari 'Obuna' bo'limidan boshqariladi. "
                "Bu yerda faqat hisoblangan holat ko'rsatiladi. "
                "'14 kunlik aksiya berildi' — qo'shimcha bepul muddat aksiyasi "
                "berilgan-berilmaganini bildiradi (idempotency uchun). "
                "'promo_xabar_yuborildi' — bepul muddat tugagach obuna promo "
                "(aksiya) xabari yuborilgan-yuborilmaganini bildiradi. Belgini "
                "olib tashlasangiz, keyingi kuni 10:00 da xabar qayta yuboriladi."
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
