from django.db import models
from apps.users.models import CustomUser
from apps.hudud.models import Hudud


class MaklerProfil(models.Model):

    class VerifyHolat(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        VERIFIED = 'verified', 'Tasdiqlangan'
        REJECTED = 'rejected', 'Rad etilgan'

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='rieltor_profil'
    )
    bio = models.TextField(blank=True, null=True)
    telegram_link = models.CharField(max_length=100, blank=True, null=True)
    hududlar = models.ManyToManyField(
        Hudud,
        blank=True,
        related_name='rieltorlar'
    )
    verify_holat = models.CharField(
        max_length=10,
        choices=VerifyHolat.choices,
        default=VerifyHolat.PENDING
    )
    verify_qilingan_vaqt = models.DateTimeField(blank=True, null=True)
    ortacha_reyting = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    jami_bitimlar = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rieltor profil'
        verbose_name_plural = 'Rieltor profillari'

    def __str__(self):
        return f"{self.user} — {self.verify_holat}"