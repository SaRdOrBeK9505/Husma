from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import CustomUser
from apps.hudud.models import Hudud, Viloyat, MulkTuri


class Kvartira(models.Model):
    """
    Kvartira / ko'chmas mulk e'loni.

    Kartochka ko'rinishi PropertyFinder uslubida:
    sarlavha, narx + valyuta, xona/hammom/maydon/qavat, manzil,
    ko'rishlar soni, sevimli, "YANGI" va "featured" belgilari,
    aloqa (telefon + Telegram).
    """

    class ArizaTuri(models.TextChoices):
        IJARA = 'ijara', 'Ijaraga berish'
        SOTISH = 'sotish', 'Sotish'

    class XonalarSoni(models.TextChoices):
        BIR = '1', '1 xonali'
        IKKI = '2', '2 xonali'
        UCH = '3', '3 xonali'
        TORT = '4', '4 xonali'
        BESH_ORTIQ = '5+', '5 va undan ko\'p'

    class Valyuta(models.TextChoices):
        """Owner talabi: narx $ yoki so'mda ko'rsatiladi."""
        USD = 'USD', '$ (dollar)'
        UZS = 'UZS', 'so\'m'

    class NarxDavri(models.TextChoices):
        """Ijara narxi qaysi davr uchun (sotishda ishlatilmaydi)."""
        OYLIK = 'oylik', 'Oyiga'
        YILLIK = 'yillik', 'Yiliga'
        KUNLIK = 'kunlik', 'Kuniga'

    class RemontHolati(models.TextChoices):
        YEVRO = 'yevro', 'Yevro remont'
        ORTA = 'orta', 'O\'rta holat'
        TAMIRSIZ = 'tamirsiz', 'Ta\'mirtalab'
        YANGI_BINO = 'yangi_bino', 'Yangi bino'

    class Holat(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        SOLD = 'sold', 'Sotilgan/Ijarada'
        ARCHIVED = 'archived', 'Arxivlangan'

    # --- Kim qo'shgan / joylashuv ---
    qoshgan = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kvartiralar'
    )
    mulk_turi = models.ForeignKey(
        MulkTuri,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kvartiralar',
        help_text="Kvartira, Hovli, Ofis va h.k."
    )
    viloyat = models.ForeignKey(
        Viloyat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kvartiralar'
    )
    hudud = models.ForeignKey(
        Hudud,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kvartiralar'
    )

    # --- Asosiy ma'lumot ---
    sarlavha = models.CharField(max_length=255)
    tavsif = models.TextField(blank=True, null=True)
    ariza_turi = models.CharField(max_length=10, choices=ArizaTuri.choices)

    # --- Narx ---
    narx = models.BigIntegerField()
    valyuta = models.CharField(
        max_length=3,
        choices=Valyuta.choices,
        default=Valyuta.UZS,
        help_text="Narx valyutasi — $ yoki so'm"
    )
    narx_davri = models.CharField(
        max_length=10,
        choices=NarxDavri.choices,
        blank=True,
        null=True,
        help_text="Faqat ijara uchun: oylik/yillik/kunlik"
    )

    # --- Xarakteristikalar ---
    xonalar_soni = models.CharField(max_length=5, choices=XonalarSoni.choices)
    hammom_soni = models.PositiveSmallIntegerField(
        blank=True, null=True,
        help_text="Vannaxona / hammom soni"
    )
    maydon_m2 = models.FloatField(blank=True, null=True)
    qavat = models.PositiveSmallIntegerField(blank=True, null=True)
    jami_qavat = models.PositiveSmallIntegerField(blank=True, null=True)
    remont_holati = models.CharField(
        max_length=15,
        choices=RemontHolati.choices,
        blank=True,
        null=True
    )
    mebel = models.BooleanField(default=False, help_text="Mebel bilanmi")

    # --- Joylashuv (aniq manzil / xarita) ---
    manzil = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Aniq manzil (ko'cha, uy raqami)"
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text="Xaritadagi aniq location — kenglik (lat)"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text="Xaritadagi aniq location — uzunlik (lng)"
    )

    # --- Aloqa (owner talabi: qo'ng'iroq + Telegram, WhatsApp emas) ---
    telefon = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Qo'ng'iroq uchun telefon raqami"
    )
    telegram_username = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Telegram username (background) — @username"
    )
    telegram_id = models.BigIntegerField(
        blank=True, null=True,
        help_text="Telegram user ID (background) — rieltordan avtomatik olinadi"
    )

    # --- Statistika / ko'rsatkichlar ---
    # TODO: Ko'rishlar soni — hozircha comentda, keyinroq qo'shiladi
    # korishlar_soni = models.PositiveIntegerField(default=0)

    # --- Holat / moderatsiya / ko'tarish ---
    holat = models.CharField(
        max_length=10,
        choices=Holat.choices,
        default=Holat.ACTIVE
    )
    is_verified = models.BooleanField(default=False)  # Admin tasdiqlagan
    featured = models.BooleanField(
        default=False,
        help_text="Ko'tarilgan / Spotlight e'lon (yuqorida ko'rsatiladi)"
    )
    featured_tugash = models.DateTimeField(
        blank=True, null=True,
        help_text="Ko'tarish (featured) muddati tugash vaqti"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kvartira'
        verbose_name_plural = 'Kvartiralar'
        ordering = ['-featured', '-created_at']
        indexes = [
            models.Index(fields=['holat', 'ariza_turi']),
            models.Index(fields=['-featured', '-created_at']),
        ]

    def __str__(self):
        return f"{self.sarlavha} — {self.hudud} — {self.narx} {self.valyuta}"

    @property
    def yangimi(self) -> bool:
        """E'lon oxirgi 7 kun ichida qo'shilgan bo'lsa — 'YANGI' belgisi."""
        if not self.created_at:
            return False
        return timezone.now() - self.created_at <= timedelta(days=7)

    @property
    def featured_faolmi(self) -> bool:
        """Ko'tarilgan e'lon hozir amal qiladimi."""
        if not self.featured:
            return False
        if self.featured_tugash and timezone.now() > self.featured_tugash:
            return False
        return True

    # TODO: Sevimlilar (like) — hozircha comentda, frontend Chrome kengaytmasi
    # orqali qilinadi, keyinroq qo'shiladi
    # @property
    # def sevimlilar_soni(self) -> int:
    #     return self.sevimlilar.count()

    # TODO: Ko'rishlar soni — keyinroq qo'shiladi
    # def korish_qoshish(self):
    #     """Ko'rishlar hisoblagichini atomik oshirish."""
    #     Kvartira.objects.filter(pk=self.pk).update(
    #         korishlar_soni=models.F('korishlar_soni') + 1
    #     )


class KvartiraRasm(models.Model):
    """Kvartira rasmlari — alohida model, ko'p rasm bo'lishi mumkin"""
    kvartira = models.ForeignKey(
        Kvartira,
        on_delete=models.CASCADE,
        related_name='rasmlar'
    )
    rasm = models.ImageField(upload_to='kvartiralar/%Y/%m/')
    asosiy = models.BooleanField(default=False)  # Bosh rasm
    tartib = models.PositiveSmallIntegerField(default=0, help_text="Ko'rsatish tartibi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kvartira rasmi'
        verbose_name_plural = 'Kvartira rasmlari'
        ordering = ['-asosiy', 'tartib', 'id']

    def __str__(self):
        return f"{self.kvartira} — rasm"


class KvartiraPlanirovka(models.Model):
    """Planirovka (floor plan) rasmlari — kartochkadagi 'Floor plan'."""
    kvartira = models.ForeignKey(
        Kvartira,
        on_delete=models.CASCADE,
        related_name='planirovkalar'
    )
    rasm = models.ImageField(upload_to='kvartiralar/planirovka/%Y/%m/')
    izoh = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Planirovka'
        verbose_name_plural = 'Planirovkalar'

    def __str__(self):
        return f"{self.kvartira} — planirovka"


# TODO: Sevimlilar (like) modeli — hozircha comentda.
# Frontend buni Chrome kengaytmasi orqali qilmoqchi, keyinroq faollashtiriladi.
# class KvartiraSevimli(models.Model):
#     """Foydalanuvchining sevimli e'lonlari (kartochkadagi ♥ tugma)."""
#     user = models.ForeignKey(
#         CustomUser,
#         on_delete=models.CASCADE,
#         related_name='sevimli_kvartiralar'
#     )
#     kvartira = models.ForeignKey(
#         Kvartira,
#         on_delete=models.CASCADE,
#         related_name='sevimlilar'
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         verbose_name = 'Sevimli'
#         verbose_name_plural = 'Sevimlilar'
#         unique_together = ['user', 'kvartira']
#         ordering = ['-created_at']
#
#     def __str__(self):
#         return f"{self.user} ♥ {self.kvartira}"
