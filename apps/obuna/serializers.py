from rest_framework import serializers
from .models import Tarif, Obuna, Tolov


# ===== TARIF =====

class TarifSerializer(serializers.ModelSerializer):
    """Public/rieltor uchun — faqat ko'rsatiladigan maydonlar."""
    chegirma_bormi = serializers.BooleanField(read_only=True)
    chegirma_foizi = serializers.IntegerField(read_only=True)
    tejaladigan_summa = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tarif
        fields = [
            'id', 'nomi', 'kod', 'narx', 'asl_narx',
            'davomiylik_kun', 'izoh', 'tartib',
            'chegirma_bormi', 'chegirma_foizi', 'tejaladigan_summa',
        ]


class TarifRieltorSerializer(serializers.ModelSerializer):
    """
    Rieltor uchun mos tarifni qaytaradi.
    Agar rieltor oldin obuna qilmagan bo'lsa - birinchi oy narxi,
    aks holda - oddiy oylik narxi.

    narx      → haqiqatda to'lanadigan summa (masalan 49 500)
    asl_narx  → chegirmagacha narx, ustidan chiziladi (masalan 99 000)
    """
    birinchi_oy_bormi = serializers.BooleanField(read_only=True)
    chegirma_bormi = serializers.BooleanField(read_only=True)
    chegirma_foizi = serializers.IntegerField(read_only=True)
    tejaladigan_summa = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tarif
        fields = [
            'id', 'nomi', 'kod', 'narx', 'asl_narx',
            'davomiylik_kun', 'izoh', 'tartib',
            'birinchi_oy_bormi',
            'chegirma_bormi', 'chegirma_foizi', 'tejaladigan_summa',
        ]


class TarifAdminSerializer(serializers.ModelSerializer):
    """Admin uchun — to'liq CRUD."""
    chegirma_bormi = serializers.BooleanField(read_only=True)
    chegirma_foizi = serializers.IntegerField(read_only=True)
    tejaladigan_summa = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tarif
        fields = [
            'id', 'nomi', 'kod', 'narx', 'asl_narx', 'davomiylik_kun',
            'izoh', 'tartib', 'is_active',
            'chegirma_bormi', 'chegirma_foizi', 'tejaladigan_summa',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        """asl_narx to'ldirilsa, u narxdan katta bo'lishi kerak."""
        narx = attrs.get('narx', getattr(self.instance, 'narx', None))
        asl_narx = attrs.get('asl_narx', getattr(self.instance, 'asl_narx', None))
        if asl_narx is not None and narx is not None and asl_narx <= narx:
            raise serializers.ValidationError({
                'asl_narx': "Asl narx chegirmali narxdan katta bo'lishi kerak."
            })
        return attrs


# ===== TO'LOV =====

class TolovSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tolov
        fields = [
            'id', 'provayder', 'summa', 'holat',
            'tashqi_id', 'tolangan_vaqt', 'created_at',
        ]
        read_only_fields = fields


class TolovAdminSerializer(serializers.ModelSerializer):
    obuna_id = serializers.IntegerField(source='obuna.id', read_only=True)
    rieltor = serializers.CharField(source='obuna.rieltor.user.full_name', read_only=True)

    class Meta:
        model = Tolov
        fields = [
            'id', 'obuna_id', 'rieltor', 'provayder', 'summa',
            'holat', 'tashqi_id', 'metadata', 'tolangan_vaqt', 'created_at',
        ]
        read_only_fields = fields


# ===== OBUNA =====

class ObunaSerializer(serializers.ModelSerializer):
    tarif_nomi = serializers.CharField(source='tarif.nomi', read_only=True)
    faolmi = serializers.BooleanField(read_only=True)
    tolovlar = TolovSerializer(many=True, read_only=True)

    class Meta:
        model = Obuna
        fields = [
            'id', 'tarif', 'tarif_nomi', 'holat', 'narx',
            'boshlanish_vaqti', 'tugash_vaqti', 'faolmi',
            'tolovlar', 'created_at',
        ]
        read_only_fields = fields


class ObunaAdminSerializer(serializers.ModelSerializer):
    tarif_nomi = serializers.CharField(source='tarif.nomi', read_only=True)
    rieltor_ismi = serializers.CharField(source='rieltor.user.full_name', read_only=True)
    faolmi = serializers.BooleanField(read_only=True)
    tolovlar = TolovSerializer(many=True, read_only=True)

    class Meta:
        model = Obuna
        fields = [
            'id', 'rieltor', 'rieltor_ismi', 'tarif', 'tarif_nomi',
            'holat', 'narx', 'boshlanish_vaqti', 'tugash_vaqti',
            'faolmi', 'tolovlar', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'rieltor_ismi', 'tarif_nomi', 'faolmi',
            'tolovlar', 'created_at', 'updated_at',
        ]


class ObunaYaratishSerializer(serializers.Serializer):
    """
    Rieltor obuna sotib olishni boshlaydi.
    tarif tanlanadi (ixtiyoriy - bo'lmasa avtomatik tanlanadi), provayder ko'rsatiladi.
    Natijada Obuna (kutilmoqda) + Tolov (kutilmoqda) yaratiladi.
    
    MUHIM: tarif_id ixtiyoriy. Ko'rsatilmagan bo'lsa:
    - Birinchi obuna bo'lsa - birinchi_oy (49,500 so'm — 50% chegirma, asl 99,000)
    - Aks holda - oylik (199,000 so'm)
    """
    tarif_id = serializers.IntegerField(required=False, allow_null=True)
    provayder = serializers.ChoiceField(
        choices=Tolov.Provayder.choices,
        default=Tolov.Provayder.PAYME,
    )

    def validate_tarif_id(self, value):
        if value is not None:
            try:
                tarif = Tarif.objects.get(pk=value, is_active=True)
            except Tarif.DoesNotExist:
                raise serializers.ValidationError("Bunday faol tarif topilmadi")
            self.context['tarif'] = tarif
        return value


class AdminObunaBerishSerializer(serializers.Serializer):
    """
    Admin rieltorga qo'lda obuna beradi (to'lovsiz, masalan bonus/aksiya).
    Obuna darhol faollashtiriladi.
    """
    rieltor_id = serializers.IntegerField()
    tarif_id = serializers.IntegerField()

    def validate_rieltor_id(self, value):
        from apps.makler.models import MaklerProfil
        try:
            self.context['rieltor'] = MaklerProfil.objects.get(pk=value)
        except MaklerProfil.DoesNotExist:
            raise serializers.ValidationError("Rieltor topilmadi")
        return value

    def validate_tarif_id(self, value):
        try:
            self.context['tarif'] = Tarif.objects.get(pk=value)
        except Tarif.DoesNotExist:
            raise serializers.ValidationError("Tarif topilmadi")
        return value
