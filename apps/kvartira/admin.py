from django.contrib import admin
from .models import Kvartira, KvartiraRasm, KvartiraPlanirovka


class KvartiraRasmInline(admin.TabularInline):
    model = KvartiraRasm
    extra = 1
    fields = ['rasm', 'asosiy', 'tartib']


class KvartiraPlanirovkaInline(admin.TabularInline):
    model = KvartiraPlanirovka
    extra = 1
    fields = ['rasm', 'izoh']


@admin.register(Kvartira)
class KvartiraAdmin(admin.ModelAdmin):
    list_display = [
        'sarlavha', 'hudud', 'ariza_turi', 'xonalar_soni',
        'narx', 'valyuta', 'holat', 'is_verified', 'featured', 'created_at'
    ]
    list_filter = [
        'ariza_turi', 'xonalar_soni', 'holat', 'is_verified',
        'featured', 'valyuta', 'mulk_turi', 'hudud',
    ]
    search_fields = ['sarlavha', 'manzil', 'telefon', 'telegram_username']
    list_editable = ['is_verified', 'holat', 'featured']
    inlines = [KvartiraRasmInline, KvartiraPlanirovkaInline]
    readonly_fields = ['created_at', 'updated_at', 'telegram_id']
    fieldsets = (
        ('Asosiy', {
            'fields': ('qoshgan', 'mulk_turi', 'viloyat', 'hudud',
                       'sarlavha', 'tavsif', 'ariza_turi')
        }),
        ('Narx', {
            'fields': ('narx', 'valyuta', 'narx_davri')
        }),
        ('Xarakteristikalar', {
            'fields': ('xonalar_soni', 'hammom_soni', 'maydon_m2',
                       'qavat', 'jami_qavat', 'remont_holati', 'mebel')
        }),
        ('Joylashuv', {
            'fields': ('manzil', 'latitude', 'longitude')
        }),
        ('Aloqa', {
            'fields': ('telefon', 'telegram_username', 'telegram_id')
        }),
        ('Holat / Moderatsiya', {
            'fields': ('holat', 'is_verified', 'featured', 'featured_tugash')
        }),
        ('Vaqtlar', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(KvartiraRasm)
class KvartiraRasmAdmin(admin.ModelAdmin):
    list_display = ['kvartira', 'asosiy', 'tartib', 'created_at']
    list_filter = ['asosiy']


@admin.register(KvartiraPlanirovka)
class KvartiraPlanirovkaAdmin(admin.ModelAdmin):
    list_display = ['kvartira', 'izoh', 'created_at']
