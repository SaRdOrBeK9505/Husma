from rest_framework import serializers
from apps.users.serializers import UserSerializer
from apps.ariza.models import ArizaMakler, Ariza
from .models import Review
from drf_spectacular.utils import extend_schema_field


class ReviewYaratishSerializer(serializers.ModelSerializer):
    """User review yozish uchun"""

    class Meta:
        model = Review
        fields = ['rieltor', 'yulduz', 'matn']

    def validate_yulduz(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Yulduz 1 dan 5 gacha bo\'lishi kerak')
        return value

    def validate(self, data):
        user = self.context['request'].user
        rieltor = data['rieltor']

        # Bir user bir rieltorga bir marta yozishi mumkin
        if Review.objects.filter(user=user, rieltor=rieltor).exists():
            raise serializers.ValidationError(
                {'non_field_errors': 'Siz bu rieltorga allaqachon baho bergansiz'}
            )

        # Faqat haqiqatan ishlashgan rieltorga review yozish mumkin
        has_worked_together = ArizaMakler.objects.filter(
            ariza__user=user,
            rieltor=rieltor,
            holat__in=[ArizaMakler.Holat.BOGLANDI, ArizaMakler.Holat.YOPILDI],
        ).exists()

        if not has_worked_together:
            raise serializers.ValidationError(
                {'rieltor': 'Siz bu rieltor bilan hali ishlamagansiz. '
                            'Faqat bog\'langan yoki yopilgan arizalar bo\'lsa baho qoldirish mumkin.'}
            )

        return data


class ReviewSerializer(serializers.ModelSerializer):
    """Review ko'rish uchun"""
    user = UserSerializer(read_only=True)
    yulduz_display = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'yulduz', 'yulduz_display',
            'matn', 'created_at'
        ]

    @extend_schema_field(serializers.CharField())
    def get_yulduz_display(self, obj):
        return '⭐' * obj.yulduz


class RieltorReytigSerializer(serializers.Serializer):
    """Rieltor reytingi umumiy ma'lumot"""
    rieltor_id = serializers.IntegerField()
    rieltor_ismi = serializers.CharField()
    ortacha_reyting = serializers.DecimalField(max_digits=3, decimal_places=2)
    jami_reviewlar = serializers.IntegerField()
    reviews = ReviewSerializer(many=True)


# Backward compatibility
MaklerReytigSerializer = RieltorReytigSerializer


class IjobiyReviewSerializer(serializers.ModelSerializer):
    """
    User paneli — 'Mijozlar fikrlari' bo'limi uchun.
    Faqat ijobiy reviewlar (yulduz >= 4).
    """
    ism = serializers.SerializerMethodField()
    xona_hudud = serializers.SerializerMethodField()
    yulduz_display = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'yulduz', 'yulduz_display', 'matn', 'ism', 'xona_hudud']

    @extend_schema_field(serializers.CharField())
    def get_ism(self, obj):
        """Foydalanuvchi ismi"""
        return obj.user.full_name or obj.user.telegram_username or "Foydalanuvchi"

    @extend_schema_field(serializers.CharField())
    def get_xona_hudud(self, obj):
        """
        Userni oxirgi arizasidan xonalar soni + hudud nomi.
        Masalan: '2-xonali, Yunusobod tumani'
        """
        ariza = (
            Ariza.objects
            .filter(user=obj.user)
            .select_related('hudud')
            .order_by('-created_at')
            .first()
        )
        if ariza and ariza.hudud:
            return f"{ariza.xonalar_soni}-xonali, {ariza.hudud.nomi}"
        elif ariza:
            return f"{ariza.xonalar_soni}-xonali"
        return None

    @extend_schema_field(serializers.CharField())
    def get_yulduz_display(self, obj):
        return '⭐' * obj.yulduz