from django.contrib import admin
from .models import MaklerProfil


@admin.register(MaklerProfil)
class RieltorProfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'verify_holat', 'ortacha_reyting', 'jami_bitimlar', 'created_at']
    list_filter = ['verify_holat']
    search_fields = ['user__full_name', 'user__telegram_username']
    filter_horizontal = ['hududlar']
    list_editable = ['verify_holat']
    readonly_fields = ['ortacha_reyting', 'jami_bitimlar', 'verify_qilingan_vaqt']