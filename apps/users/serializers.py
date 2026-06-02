from rest_framework import serializers
from apps.hudud.models import Hudud
from .models import CustomUser


class TelegramAuthSerializer(serializers.Serializer):
    init_data = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'telegram_id', 'telegram_username',
            'full_name', 'phone', 'role', 'created_at'
        ]
        read_only_fields = ['id', 'telegram_id', 'role', 'created_at']


class RieltorRoliSorovSerializer(serializers.Serializer):
    """User rieltor bo'lmoqchi — so'rov yuboradi"""
    bio = serializers.CharField(required=False, allow_blank=True)
    telegram_link = serializers.CharField(required=False, allow_blank=True)
    hududlar = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="Hudud IDlar ro'yxati, kamida 1 ta"
    )


# ===== RIELTOR USERNAME/PAROL AUTH =====

class RieltorRegisterSerializer(serializers.Serializer):
    """Rieltor ro'yxatdan o'tish"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=6, write_only=True)
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    telegram_link = serializers.CharField(required=False, allow_blank=True)
    hududlar = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="Hudud IDlar ro'yxati, kamida 1 ta"
    )

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu username band, boshqasini tanlang")
        return value

    def validate_hududlar(self, value):
        hududlar = Hudud.objects.filter(id__in=value, is_active=True)
        if hududlar.count() != len(value):
            raise serializers.ValidationError("Bir yoki bir nechta hudud topilmadi")
        return value


class RieltorLoginSerializer(serializers.Serializer):
    """Rieltor kirish"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RieltorProfileResponseSerializer(serializers.Serializer):
    """Login/register response uchun"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    phone = serializers.CharField(allow_null=True)
    role = serializers.CharField()
    verify_holat = serializers.CharField()
    bio = serializers.CharField(allow_null=True)
    telegram_link = serializers.CharField(allow_null=True)
