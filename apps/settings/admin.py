from django.contrib import admin
from .models import SiteSettings, KontaktMalumot, UserStatistika, SliderKarta


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('🖼 Hero Banner', {
            'fields': ('hero_sarlavha', 'hero_tavsif', 'hero_rasm'),
        }),
        # 📊 Statistika maydonlari olib tashlandi — endi /api/statistika/
        # endpoint'i DB dan real-time hisoblab beradi (ArizaMakler va MaklerProfil dan).
        ('💰 Minimal Komissiya Banner', {
            'fields': ('komissiya_foiz', 'komissiya_tavsif'),
        }),
        ('✅ Nega bizni tanlashadi', {
            'fields': (
                'ustunlik_1_sarlavha', 'ustunlik_1_tavsif',
                'ustunlik_2_sarlavha', 'ustunlik_2_tavsif',
                'ustunlik_3_sarlavha', 'ustunlik_3_tavsif',
            ),
        }),
        ('🔢 Bu qanday ishlaydi', {
            'fields': (
                'qadam_1_sarlavha', 'qadam_1_tavsif',
                'qadam_2_sarlavha', 'qadam_2_tavsif',
                'qadam_3_sarlavha', 'qadam_3_tavsif',
            ),
        }),
        ('📝 Ariza forma', {
            'fields': ('rieltor_maslahati_forma',),
        }),
        ('🛡 Xavfsizlik kafolati', {
            'fields': (
                'xavfsizlik_sarlavha',
                'xavfsizlik_tavsif',
                'xavfsizlik_qoshimcha',
            ),
        }),
        ('💡 Rieltor tavsiyalar', {
            'fields': ('tavsiya_1', 'tavsiya_2'),
        }),
        ('📄 Footer', {
            'fields': ('copyright_matn',),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(KontaktMalumot)
class KontaktMalumotAdmin(admin.ModelAdmin):
    fieldsets = (
        ("📞 Biz bilan bog'laning", {
            'fields': ('telefon', 'email', 'telegram_bot', 'ofis_manzil'),
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        """Faqat bitta yozuv bo'lishi uchun"""
        return not KontaktMalumot.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """O'chirib bo'lmaydi"""
        return False


@admin.register(UserStatistika)
class UserStatistikaAdmin(admin.ModelAdmin):
    fieldsets = (
        ("📊 User paneli statistikasi", {
            'fields': ('bitimlar_soni', 'rieltorlar_soni', 'javob_vaqti',),
            'description': (
                "Bitimlar soni, rieltorlar soni va javob vaqti admin tomonidan kiritiladi. "
                "Frontendda '500+', '50+', '2s' ko'rinishida chiqadi."
            )
        }),
        ("ℹ️ Ma'lumot", {
            'fields': ('updated_at',),
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return not UserStatistika.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SliderKarta)
class SliderKartaAdmin(admin.ModelAdmin):
    list_display = ('title', 'panel_turi', 'badge_matn', 'tartib', 'faol', 'updated_at')
    list_filter = ('panel_turi', 'faol')
    list_editable = ('tartib', 'faol')
    search_fields = ('title', 'badge_matn', 'sarlavha', 'description')
    ordering = ('panel_turi', 'tartib')
    fieldsets = (
        ('🎠 Slider ma\'lumotlari', {
            'fields': ('panel_turi', 'badge_matn', 'sarlavha', 'title', 'description'),
        }),
        ('⚙️ Sozlamalar', {
            'fields': ('tartib', 'faol'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
