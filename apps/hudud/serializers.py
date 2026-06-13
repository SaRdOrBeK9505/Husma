from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Hudud, Viloyat, MulkTuri


class MulkTuriSerializer(serializers.ModelSerializer):
    class Meta:
        model = MulkTuri
        fields = ['id', 'kod', 'nomi']


class HududSerializer(serializers.ModelSerializer):
    viloyat_nomi = serializers.CharField(source='viloyat.nomi', read_only=True)

    class Meta:
        model = Hudud
        fields = ['id', 'nomi', 'shahar', 'viloyat', 'viloyat_nomi', 'is_active']


class ViloyatSerializer(serializers.ModelSerializer):
    hududlar = serializers.SerializerMethodField()

    class Meta:
        model = Viloyat
        fields = ['id', 'nomi', 'hududlar']

    @extend_schema_field(HududSerializer(many=True))
    def get_hududlar(self, obj):
        qs = obj.hududlar.filter(is_active=True)
        return HududSerializer(qs, many=True).data
