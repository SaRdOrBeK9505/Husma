from rest_framework import serializers
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


class RieltorLoginSerializer(serializers.Serializer):
    """Rieltor kirish — username + parol"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RieltorOTPSorovSerializer(serializers.Serializer):
    """
    Rieltor register — 1-qadam.
    Faqat asosiy ma'lumotlar yuboriladi.
    telegram_id request.user dan olinadi (Telegram auth o'tgan bo'lishi shart).
    Hudud va telegram_link keyinchalik profildan qo'shiladi.
    """
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu username band, boshqasini tanlang")
        return value


class RieltorOTPVerifySerializer(serializers.Serializer):
    """
    Rieltor register — 2-qadam.
    Faqat kode yuboriladi.
    telegram_id request.user dan olinadi.
    """
    kode = serializers.CharField(max_length=6, min_length=6)
