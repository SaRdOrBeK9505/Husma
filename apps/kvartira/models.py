from django.db import models
from apps.users.models import CustomUser
from apps.hudud.models import Hudud


class Kvartira(models.Model):

    class ArizaTuri(models.TextChoices):
        IJARA = 'ijara', 'Ijaraga berish'
        SOTISH = 'sotish', 'Sotish'

    class XonalarSoni(models.TextChoices):
        BIR = '1', '1 xonali'
        IKKI = '2', '2 xonali'
        UCH = '3', '3 xonali'
        TORT = '4', '4 xonali'
        BESH_ORTIQ = '5+', '5 va undan ko\'p'

    class Holat(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        SOLD = 'sold', 'Sotilgan/Ijarada'
        ARCHIVED = 'archived', 'Arxivlangan'

    # Kim qo'shgan
    qoshgan = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kvartiralar'
    )
    hudud = models.ForeignKey(
        Hudud,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kvartiralar'
    )

    sarlavha = models.CharField(max_length=255)
    tavsif = models.TextField(blank=True, null=True)
    ariza_turi = models.CharField(max_length=10, choices=ArizaTuri.choices)
    xonalar_soni = models.CharField(max_length=5, choices=XonalarSoni.choices)
    narx = models.BigIntegerField()
    maydon_m2 = models.FloatField(blank=True, null=True)
    qavat = models.PositiveSmallIntegerField(blank=True, null=True)
    jami_qavat = models.PositiveSmallIntegerField(blank=True, null=True)
    manzil = models.CharField(max_length=255, blank=True, null=True)
    holat = models.CharField(
        max_length=10,
        choices=Holat.choices,
        default=Holat.ACTIVE
    )
    is_verified = models.BooleanField(default=False)  # Admin tasdiqlagan

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kvartira'
        verbose_name_plural = 'Kvartiralar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sarlavha} — {self.hudud} — {self.narx}"


class KvartiraRasm(models.Model):
    """Kvartira rasmlari — alohida model, ko'p rasm bo'lishi mumkin"""
    kvartira = models.ForeignKey(
        Kvartira,
        on_delete=models.CASCADE,
        related_name='rasmlar'
    )
    rasm = models.ImageField(upload_to='kvartiralar/%Y/%m/')
    asosiy = models.BooleanField(default=False)  # Bosh rasm
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kvartira rasmi'
        verbose_name_plural = 'Kvartira rasmlari'

    def __str__(self):
        return f"{self.kvartira} — rasm"