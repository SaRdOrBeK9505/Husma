from django.utils import timezone
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.hudud.serializers import HududSerializer
from .models import Ariza, ArizaMakler


def vaqt_oldin(dt) -> str:
    """
    datetime → "5s oldin", "3m oldin", "2s oldin", "1k oldin" kabi
    """
    if dt is None:
        return ''
    now = timezone.now()
    diff = int((now - dt).total_seconds())

    if diff < 60:
        return f"{diff}s oldin"
    elif diff < 3600:
        return f"{diff // 60}m oldin"
    elif diff < 86400:
        return f"{diff // 3600}s oldin"
    elif diff < 2592000:
        return f"{diff // 86400}k oldin"
    elif diff < 31536000:
        return f"{diff // 2592000}oy oldin"
    else:
        return f"{diff // 31536000}y oldin"


class ArizaYaratishSerializer(serializers.ModelSerializer):
    """User ariza yuborish uchun"""

    class Meta:
        model = Ariza
        fields = [
            'id', 'hudud', 'ariza_turi', 'xonalar_soni',
            'narx_min', 'narx_max', 'telefon', 'ism', 'qoshimcha_izoh',
        ]

    def validate(self, data):
        if data['narx_min'] > data['narx_max']:
            raise serializers.ValidationError(
                {'narx_min': 'Minimal narx maksimal narxdan katta bo\'lishi mumkin emas'}
            )
        return data


class ArizaSerializer(serializers.ModelSerializer):
    """Ariza detail ko'rish uchun"""
    hudud = HududSerializer(read_only=True)
    ariza_turi_display = serializers.CharField(
        source='get_ariza_turi_display', read_only=True
    )
    xonalar_soni_display = serializers.CharField(
        source='get_xonalar_soni_display', read_only=True
    )
    holat_display = serializers.CharField(
        source='get_holat_display', read_only=True
    )

    class Meta:
        model = Ariza
        fields = [
            'id', 'hudud', 'ariza_turi', 'ariza_turi_display',
            'xonalar_soni', 'xonalar_soni_display',
            'narx_min', 'narx_max', 'telefon', 'ism',
            'qoshimcha_izoh', 'holat', 'holat_display',
            'created_at',
        ]


class MaklerArizaSerializer(serializers.ModelSerializer):
    """Rieltor uchun ariza — telefon raqam ko'rinadi"""
    hudud = HududSerializer(read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    ariza_turi_display = serializers.CharField(
        source='get_ariza_turi_display', read_only=True
    )
    xonalar_soni_display = serializers.CharField(
        source='get_xonalar_soni_display', read_only=True
    )
    vaqt_oldin = serializers.SerializerMethodField()

    class Meta:
        model = Ariza
        fields = [
            'id', 'user_full_name', 'hudud',
            'ariza_turi', 'ariza_turi_display',
            'xonalar_soni', 'xonalar_soni_display',
            'narx_min', 'narx_max', 'telefon', 'ism',
            'qoshimcha_izoh', 'holat', 'created_at', 'vaqt_oldin',
        ]

    @extend_schema_field(serializers.CharField())
    def get_vaqt_oldin(self, obj):
        return vaqt_oldin(obj.created_at)