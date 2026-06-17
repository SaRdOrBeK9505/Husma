from rest_framework import serializers
from apps.hudud.models import Hudud, MulkTuri
from apps.hudud.serializers import HududSerializer, MulkTuriSerializer
from apps.users.serializers import UserSerializer
from .models import MaklerProfil


class RieltorProfilSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    hududlar = HududSerializer(many=True, read_only=True)
    mulk_turlari = MulkTuriSerializer(many=True, read_only=True)

    class Meta:
        model = MaklerProfil
        fields = [
            'id', 'user', 'bio', 'telegram_link',
            'hududlar', 'mulk_turlari', 'verify_holat', 'ortacha_reyting',
            'jami_bitimlar', 'created_at',
        ]
        read_only_fields = ['verify_holat', 'ortacha_reyting', 'jami_bitimlar']


class RieltorProfilUpdateSerializer(serializers.ModelSerializer):
    """Rieltor o'z profilini yangilash uchun"""
    hududlar = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Hudud.objects.filter(is_active=True)
    )
    mulk_turlari = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MulkTuri.objects.filter(is_active=True)
    )

    class Meta:
        model = MaklerProfil
        fields = ['bio', 'telegram_link', 'hududlar', 'mulk_turlari']


class RieltorVerifySerializer(serializers.ModelSerializer):
    """Admin verify qilish uchun"""
    class Meta:
        model = MaklerProfil
        fields = ['verify_holat']


class RieltorLoginSerializer(serializers.Serializer):
    """Rieltor login so'rovi uchun (Swagger docs)"""
    username = serializers.CharField(
        help_text="Telegram orqali ro'yxatdan o'tgan username"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Foydalanuvchi paroli"
    )


class RieltorLoginResponseSerializer(serializers.Serializer):
    """Rieltor login muvaffaqiyatli javob uchun (Swagger docs)"""
    message = serializers.CharField()

    class RieltorInfoSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        bio = serializers.CharField(allow_null=True)
        verify_holat = serializers.CharField()
        faol = serializers.BooleanField()

    rieltor = RieltorInfoSerializer()


# Backward compatibility
MaklerProfilSerializer = RieltorProfilSerializer
MaklerProfilUpdateSerializer = RieltorProfilUpdateSerializer
MaklerVerifySerializer = RieltorVerifySerializer
