from rest_framework import serializers
from .models import Kvartira, KvartiraRasm


class KvartiraRasmSerializer(serializers.ModelSerializer):
    class Meta:
        model = KvartiraRasm
        fields = ['id', 'rasm', 'asosiy']


class KvartiraSerializer(serializers.ModelSerializer):
    rasmlar = KvartiraRasmSerializer(many=True, read_only=True)
    hudud_nomi = serializers.CharField(source='hudud.nomi', read_only=True)
    ariza_turi_display = serializers.CharField(
        source='get_ariza_turi_display', read_only=True
    )
    xonalar_soni_display = serializers.CharField(
        source='get_xonalar_soni_display', read_only=True
    )

    class Meta:
        model = Kvartira
        fields = [
            'id', 'hudud', 'hudud_nomi', 'sarlavha', 'tavsif',
            'ariza_turi', 'ariza_turi_display',
            'xonalar_soni', 'xonalar_soni_display',
            'narx', 'maydon_m2', 'qavat', 'jami_qavat',
            'manzil', 'holat', 'is_verified',
            'rasmlar', 'created_at',
        ]


class KvartiraYaratishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kvartira
        fields = [
            'hudud', 'sarlavha', 'tavsif',
            'ariza_turi', 'xonalar_soni',
            'narx', 'maydon_m2', 'qavat',
            'jami_qavat', 'manzil',
        ]