from io import BytesIO

from rest_framework import serializers
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from .models import Kvartira, KvartiraRasm, KvartiraPlanirovka
from apps.hudud.models import Viloyat, Hudud

# --- HEIC/HEIF (iPhone rasmlari) qo'llab-quvvatlash ---
# pillow-heif kutubxonasi o'rnatilgan bo'lsa, Pillow HEIC faylini ham o'qiy
# oladi. O'rnatilmagan bo'lsa — app ishlashda davom etadi (faqat HEIC qabul
# qilinmaydi), shuning uchun import xatoni yutamiz.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_QOLLAB_QUVVATLANADI = True
except Exception:  # pragma: no cover - kutubxona yo'q bo'lsa
    HEIC_QOLLAB_QUVVATLANADI = False

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
# HEIC/HEIF — iPhone standart formati. Ular qabul qilinadi, lekin saqlashdan
# oldin JPEG'ga aylantiriladi (web brauzerlar HEIC'ni ko'rsata olmaydi).
RUXSAT_MIME_TURLARI = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/heic',
    'image/heif',
}
RUXSAT_KENGAYTMALAR = ('.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif')

# HEIC/HEIF fayllarni aniqlash uchun.
HEIC_MIME_TURLARI = {'image/heic', 'image/heif'}
HEIC_KENGAYTMALAR = ('.heic', '.heif')


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

    # 2. MIME turi (content_type) va/yoki kengaytma tekshiruvi.
    # Ba'zi qurilmalar/brauzerlar (asosan iPhone/Safari) to'g'ri formatdagi
    # faylni noto'g'ri MIME turi (masalan "application/octet-stream") bilan
    # yuborishi mumkin. Shuning uchun KAMIDA BITTASI to'g'ri bo'lsa qabul
    # qilinadi: content_type YOKI fayl kengaytmasi.
    content_type = getattr(fayl, 'content_type', None)
    nomi = (getattr(fayl, 'name', '') or '').lower()
    kengaytma_ok = nomi.endswith(RUXSAT_KENGAYTMALAR)
    mime_ok = content_type in RUXSAT_MIME_TURLARI if content_type else False

    if not mime_ok and not kengaytma_ok:
        raise serializers.ValidationError(
            f"Rasm formati qo'llab-quvvatlanmaydi"
            f"{f' ({content_type})' if content_type else ''}. "
            f"Faqat JPEG, PNG, WEBP yoki HEIC/HEIF (iPhone) yuklash mumkin."
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


def _heic_faylmi(fayl):
    """Fayl HEIC/HEIF formatida ekanligini nom yoki content_type bo'yicha aniqlaydi."""
    nomi = (getattr(fayl, 'name', '') or '').lower()
    content_type = (getattr(fayl, 'content_type', '') or '').lower()
    return nomi.endswith(HEIC_KENGAYTMALAR) or content_type in HEIC_MIME_TURLARI


def heic_ni_jpegga_aylantir(fayl):
    """
    Agar fayl HEIC/HEIF (iPhone) formatida bo'lsa — uni JPEG'ga aylantirib
    qaytaradi. Boshqa formatlar (JPEG/PNG/WEBP) o'zgarishsiz qaytariladi.

    MUHIM:
    - EXIF orientation hisobga olinadi (`exif_transpose`) — aks holda iPhone
      rasmlari yon tomonga ag'darilib saqlanadi.
    - pillow-heif o'rnatilmagan bo'lsa (HEIC_QOLLAB_QUVVATLANADI=False) —
      fayl o'zgarishsiz qaytariladi (bunda ImageField uni rad etadi).
    """
    if not _heic_faylmi(fayl) or not HEIC_QOLLAB_QUVVATLANADI:
        return fayl

    # Faylni boshidan o'qishga tayyorlaymiz
    if hasattr(fayl, 'seek'):
        fayl.seek(0)

    rasm = Image.open(fayl)
    # EXIF orientation'ni to'g'rilash (iPhone rasmlari uchun kritik)
    rasm = ImageOps.exif_transpose(rasm)
    rasm = rasm.convert('RGB')

    buffer = BytesIO()
    rasm.save(buffer, format='JPEG', quality=85, optimize=True)

    asl_nomi = (getattr(fayl, 'name', '') or 'rasm').rsplit('.', 1)[0]
    return ContentFile(buffer.getvalue(), name=f"{asl_nomi}.jpg")


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
            'sanuzellar_soni', 'maydon_m2', 'qavat', 'jami_qavat',
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

    # Tuman (hudud) — MAJBURIY. Bo'sh qoldirib bo'lmaydi.
    hudud = serializers.PrimaryKeyRelatedField(
        queryset=Hudud.objects.all(),
        required=True,
        allow_null=False,
        error_messages={
            'required': "Tumanni tanlash majburiy.",
            'null': "Tumanni tanlash majburiy.",
        },
    )
    # Viloyat — ixtiyoriy yuboriladi; yuborilmasa tumandan avtomatik olinadi.
    # ("Barchasi" kabi bo'sh qiymat yuborilsa ham xato bermaydi.)
    viloyat = serializers.PrimaryKeyRelatedField(
        queryset=Viloyat.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Kvartira
        fields = [
            'mulk_turi', 'viloyat', 'hudud',
            'sarlavha', 'tavsif', 'ariza_turi',
            'narx', 'valyuta', 'narx_davri',
            'xonalar_soni', 'sanuzellar_soni', 'maydon_m2',
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

    def validate(self, attrs):
        """
        Viloyat berilmagan (yoki "Barchasi" kabi bo'sh) bo'lsa — uni
        tanlangan tumandan (hudud) avtomatik olamiz. Shunda foydalanuvchi
        faqat tumanni tanlasa yetarli.
        """
        hudud = attrs.get('hudud')
        # PATCH/PUT da hudud yuborilmasa — mavjud instance'dan olamiz
        if hudud is None and self.instance is not None:
            hudud = self.instance.hudud

        if not attrs.get('viloyat'):
            if hudud is not None and hudud.viloyat_id:
                attrs['viloyat'] = hudud.viloyat
        return attrs

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
                kvartira=kvartira, rasm=heic_ni_jpegga_aylantir(rasm),
                asosiy=(i == 0), tartib=i
            )
        for rasm in planirovkalar:
            KvartiraPlanirovka.objects.create(
                kvartira=kvartira, rasm=heic_ni_jpegga_aylantir(rasm)
            )
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
                    kvartira=instance, rasm=heic_ni_jpegga_aylantir(rasm),
                    asosiy=(not bosh_rasm_bormi and i == 0),
                    tartib=mavjud + i
                )
        if planirovkalar:
            for rasm in planirovkalar:
                KvartiraPlanirovka.objects.create(
                    kvartira=instance, rasm=heic_ni_jpegga_aylantir(rasm)
                )
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
