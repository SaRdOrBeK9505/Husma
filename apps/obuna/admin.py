from django.contrib import admin
from django.utils import timezone
from .models import Tarif, Obuna, Tolov, PaymeTransaction


@admin.register(Tarif)
class TarifAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'kod', 'narx', 'davomiylik_kun', 'tartib', 'is_active']
    list_editable = ['narx', 'tartib', 'is_active']
    list_filter = ['is_active']
    search_fields = ['nomi', 'kod']
    prepopulated_fields = {'kod': ('nomi',)}


class TolovInline(admin.TabularInline):
    model = Tolov
    extra = 0
    readonly_fields = ['created_at', 'tolangan_vaqt']
    fields = ['provayder', 'summa', 'holat', 'tashqi_id', 'tolangan_vaqt', 'created_at']


@admin.register(Obuna)
class ObunaAdmin(admin.ModelAdmin):
    list_display = [
        'rieltor', 'tarif', 'holat', 'narx',
        'boshlanish_vaqti', 'tugash_vaqti', 'faolmi',
    ]
    list_filter = ['holat', 'tarif']
    search_fields = ['rieltor__user__full_name', 'rieltor__user__username']
    readonly_fields = ['created_at', 'updated_at', 'faolmi']
    inlines = [TolovInline]
    actions = ['faollashtirish_action']

    @admin.display(boolean=True, description='Hozir faolmi')
    def faolmi(self, obj):
        return obj.faolmi

    @admin.action(description="Tanlangan obunalarni faollashtirish (qo'lda)")
    def faollashtirish_action(self, request, queryset):
        soni = 0
        for obuna in queryset:
            obuna.faollashtirish()
            soni += 1
        self.message_user(request, f"{soni} ta obuna faollashtirildi.")


@admin.register(Tolov)
class TolovAdmin(admin.ModelAdmin):
    list_display = [
        'obuna', 'provayder', 'summa', 'holat',
        'tashqi_id', 'tolangan_vaqt', 'created_at',
    ]
    list_filter = ['provayder', 'holat']
    search_fields = ['tashqi_id', 'obuna__rieltor__user__full_name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['tasdiqlash_action']

    @admin.action(description="To'lovni tasdiqlash → obunani faollashtirish")
    def tasdiqlash_action(self, request, queryset):
        soni = 0
        for tolov in queryset.filter(holat=Tolov.Holat.KUTILMOQDA):
            tolov.muvaffaqiyatli_deb_belgilash()
            soni += 1
        self.message_user(request, f"{soni} ta to'lov tasdiqlandi va obuna faollashtirildi.")


@admin.register(PaymeTransaction)
class PaymeTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'payme_id', 'tolov', 'amount', 'state',
        'reason', 'created_at',
    ]
    list_filter = ['state']
    search_fields = ['payme_id', 'tolov__obuna__rieltor__user__full_name']
    readonly_fields = [
        'tolov', 'payme_id', 'amount', 'state', 'reason',
        'create_time', 'perform_time', 'cancel_time',
        'created_at', 'updated_at',
    ]

    def has_add_permission(self, request):
        # Payme tranzaksiyalari faqat webhook orqali yaratiladi
        return False
