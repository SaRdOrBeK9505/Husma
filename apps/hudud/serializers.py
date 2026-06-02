from rest_framework import serializers
from .models import Hudud


class HududSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hudud
        fields = ['id', 'nomi', 'shahar', 'is_active']