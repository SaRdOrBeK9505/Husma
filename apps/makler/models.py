from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import CustomUser
from apps.hudud.models import Hudud, MulkTuri


class MaklerProfil(models.Model):

    class VerifyHolat(models.TextChoices):
        """
        Rieltor profilining admin tomonidan boshqariladigan holati.

        MUHIM: Bu maydon rieltorning "ishlashga huquqi"ni (obuna/bepul muddat)
        belgilamaydi — buni `faol` property hal qiladi. Bu maydon ADMIN uchun
        qo'lda boshqaruv (moderatsiya / bloklash) vositasi:

        - VERIFIED  : Profil ruxsat etilgan (default). Rieltor normal ishlaydi.
        - REJECTED  : Admin tomonidan BLOKLANGAN. Obuna/bepul muddati bo'lsa ham
                      rieltor arizalarga kira olmaydi va unga ariza tarqatilmaydi.
        - PENDING   : Kelajakda qo'lda tasdiqlash oqimi joriy qilinsa ishlatish
                      uchun zaxiraga qoldirilgan. Hozircha registratsiyada
                      ishlatilmaydi (yangi rieltor darhol VERIFIED bo'ladi).
        """
        PENDING = 'pending', 'Kutilmoqda'
        VERIFIED = 'verified', 'Tasdiqlangan'
        REJECTED = 'rejected', 'Bloklangan'

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
        default=VerifyHolat.VERIFIED,  # Ro'yxatdan o'tganda darhol verified
        help_text=(
            "Admin moderatsiya holati. 'Bloklangan' (rejected) qilinsa, "
            "obuna/bepul muddatidan qat'i nazar rieltor ishlay olmaydi."
        ),
    )
    verify_qilingan_vaqt = models.DateTimeField(blank=True, null=True)

    # Bepul sinov muddati — ro'yxatdan o'tgan kundan 7 kun beriladi.
    # To'liq obuna ma'lumotlari endi alohida `apps.obuna.Obuna` modelida saqlanadi.
    bepul_muddat_tugash = models.DateTimeField(
        blank=True, null=True,
        help_text="Bepul sinov muddati tugash vaqti (ro'yxatdan o'tgandan 7 kun)"
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
    def bloklangan(self) -> bool:
        """Admin tomonidan bloklanganmi (verify_holat = rejected)."""
        return self.verify_holat == self.VerifyHolat.REJECTED

    @property
    def obuna_faol(self) -> bool:
        """
        Rieltorda hozir amal qilayotgan (to'langan, muddati o'tmagan) obuna bormi.
        Yagona haqiqat manbai — `apps.obuna.Obuna` modeli.
        """
        obuna = getattr(self, 'joriy_obuna', None)
        if obuna is None:
            # related_name orqali eng so'nggi faol obunani qidiramiz
            obuna = self.obunalar.faol().order_by('-tugash_vaqti').first()
        return obuna is not None

    @property
    def obuna_tugash(self):
        """Joriy faol obunaning tugash vaqti (bo'lmasa None)."""
        obuna = self.obunalar.faol().order_by('-tugash_vaqti').first()
        return obuna.tugash_vaqti if obuna else None

    @property
    def faol(self) -> bool:
        """
        Rieltor hozir ishlashi (arizalarni ko'rishi va olishi) mumkinmi.

        Tartib:
        1. Admin bloklagan bo'lsa (verify_holat=rejected) — DOIM False.
        2. Bepul sinov muddati ichida bo'lsa — True.
        3. Faol (to'langan) obunasi bo'lsa — True.
        4. Aks holda — False.
        """
        # 1. Admin bloki hamma narsadan ustun
        if self.bloklangan:
            return False

        now = timezone.now()

        # 2. Bepul sinov muddati ichidami
        if self.bepul_muddat_tugash and now <= self.bepul_muddat_tugash:
            return True

        # 3. Faol obuna bormi
        if self.obuna_faol:
            return True

        return False