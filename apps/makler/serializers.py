from rest_framework import serializers
from apps.hudud.serializers import HududSerializer
from apps.users.serializers import UserSerializer
from .models import MaklerProfil


class RieltorProfilSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    hududlar = HududSerializer(many=True, read_only=True)

    class Meta:
        model = MaklerProfil
        fields = [
            'id', 'user', 'bio', 'telegram_link',
            'hududlar', 'verify_holat', 'ortacha_reyting',
            'jami_bitimlar', 'created_at',
        ]
        read_only_fields = ['verify_holat', 'ortacha_reyting', 'jami_bitimlar']


class RieltorProfilUpdateSerializer(serializers.ModelSerializer):
    """Rieltor o'z profilini yangilash uchun"""
    hududlar = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=__import__('apps.hudud.models', fromlist=['Hudud']).Hudud.objects.filter(is_active=True)
    )

    class Meta:
        model = MaklerProfil
        fields = ['bio', 'telegram_link', 'hududlar']


class RieltorVerifySerializer(serializers.ModelSerializer):
    """Admin verify qilish uchun"""
    class Meta:
        model = MaklerProfil
        fields = ['verify_holat']


# Backward compatibility
MaklerProfilSerializer = RieltorProfilSerializer
MaklerProfilUpdateSerializer = RieltorProfilUpdateSerializer
MaklerVerifySerializer = RieltorVerifySerializer