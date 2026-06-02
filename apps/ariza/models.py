from django.db import models
from apps.users.models import CustomUser
from apps.hudud.models import Hudud


class Ariza(models.Model):

    class ArizaTuri(models.TextChoices):
        IJARA = 'ijara', 'Ijaraga olish'
        SOTIB_OLISH = 'sotib_olish', 'Sotib olish'

    class XonalarSoni(models.TextChoices):
        BIR = '1', '1 xonali'
        IKKI = '2', '2 xonali'
        UCH = '3', '3 xonali'
        TORT = '4+', '4+ xonali'

    class Holat(models.TextChoices):
        YANGI = 'yangi', 'Yangi'
        KORILMOQDA = 'korilmoqda', 'Ko\'rilmoqda'
        YOPILGAN = 'yopilgan', 'Yopilgan'

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='arizalar'
    )
    hudud = models.ForeignKey(
        Hudud,
        on_delete=models.SET_NULL,
        null=True,
        related_name='arizalar'
    )

    ism = models.CharField(max_length=100, blank=True, null=True)
    ariza_turi = models.CharField(
        max_length=15,
        choices=ArizaTuri.choices,
    )
    xonalar_soni = models.CharField(
        max_length=5,
        choices=XonalarSoni.choices,
    )
    narx_min = models.BigIntegerField()
    narx_max = models.BigIntegerField()
    telefon = models.CharField(max_length=20, blank=True, null=True)
    qoshimcha_izoh = models.TextField(blank=True, null=True)
    holat = models.CharField(
        max_length=15,
        choices=Holat.choices,
        default=Holat.YANGI
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ariza'
        verbose_name_plural = 'Arizalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.xonalar_soni} xona — {self.hudud}"


class ArizaMakler(models.Model):
    """Ariza qaysi rieltorlarga yuborilgani"""

    class Holat(models.TextChoices):
        YANGI = 'yangi', 'Yangi'
        KORILDI = 'korildi', 'Ko\'rildi'
        BOGLANDI = 'boglandi', 'Bog\'landi'
        YOPILDI = 'yopildi', 'Yopildi'

    ariza = models.ForeignKey(
        Ariza,
        on_delete=models.CASCADE,
        related_name='ariza_rieltorlar'
    )
    rieltor = models.ForeignKey(
        'makler.MaklerProfil',
        on_delete=models.CASCADE,
        related_name='ariza_rieltorlar'
    )
    holat = models.CharField(
        max_length=15,
        choices=Holat.choices,
        default=Holat.YANGI
    )
    korilgan_vaqt = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ariza-Rieltor'
        verbose_name_plural = 'Ariza-Rieltorlar'
        unique_together = ['ariza', 'rieltor']

    def __str__(self):
        return f"{self.ariza} → {self.rieltor}"