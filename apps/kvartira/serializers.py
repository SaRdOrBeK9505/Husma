from rest_framework import serializers
from .models import Kvartira, KvartiraRasm, KvartiraPlanirovka
from apps.hudud.models import Viloyat, Hudud

# Bitta e'longa ruxsat etilgan maksimal rasm soni (owner talabi: 8 tagacha)
MAX_RASM_SONI = 8

# Bitta rasm uchun maksimal fayl hajmi (baytda). Owner talabi bo'yicha
# katta fayllar rad etiladi — DoS/resurs va DigitalOcean Spaces xarajati himoyasi.
MAX_RASM_HAJMI_MB = 10
MAX_RASM_HAJMI = MAX_RASM_HAJMI_MB * 1024 * 1024

# Bitta e'longa yuklanadigan barcha rasmlarning UMUMIY maksimal hajmi (baytda).
# Bu nginx `client_max_body_size` bilan mos bo'lishi kerak (nginx biroz kattaroq
# — masalan 25M — bo'lsin, chunki so'rovda rasmdan tashqari boshqa maydonlar ham bor).
MAX_UMUMIY_HAJMI_MB = 20
MAX_UMUMIY_HAJMI = MAX_UMUMIY_HAJMI_MB * 1024 * 1024

# Ruxsat etilgan rasm MIME turlari (formatlar).
RUXSAT_MIME_TURLARI = {
    'image/jpeg',
    'image/png',
    'image/webp',
}
RUXSAT_KENGAYTMALAR = ('.jpg', '.jpeg', '.png', '.webp')


def rasm_faylini_tekshir(fayl):
    """
    Yuklangan rasm faylini hajm va format (MIME) bo'yicha tekshiradi.

    Django'ning `ImageField`i faylning haqiqiy rasm ekanini (Pillow orqali)
    allaqachon tekshiradi, lekin hajm va aniq formatga cheklov qo'ymaydi.
    Bu validator qo'shimcha himoya qatlamini beradi.

    Raises:
        serializers.ValidationError: hajm katta yoki format ruxsat etilmagan bo'lsa.
    """
    # 1. Fayl hajmi
    hajm = getattr(fayl, 'size', None)
    if hajm is not None and hajm > MAX_RASM_HAJMI:
        raise serializers.ValidationError(
            f"Rasm hajmi juda katta ({hajm / (1024 * 1024):.1f} MB). "
            f"Ruxsat etilgan maksimal hajm — {MAX_RASM_HAJMI_MB} MB."
        )

    # 2. MIME turi (content_type) yoki kengaytma
    content_type = getattr(fayl, 'content_type', None)
    nomi = (getattr(fayl, 'name', '') or '').lower()
    kengaytma_ok = nomi.endswith(RUXSAT_KENGAYTMALAR)

    if content_type is not None:
        if content_type not in RUXSAT_MIME_TURLARI:
            raise serializers.ValidationError(
                f"Rasm formati qo'llab-quvvatlanmaydi ({content_type}). "
                f"Faqat JPEG, PNG yoki WEBP yuklash mumkin."
            )
    elif nomi and not kengaytma_ok:
        raise serializers.ValidationError(
            "Rasm formati qo'llab-quvvatlanmaydi. "
            "Faqat JPEG, PNG yoki WEBP yuklash mumkin."
        )

    return fayl


def umumiy_hajmni_tekshir(fayllar):
    """
    Yuklangan rasmlar ro'yxatining UMUMIY hajmini tekshiradi.

    Har bir fayl alohida `MAX_RASM_HAJMI` bilan cheklangan bo'lsa ham,
    ko'p fayl birga kelganda umumiy hajm server/nginx limitidan oshib
    413 (Request Entity Too Large) xatosini keltirib chiqarishi mumkin.
    Bu validator umumiy hajmni oldindan cheklab, aniq xabar beradi.

    Raises:
        serializers.ValidationError: umumiy hajm ruxsat etilgandan katta bo'lsa.
    """
    jami = 0
    for fayl in fayllar:
        jami += getattr(fayl, 'size', 0) or 0
    if jami > MAX_UMUMIY_HAJMI:
        raise serializers.ValidationError(
            f"Rasmlarning umumiy hajmi juda katta ({jami / (1024 * 1024):.1f} MB). "
            f"Ruxsat etilgan umumiy hajm — {MAX_UMUMIY_HAJMI_MB} MB. "
            f"Rasmlarni kamaytiring yoki siqib (kichraytirib) yuklang."
        )


class KvartiraRasmSerializer(serializers.ModelSerializer):
    class Meta:
        model = KvartiraRasm
        fields = ['id', 'rasm', 'asosiy', 'tartib', 'created_at']
        read_only_fields = ['id', 'created_at']


class KvartiraPlanirovkaSerializer(serializers.ModelSerializer):
    class Meta:
        model = KvartiraPlanirovka
        fields = ['id', 'rasm', 'izoh', 'created_at']
        read_only_fields = ['id', 'created_at']


class KvartiraSerializer(serializers.ModelSerializer):
    """To'liq o'qish uchun — detail va list."""
    rasmlar = KvartiraRasmSerializer(many=True, read_only=True)
    planirovkalar = KvartiraPlanirovkaSerializer(many=True, read_only=True)

    hudud_nomi = serializers.CharField(source='hudud.nomi', read_only=True)
    viloyat_nomi = serializers.CharField(source='viloyat.nomi', read_only=True)
    mulk_turi_nomi = serializers.CharField(source='mulk_turi.nomi', read_only=True)
    qoshgan_nomi = serializers.CharField(source='qoshgan.full_name', read_only=True)

    ariza_turi_display = serializers.CharField(
        source='get_ariza_turi_display', read_only=True
    )
    xonalar_soni_display = serializers.CharField(
        source='get_xonalar_soni_display', read_only=True
    )
    valyuta_display = serializers.CharField(
        source='get_valyuta_display', read_only=True
    )
    narx_davri_display = serializers.CharField(
        source='get_narx_davri_display', read_only=True
    )
    remont_holati_display = serializers.CharField(
        source='get_remont_holati_display', read_only=True
    )
    yangimi = serializers.BooleanField(read_only=True)
    featured_faolmi = serializers.BooleanField(read_only=True)

    class Meta:
        model = Kvartira
        fields = [
            'id',
            'mulk_turi', 'mulk_turi_nomi',
            'viloyat', 'viloyat_nomi',
            'hudud', 'hudud_nomi',
            'qoshgan', 'qoshgan_nomi',
            'sarlavha', 'tavsif', 'ariza_turi', 'ariza_turi_display',
            'narx', 'valyuta', 'valyuta_display',
            'narx_davri', 'narx_davri_display',
            'xonalar_soni', 'xonalar_soni_display',
            'hammom_soni', 'maydon_m2', 'qavat', 'jami_qavat',
            'remont_holati', 'remont_holati_display', 'mebel',
            'manzil', 'latitude', 'longitude',
            'telefon', 'telegram_username', 'telegram_id',
            'holat', 'is_verified', 'featured', 'featured_faolmi',
            'yangimi', 'rasmlar', 'planirovkalar',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'qoshgan', 'is_verified', 'featured',
            'telegram_id', 'created_at', 'updated_at',
        ]


class KvartiraYaratishSerializer(serializers.ModelSerializer):
    """Rieltor kvartira qo'shadi/tahrirlaydi. Rasmlarni ko'p qilib yuklash mumkin."""
    rasmlar = serializers.ListField(
        child=serializers.ImageField(validators=[rasm_faylini_tekshir]),
        write_only=True,
        required=False,
        help_text=f"Kvartira rasmlari — {MAX_RASM_SONI} tagacha, har biri {MAX_RASM_HAJMI_MB} MB gacha (JPEG/PNG/WEBP)"
    )
    planirovkalar = serializers.ListField(
        child=serializers.ImageField(validators=[rasm_faylini_tekshir]),
        write_only=True,
        required=False,
        help_text="Planirovka (floor plan) rasmlari"
    )

    # Viloyat va tuman (hudud) — majburiy. Bo'sh qoldirib bo'lmaydi.
    viloyat = serializers.PrimaryKeyRelatedField(
        queryset=Viloyat.objects.all(),
        required=True,
        allow_null=False,
        error_messages={
            'required': "Viloyatni tanlash majburiy.",
            'null': "Viloyatni tanlash majburiy.",
        },
    )
    hudud = serializers.PrimaryKeyRelatedField(
        queryset=Hudud.objects.all(),
        required=True,
        allow_null=False,
        error_messages={
            'required': "Tumanni tanlash majburiy.",
            'null': "Tumanni tanlash majburiy.",
        },
    )

    class Meta:
        model = Kvartira
        fields = [
            'mulk_turi', 'viloyat', 'hudud',
            'sarlavha', 'tavsif', 'ariza_turi',
            'narx', 'valyuta', 'narx_davri',
            'xonalar_soni', 'hammom_soni', 'maydon_m2',
            'qavat', 'jami_qavat', 'remont_holati', 'mebel',
            'manzil', 'latitude', 'longitude',
            'telefon', 'telegram_username',
            'holat', 'rasmlar', 'planirovkalar',
        ]

    def validate_rasmlar(self, value):
        if len(value) > MAX_RASM_SONI:
            raise serializers.ValidationError(
                f"Ko'pi bilan {MAX_RASM_SONI} ta rasm yuklash mumkin."
            )
        umumiy_hajmni_tekshir(value)
        return value

    def validate_planirovkalar(self, value):
        umumiy_hajmni_tekshir(value)
        return value

    def _rasm_limitini_tekshir(self, kvartira, yangi_rasmlar):
        """Mavjud + yangi rasmlar 8 tadan oshmasligini tekshiradi."""
        mavjud = kvartira.rasmlar.count() if kvartira and kvartira.pk else 0
        if mavjud + len(yangi_rasmlar) > MAX_RASM_SONI:
            raise serializers.ValidationError({
                'rasmlar': (
                    f"Jami rasmlar soni {MAX_RASM_SONI} tadan oshmasligi kerak. "
                    f"Hozir {mavjud} ta bor."
                )
            })

    def create(self, validated_data):
        rasmlar = validated_data.pop('rasmlar', [])
        planirovkalar = validated_data.pop('planirovkalar', [])
        kvartira = Kvartira.objects.create(**validated_data)

        for i, rasm in enumerate(rasmlar):
            KvartiraRasm.objects.create(
                kvartira=kvartira, rasm=rasm,
                asosiy=(i == 0), tartib=i
            )
        for rasm in planirovkalar:
            KvartiraPlanirovka.objects.create(kvartira=kvartira, rasm=rasm)
        return kvartira

    def update(self, instance, validated_data):
        rasmlar = validated_data.pop('rasmlar', None)
        planirovkalar = validated_data.pop('planirovkalar', None)

        if rasmlar:
            self._rasm_limitini_tekshir(instance, rasmlar)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if rasmlar:
            mavjud = instance.rasmlar.count()
            bosh_rasm_bormi = instance.rasmlar.filter(asosiy=True).exists()
            for i, rasm in enumerate(rasmlar):
                KvartiraRasm.objects.create(
                    kvartira=instance, rasm=rasm,
                    asosiy=(not bosh_rasm_bormi and i == 0),
                    tartib=mavjud + i
                )
        if planirovkalar:
            for rasm in planirovkalar:
                KvartiraPlanirovka.objects.create(kvartira=instance, rasm=rasm)
        return instance


class KvartiraStatusSerializer(serializers.ModelSerializer):
    """Faqat statusni tahrirlash uchun."""
    class Meta:
        model = Kvartira
        fields = ['holat']


class KvartiraRasmYuklashSerializer(serializers.Serializer):
    """Mavjud kvartiraga bitta yoki bir nechta yangi rasm qo'shish."""
    rasmlar = serializers.ListField(
        child=serializers.ImageField(validators=[rasm_faylini_tekshir]),
        allow_empty=False,
        help_text=(
            f"Yangi rasmlar — jami {MAX_RASM_SONI} tadan oshmasin, "
            f"har biri {MAX_RASM_HAJMI_MB} MB gacha (JPEG/PNG/WEBP), "
            f"umumiy hajmi {MAX_UMUMIY_HAJMI_MB} MB gacha"
        )
    )

    def validate_rasmlar(self, value):
        umumiy_hajmni_tekshir(value)
        return value
