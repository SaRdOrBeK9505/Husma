from django.db import models


class SiteSettings(models.Model):
    """
    Singleton model — faqat BITTA yozuv bo'ladi.
    Admin paneldan o'zgartiriladi.
    """

    # ===== HERO BANNER =====
    hero_sarlavha = models.CharField(
        max_length=255,
        default="Orzuingizdagi kvartirani topamiz"
    )
    hero_tavsif = models.CharField(
        max_length=500,
        default="Professional rieltor sizga ideal variantni tanlashda yordam beradi"
    )
    hero_rasm = models.ImageField(
        upload_to='settings/',
        blank=True, null=True
    )

    # ===== MINIMAL KOMISSIYA BANNER =====
    komissiya_foiz = models.CharField(
        max_length=20,
        default="1%",
        help_text="Faqat 1%"
    )
    komissiya_tavsif = models.CharField(
        max_length=255,
        default="Eng arzon narxlar shaharda!"
    )

    # ===== NEGA BIZNI TANLASHADI =====
    ustunlik_1_sarlavha = models.CharField(
        max_length=100,
        default="Professional tanlov"
    )
    ustunlik_1_tavsif = models.CharField(
        max_length=255,
        default="Faqat tajribali rieltorlardan tekshirilgan variantlar"
    )

    ustunlik_2_sarlavha = models.CharField(
        max_length=100,
        default="Minimal komissiya 1%"
    )
    ustunlik_2_tavsif = models.CharField(
        max_length=255,
        default="Eng yaxshi narx bo'yicha kelishishga yordam beramiz"
    )

    ustunlik_3_sarlavha = models.CharField(
        max_length=100,
        default="Yuridik tozalik"
    )
    ustunlik_3_tavsif = models.CharField(
        max_length=255,
        default="Bitim oldidan barcha hujjatlarni tekshiramiz"
    )

    # ===== BU QANDAY ISHLAYDI =====
    qadam_1_sarlavha = models.CharField(
        max_length=100,
        default="Ariza qoldiring"
    )
    qadam_1_tavsif = models.CharField(
        max_length=255,
        default="Kvartira talablaringizni va aloqa ma'lumotlaringizni ko'rsating"
    )

    qadam_2_sarlavha = models.CharField(
        max_length=100,
        default="Variantlar tanlash"
    )
    qadam_2_tavsif = models.CharField(
        max_length=255,
        default="Rieltor sizning mezonlaringizga mos kvartilarni topadi"
    )

    qadam_3_sarlavha = models.CharField(
        max_length=100,
        default="Bitimni tuzish"
    )
    qadam_3_tavsif = models.CharField(
        max_length=255,
        default="Yuridik rasmiylashirish va hujjatlar bilan yordam beramiz"
    )

    # ===== RIELTOR MASLAHATI (Ariza forma) =====
    rieltor_maslahati_forma = models.TextField(
        default="Qanchalik batafsil talablaringizni yozsangiz, ideal variantni shunchalik tezroq topamiz!"
    )

    # ===== XAVFSIZLIK KAFOLATI =====
    xavfsizlik_sarlavha = models.CharField(
        max_length=100,
        default="Xavfsizlik kafolati"
    )
    xavfsizlik_tavsif = models.TextField(
        default="Biz faqat tekshirilgan ob'ektlar bilan ishlaymiz va barcha bitimlarning yuridik tozaligiga kafolat beramiz"
    )
    xavfsizlik_qoshimcha = models.CharField(
        max_length=255,
        default="Ko'chmas mulk bozorida 5 yildan ortiq"
    )

    # ===== RIELTOR PANELI TAVSIYALAR =====
    tavsiya_1 = models.TextField(
        default="Arizalarga 2 soat ichida javob bering - bu konversiyani 45% ga oshiradi"
    )
    tavsiya_2 = models.TextField(
        default="Mijoz tanlashi uchun bir nechta kvartira variantlarini taklif qiling"
    )

    # ===== FOOTER =====
    copyright_matn = models.CharField(
        max_length=255,
        default="© 2026 Kvartira Qidiruv. Barcha huquqlar himoyalangan"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sayt sozlamalari'
        verbose_name_plural = 'Sayt sozlamalari'

    def __str__(self):
        return "Sayt sozlamalari"

    def save(self, *args, **kwargs):
        """Singleton — faqat bitta yozuv"""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Har doim bitta settings obyektini qaytaradi"""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SliderKarta(models.Model):
    """
    Slider kartochkalari — user va rieltor paneli uchun alohida.
    Admin qo'shadi, tahrirlaydi, o'chiradi.
    """

    class PanelTuri(models.TextChoices):
        USER = 'user', 'User paneli'
        RIELTOR = 'rieltor', 'Rieltor paneli'

    panel_turi = models.CharField(
        max_length=10,
        choices=PanelTuri.choices,
        help_text="Qaysi panel uchun ko'rsatilsin"
    )
    badge_matn = models.CharField(
        max_length=100,
        help_text="Badge ustidagi kichik matn (masalan: 'Husma Estate', 'Rieltor paneli')"
    )
    sarlavha = models.CharField(
        max_length=150,
        blank=True, null=True,
        help_text="Kichik sarlavha (masalan: 'Bugungi holat') — ixtiyoriy"
    )
    title = models.CharField(
        max_length=255,
        help_text="Asosiy katta sarlavha"
    )
    description = models.TextField(
        blank=True, null=True,
        help_text="Qo'shimcha tavsif matni — ixtiyoriy"
    )
    tartib = models.PositiveSmallIntegerField(
        default=0,
        help_text="Sliderda tartib raqami (kichikroq = oldin chiqadi)"
    )
    faol = models.BooleanField(
        default=True,
        help_text="False qilsangiz frontendda ko'rinmaydi"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Slider kartochka'
        verbose_name_plural = 'Slider kartochkalar'
        ordering = ['panel_turi', 'tartib']

    def __str__(self):
        return f"[{self.get_panel_turi_display()}] {self.title}"


class KontaktMalumot(models.Model):
    """
    Singleton model — "Biz bilan bog'laning" sahifasi uchun.
    Telefon, email, telegram, ofis manzilini saqlaydi.
    """
    telefon = models.CharField(
        max_length=20,
        default="+998 99 123-45-67",
        help_text="Masalan: +998 99 123-45-67"
    )
    email = models.EmailField(
        default="info@kvartira.uz"
    )
    telegram_bot = models.CharField(
        max_length=100,
        default="@kvartira_bot",
        help_text="Telegram bot yoki kanal nomi"
    )
    ofis_manzil = models.CharField(
        max_length=255,
        default="Amir Temur ko'chasi, 1"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kontakt ma'lumot"
        verbose_name_plural = "Kontakt ma'lumot"

    def __str__(self):
        return "Kontakt ma'lumot"

    def save(self, *args, **kwargs):
        """Singleton — faqat bitta yozuv"""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Har doim bitta kontakt obyektini qaytaradi"""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class UserStatistika(models.Model):
    """
    Singleton model — User paneli uchun statik statistika.
    Admin paneldan o'zgartiriladi.
    """
    bitimlar = models.PositiveIntegerField(
        default=500,
        help_text="Masalan: 500 → frontendda '500+' ko'rinadi"
    )
    rieltor_soni = models.PositiveIntegerField(
        default=50,
        help_text="Masalan: 50 → frontendda '50+' ko'rinadi"
    )
    javob_vaqti = models.CharField(
        max_length=10,
        default="2s",
        help_text="Javob vaqti (2s, 5min, ...)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User statistikasi"
        verbose_name_plural = "User statistikasi"

    def __str__(self):
        return "User statistikasi"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj