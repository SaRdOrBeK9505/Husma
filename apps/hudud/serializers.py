from rest_framework import serializers
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
    class Meta:
        model = Viloyat
        fields = ['id', 'nomi']
