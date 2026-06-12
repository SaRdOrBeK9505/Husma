from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import CustomUser
from apps.hudud.models import Hudud, MulkTuri


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
    mulk_turlari = models.ManyToManyField(
        MulkTuri,
        blank=True,
        related_name='rieltorlar',
        help_text="Rieltor qaysi mulk turlari bilan ishlaydi"
    )
    verify_holat = models.CharField(
        max_length=10,
        choices=VerifyHolat.choices,
        default=VerifyHolat.VERIFIED  # Ro'yxatdan o'tganda darhol verified
    )
    verify_qilingan_vaqt = models.DateTimeField(blank=True, null=True)

    # Obuna tizimi uchun — keyinchalik to'ldiriladi
    # Hozir ro'yxatdan o'tgan kundan 7 kun bepul sinov muddati beriladi
    bepul_muddat_tugash = models.DateTimeField(
        blank=True, null=True,
        help_text="Bepul sinov muddati tugash vaqti (ro'yxatdan o'tgandan 7 kun)"
    )
    obuna_faol = models.BooleanField(
        default=False,
        help_text="To'liq obuna faolmi (keyinchalik qo'shiladi)"
    )
    obuna_tugash = models.DateTimeField(
        blank=True, null=True,
        help_text="Obuna tugash vaqti (keyinchalik qo'shiladi)"
    )

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

    @property
    def faol(self) -> bool:
        """
        Rieltor hozir ishlashi mumkinmi.
        Ikkita holat: bepul muddat ichida YOKI faol obuna bor.
        Keyinchalik obuna tizimi qo'shilganda faqat shu property o'zgaradi.
        """
        now = timezone.now()

        # Bepul sinov muddati ichidami
        if self.bepul_muddat_tugash and now <= self.bepul_muddat_tugash:
            return True

        # Faol obuna bormi (keyinchalik qo'shiladi)
        if self.obuna_faol and self.obuna_tugash and now <= self.obuna_tugash:
            return True

        return False