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

    def update(self, instance, validated_data):
        """
        MUHIM — ManyToMany vaqt tartibi:
        ManyToMany maydonlari (hududlar, mulk_turlari) asosiy model.save()'dan
        alohida o'rnatiladi. Shuning uchun o'zgarishni aniqlash uchun eski ID
        to'plamlarini set() CHAQIRILMASDAN OLDIN saqlab qo'yamiz, keyin
        set() dan keyin solishtirish qilamiz.

        post_save signal'dan foydalanib solishtirish XATO bo'lardi, chunki
        signal paytida ManyToMany hali yangilanmagan bo'ladi — loyihada ilgari
        shunga o'xshash token tartibi xatosi yuz bergan edi.
        """
        from apps.ariza.services import yangi_rieltorga_eski_arizalarni_biriktir

        # 1. ManyToMany maydonlari uchun yangi qiymatlarni validated_data'dan olamiz
        yangi_hududlar = validated_data.pop('hududlar', None)
        yangi_mulk_turlari = validated_data.pop('mulk_turlari', None)

        # 2. set() CHAQIRILMASDAN OLDIN eski ID to'plamlarini saqlaymiz.
        #    Shu tartib muhim: keyin set() ni chaqirgandan so'ng solishtirish
        #    har doim to'g'ri ishlamaydi, chunki instance allaqachon yangilanib
        #    bo'ladi.
        eski_hudud_idlar = (
            set(instance.hududlar.values_list('id', flat=True))
            if yangi_hududlar is not None
            else None
        )
        eski_mulk_turi_idlar = (
            set(instance.mulk_turlari.values_list('id', flat=True))
            if yangi_mulk_turlari is not None
            else None
        )

        # 3. Oddiy maydonlarni saqlaymiz (bio, telegram_link, ...)
        instance = super().update(instance, validated_data)

        # 4. ManyToMany maydonlarini yangilaymiz (set() bu yerda chaqiriladi)
        if yangi_hududlar is not None:
            instance.hududlar.set(yangi_hududlar)
        if yangi_mulk_turlari is not None:
            instance.mulk_turlari.set(yangi_mulk_turlari)

        # 5. set() dan KEYIN yangi ID to'plamlar bilan solishtiramiz.
        #    Faqat hududlar YOKI mulk_turlari o'zgarganda biriktirish ishga tushadi.
        #    bio, telegram_link kabi boshqa maydonlar o'zgarganda ISHLAMAYDI.
        hudud_ozgardi = (
            eski_hudud_idlar is not None
            and eski_hudud_idlar != set(instance.hududlar.values_list('id', flat=True))
        )
        mulk_turi_ozgardi = (
            eski_mulk_turi_idlar is not None
            and eski_mulk_turi_idlar != set(instance.mulk_turlari.values_list('id', flat=True))
        )

        if hudud_ozgardi or mulk_turi_ozgardi:
            # xabar_yubor=False: bu eski arizalar backfill'i, rieltorga
            # "yangi ariza keldi" signali yuborish noto'g'ri.
            yangi_rieltorga_eski_arizalarni_biriktir(instance, xabar_yubor=False)

        return instance


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
