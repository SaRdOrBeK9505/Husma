from django.contrib import admin
from .models import Kvartira, KvartiraRasm


class KvartiraRasmInline(admin.TabularInline):
    model = KvartiraRasm
    extra = 1


@admin.register(Kvartira)
class KvartiraAdmin(admin.ModelAdmin):
    list_display = [
        'sarlavha', 'hudud', 'ariza_turi',
        'xonalar_soni', 'narx', 'holat', 'is_verified', 'created_at'
    ]
    list_filter = ['ariza_turi', 'xonalar_soni', 'holat', 'is_verified', 'hudud']
    search_fields = ['sarlavha', 'manzil']
    list_editable = ['is_verified', 'holat']
    inlines = [KvartiraRasmInline]
    readonly_fields = ['created_at', 'updated_at']