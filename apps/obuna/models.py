from django.db import models
from django.utils import timezone


class Tarif(models.Model):
    """
    Obuna tarif rejasi (masalan: Oylik, Choraklik, Yillik).
    Admin paneldan boshqariladi. Narx va davomiylik shu yerda belgilanadi.
    """
    nomi = models.CharField(max_length=100, help_text="Masalan: 'Oylik obuna'")
    kod = models.SlugField(
        max_length=50, unique=True,
        help_text="Texnik kod, masalan: 'oylik', 'yillik'"
    )
    narx = models.PositiveIntegerField(help_text="So'mda")
    davomiylik_kun = models.PositiveIntegerField(
        help_text="Obuna necha kun amal qiladi (masalan: 30, 90, 365)"
    )
    izoh = models.TextField(blank=True, null=True)
    tartib = models.PositiveSmallIntegerField(
        default=0, help_text="Ro'yxatdagi tartibi (kichikroq = oldin)"
    )
    is_active = models.BooleanField(
        default=True, help_text="False bo'lsa frontendda ko'rinmaydi va sotib olib bo'lmaydi"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tarif'
        verbose_name_plural = 'Tariflar'
        ordering = ['tartib', 'narx']

    def __str__(self):
        return f"{self.nomi} — {self.narx:,} so'm / {self.davomiylik_kun} kun"


class ObunaQuerySet(models.QuerySet):
    def faol(self):
        """Hozir amal qilayotgan obunalar: holat=faol VA tugash vaqti o'tmagan."""
        now = timezone.now()
        return self.filter(holat=Obuna.Holat.FAOL, tugash_vaqti__gt=now)


class Obuna(models.Model):
    """
    Rieltorning konkret obuna davri.
    Bitta rieltorda vaqt o'tishi bilan bir nechta obuna bo'lishi mumkin (tarix),
    lekin ayni paytda faqat bittasi `faol` bo'ladi.
    """

    class Holat(models.TextChoices):
        KUTILMOQDA = 'kutilmoqda', 'To\'lov kutilmoqda'
        FAOL = 'faol', 'Faol'
        TUGAGAN = 'tugagan', 'Muddati tugagan'
        BEKOR = 'bekor', 'Bekor qilingan'

    rieltor = models.ForeignKey(
        'makler.MaklerProfil',
        on_delete=models.CASCADE,
        related_name='obunalar'
    )
    tarif = models.ForeignKey(
        Tarif,
        on_delete=models.PROTECT,
        related_name='obunalar'
    )
    holat = models.CharField(
        max_length=15,
        choices=Holat.choices,
        default=Holat.KUTILMOQDA
    )
    # Tarif narxi vaqt o'tishi bilan o'zgarishi mumkin — shuning uchun
    # sotib olingan paytdagi narxni shu yerda "muzlatib" saqlaymiz.
    narx = models.PositiveIntegerField(help_text="Sotib olingan paytdagi narx (so'm)")

    boshlanish_vaqti = models.DateTimeField(blank=True, null=True)
    tugash_vaqti = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ObunaQuerySet.as_manager()

    class Meta:
        verbose_name = 'Obuna'
        verbose_name_plural = 'Obunalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rieltor} — {self.tarif.nomi} ({self.holat})"

    @property
    def faolmi(self) -> bool:
        return (
            self.holat == self.Holat.FAOL
            and self.tugash_vaqti is not None
            and timezone.now() <= self.tugash_vaqti
        )

    def faollashtirish(self):
        """
        To'lov tasdiqlangach obunani faollashtiradi.
        Boshlanish — hozir, tugash — tarif davomiyligiga qarab.
        Agar rieltorda hali tugamagan obuna bo'lsa, uning ustiga davom ettiriladi.
        """
        now = timezone.now()

        # Mavjud faol obuna bo'lsa, yangi muddat uning tugashidan boshlanadi (stacking)
        joriy = self.rieltor.obunalar.faol().order_by('-tugash_vaqti').first()
        boshlanish = joriy.tugash_vaqti if joriy and joriy.id != self.id else now

        from datetime import timedelta
        self.boshlanish_vaqti = boshlanish
        self.tugash_vaqti = boshlanish + timedelta(days=self.tarif.davomiylik_kun)
        self.holat = self.Holat.FAOL
        self.save(update_fields=['boshlanish_vaqti', 'tugash_vaqti', 'holat', 'updated_at'])

        # Rieltorga Telegram orqali xabar (xato bo'lsa jim o'tadi)
        try:
            from .notifications import obuna_faollashdi_xabar
            obuna_faollashdi_xabar(self)
        except Exception:
            pass


class Tolov(models.Model):
    """
    Obuna uchun to'lov tranzaksiyasi.
    Payme / Click integratsiyasi uchun struktura tayyor — hozircha `manual`
    (admin qo'lda tasdiqlash) ham qo'llab-quvvatlanadi.
    """

    class Provayder(models.TextChoices):
        PAYME     = 'payme',     'Payme'
        CLICK     = 'click',     'Click'
        MANUAL    = 'manual',    'Qo\'lda (admin)'
        MULTICARD = 'multicard', 'Multicard'

    class Holat(models.TextChoices):
        KUTILMOQDA = 'kutilmoqda', 'Kutilmoqda'
        MUVAFFAQIYATLI = 'muvaffaqiyatli', 'Muvaffaqiyatli'
        BEKOR = 'bekor', 'Bekor qilingan'
        XATO = 'xato', 'Xato'

    obuna = models.ForeignKey(
        Obuna,
        on_delete=models.CASCADE,
        related_name='tolovlar'
    )
    provayder = models.CharField(
        max_length=10,
        choices=Provayder.choices,
        default=Provayder.MANUAL
    )
    summa = models.PositiveIntegerField(help_text="To'lov summasi (so'm)")
    holat = models.CharField(
        max_length=15,
        choices=Holat.choices,
        default=Holat.KUTILMOQDA
    )
    # Tashqi to'lov tizimidagi tranzaksiya ID (Payme/Click qaytaradi)
    tashqi_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Payme/Click tranzaksiya identifikatori"
    )
    # Provayderdan kelgan to'liq javobni saqlash (debug / audit uchun)
    metadata = models.JSONField(default=dict, blank=True)

    tolangan_vaqt = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.obuna} — {self.summa:,} so'm ({self.holat})"

    def muvaffaqiyatli_deb_belgilash(self):
        """
        To'lovni muvaffaqiyatli deb belgilaydi va bog'liq obunani faollashtiradi.
        Payme/Click callback yoki admin qo'lda tasdiqlashidan chaqiriladi.
        """
        self.holat = self.Holat.MUVAFFAQIYATLI
        self.tolangan_vaqt = timezone.now()
        self.save(update_fields=['holat', 'tolangan_vaqt', 'updated_at'])
        self.obuna.faollashtirish()

    def bekor_deb_belgilash(self):
        """To'lovni bekor qilingan deb belgilaydi."""
        self.holat = self.Holat.BEKOR
        self.save(update_fields=['holat', 'updated_at'])


class PaymeTransaction(models.Model):
    """
    Payme Merchant API tranzaksiyasi.
    Payme o'zining state-machine'siga ega bo'lgani uchun alohida modelda
    saqlanadi va bizning `Tolov` modeliga bog'lanadi.

    State qiymatlari Payme protokoli bo'yicha:
        1   — yaratilgan (CreateTransaction)
        2   — yakunlangan (PerformTransaction)
       -1   — yaratilgan holatda bekor qilingan
       -2   — yakunlangandan keyin bekor qilingan
    """
    STATE_CREATED = 1
    STATE_COMPLETED = 2
    STATE_CANCELLED = -1
    STATE_CANCELLED_AFTER_COMPLETE = -2

    tolov = models.OneToOneField(
        Tolov,
        on_delete=models.CASCADE,
        related_name='payme_transaction'
    )
    payme_id = models.CharField(
        max_length=255, unique=True,
        help_text="Payme tomonidagi tranzaksiya identifikatori"
    )
    # Payme summani tiyinda yuboradi (so'm * 100)
    amount = models.BigIntegerField(help_text="Summa (tiyin)")
    state = models.IntegerField(default=STATE_CREATED)
    reason = models.IntegerField(
        blank=True, null=True,
        help_text="Bekor qilish sababi kodi (Payme)"
    )
    # Payme vaqtlari — Unix millisekund (epoch ms)
    create_time = models.BigIntegerField(default=0)
    perform_time = models.BigIntegerField(default=0)
    cancel_time = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payme tranzaksiya'
        verbose_name_plural = 'Payme tranzaksiyalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payme {self.payme_id} — state={self.state}"
