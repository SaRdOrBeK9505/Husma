from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import SiteSettings, KontaktMalumot, UserStatistika, SliderKarta


# ===== SLIDER KARTOCHKA =====

class SliderKartaSerializer(serializers.ModelSerializer):
    """User / rieltor uchun — faqat o'qish"""
    class Meta:
        model = SliderKarta
        fields = ['id', 'badge_matn', 'sarlavha', 'title', 'description', 'tartib']


class SliderKartaAdminSerializer(serializers.ModelSerializer):
    """Admin uchun — to'liq CRUD"""
    class Meta:
        model = SliderKarta
        fields = [
            'id', 'panel_turi', 'badge_matn', 'sarlavha',
            'title', 'description', 'tartib', 'faol',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


# ===== YORDAMCHI SERIALIZERLAR (schema uchun) =====

class UstunlikSerializer(serializers.Serializer):
    sarlavha = serializers.CharField()
    tavsif = serializers.CharField()


class QadamSerializer(serializers.Serializer):
    raqam = serializers.IntegerField()
    sarlavha = serializers.CharField()
    tavsif = serializers.CharField()


# ===== USER STATISTIKA =====

class UserStatistikaSerializer(serializers.Serializer):
    """
    User paneli uchun — dinamik statistika.
    bitimlar va rieltor_soni DB'dan real hisoblanadi.
    javob_vaqti esa admin nazoratida (UserStatistika modelidan).
    """
    bitimlar    = serializers.IntegerField(help_text="Yopilgan bitimlar soni (DB'dan hisob)")
    rieltor_soni = serializers.IntegerField(help_text="Faol (verified) rieltorlar soni (DB'dan hisob)")
    javob_vaqti = serializers.CharField(help_text="O'rtacha javob vaqti (admin tomonidan kiritilgan)")


class UserStatistikaAdminSerializer(serializers.ModelSerializer):
    """Admin uchun — faqat javob_vaqti ni tahrirlash"""
    class Meta:
        model = UserStatistika
        fields = ['javob_vaqti', 'updated_at']
        read_only_fields = ['updated_at']


# ===== RIELTOR STATISTIKA (dynamic) =====

class RieltorStatistikaSerializer(serializers.Serializer):
    """Rieltor paneli uchun — real-time hisoblanadi"""
    faol_arizalar = serializers.IntegerField()
    konversiya = serializers.FloatField(help_text="Yopilgan / jami arizalar foizi (0–100)")


# ===== KONTAKT =====

class KontaktMalumotSerializer(serializers.ModelSerializer):
    """User va rieltor paneli uchun — faqat o'qish"""
    class Meta:
        model = KontaktMalumot
        fields = ['telefon', 'email', 'telegram_bot', 'ofis_manzil']


class KontaktMalumotAdminSerializer(serializers.ModelSerializer):
    """Admin uchun — tahrirlash"""
    class Meta:
        model = KontaktMalumot
        fields = ['telefon', 'email', 'telegram_bot', 'ofis_manzil', 'updated_at']
        read_only_fields = ['updated_at']


# ===== SITE SETTINGS =====

class SiteSettingsSerializer(serializers.ModelSerializer):
    ustunliklar = serializers.SerializerMethodField()
    qadamlar = serializers.SerializerMethodField()
    tavsiyalar = serializers.SerializerMethodField()

    class Meta:
        model = SiteSettings
        fields = [
            'hero_sarlavha', 'hero_tavsif', 'hero_rasm',
            'komissiya_foiz', 'komissiya_tavsif',
            'xavfsizlik_sarlavha', 'xavfsizlik_tavsif', 'xavfsizlik_qoshimcha',
            'rieltor_maslahati_forma',
            'copyright_matn',
            'ustunliklar', 'qadamlar', 'tavsiyalar',
        ]

    @extend_schema_field(UstunlikSerializer(many=True))
    def get_ustunliklar(self, obj):
        return [
            {"sarlavha": obj.ustunlik_1_sarlavha, "tavsif": obj.ustunlik_1_tavsif},
            {"sarlavha": obj.ustunlik_2_sarlavha, "tavsif": obj.ustunlik_2_tavsif},
            {"sarlavha": obj.ustunlik_3_sarlavha, "tavsif": obj.ustunlik_3_tavsif},
        ]

    @extend_schema_field(QadamSerializer(many=True))
    def get_qadamlar(self, obj):
        return [
            {"raqam": 1, "sarlavha": obj.qadam_1_sarlavha, "tavsif": obj.qadam_1_tavsif},
            {"raqam": 2, "sarlavha": obj.qadam_2_sarlavha, "tavsif": obj.qadam_2_tavsif},
            {"raqam": 3, "sarlavha": obj.qadam_3_sarlavha, "tavsif": obj.qadam_3_tavsif},
        ]

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_tavsiyalar(self, obj):
        return [obj.tavsiya_1, obj.tavsiya_2]
