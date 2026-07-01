from rest_framework import serializers
from apps.hudud.models import Hudud, MulkTuri
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


class RieltorOTPSorovSerializer(serializers.Serializer):
    """
    Rieltor register — 1-qadam.
    telegram_id request.user dan olinadi (Telegram auth o'tgan bo'lishi shart).
    Hudud va mulk turlari registratsiyada MAJBURIY — shunda rieltor profilni
    keyin alohida tahrirlashi shart bo'lmaydi va unga darhol ariza tarqatiladi.
    
    DIQQAT: Username va password KERAK EMAS - rieltor faqat Telegram orqali ishlaydi!
    """
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    hududlar = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Hudud.objects.filter(is_active=True),
        allow_empty=False,
        help_text="Rieltor ishlaydigan hududlar (kamida bitta)",
    )
    mulk_turlari = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MulkTuri.objects.filter(is_active=True),
        allow_empty=False,
        help_text="Rieltor ishlaydigan mulk turlari (kamida bitta)",
    )


class RieltorOTPVerifySerializer(serializers.Serializer):
    """
    Rieltor register — 2-qadam.
    Faqat kode yuboriladi.
    telegram_id request.user dan olinadi.
    """
    kode = serializers.CharField(max_length=6, min_length=6)


# ===== ADMIN AUTH =====

class AdminLoginSerializer(serializers.Serializer):
    """Admin panel uchun login — username + parol"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AdminUserSerializer(serializers.ModelSerializer):
    """Admin profil ma'lumotlari"""
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'full_name', 'role', 
            'is_staff', 'is_superuser', 'created_at'
        ]
        read_only_fields = ['id', 'role', 'is_staff', 'is_superuser', 'created_at']


class AdminChangePasswordSerializer(serializers.Serializer):
    """Admin parolini o'zgartirish"""
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=6)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri")
        return value
    
    def validate_new_password(self, value):
        # Yangi parol eski parol bilan bir xil bo'lmasligi kerak
        user = self.context['request'].user
        if user.check_password(value):
            raise serializers.ValidationError("Yangi parol eski parol bilan bir xil bo'lmasligi kerak")
        return value
