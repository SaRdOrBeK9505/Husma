from apps.makler.models import MaklerProfil
from .models import Ariza, ArizaMakler


def arizani_rieltorlarga_yuborish(ariza: Ariza) -> int:
    """
    Ariza yuborilganda shu hudud va mulk turi bilan ishlaydigan
    faol rieltorlarga avtomatik yuboradi.

    Faol = admin bloklamagan (verify_holat != rejected) VA
           (bepul sinov muddatida YOKI faol obunasi bor).
    Nechta rieltorga yuborilganini qaytaradi.
    """
    # Shu hududda ishlaydigan, bloklanmagan, aktiv rieltorlar.
    # verify_holat=rejected — admin bloklagan, ularni chiqarib tashlaymiz.
    rieltorlar = MaklerProfil.objects.filter(
        hududlar=ariza.hudud,
        user__is_active=True,
    ).exclude(
        verify_holat=MaklerProfil.VerifyHolat.REJECTED,
    )

    # Agar arizani rieltor yuborayotgan bo'lsa, o'zini chiqarib tashlaymiz
    if ariza.user.role == 'makler':
        rieltorlar = rieltorlar.exclude(user=ariza.user)

    # Mulk turi bo'yicha ham filtrlash (ariza mulk turi ko'rsatilgan bo'lsa)
    if ariza.mulk_turi_id:
        rieltorlar = rieltorlar.filter(mulk_turlari=ariza.mulk_turi)

    rieltorlar = rieltorlar.distinct()

    yuborildi = 0
    for rieltor in rieltorlar:
        # Har birining faolligini (blok + bepul muddat yoki obuna) tekshiramiz
        if not rieltor.faol:
            continue
        _, created = ArizaMakler.objects.get_or_create(
            ariza=ariza,
            rieltor=rieltor,
        )
        if created:
            yuborildi += 1

    return yuborildi


# Backward compatibility
arizani_maklerlarga_yuborish = arizani_rieltorlarga_yuborish


def yangi_rieltorga_eski_arizalarni_biriktir(rieltor, kun_chegarasi=30) -> int:
    """
    Yangi ro'yxatdan o'tgan rieltor uchun uning hudud va mulk_turlari bo'yicha
    oxirgi `kun_chegarasi` kun ichida yaratilgan ochiq arizalarni avtomatik biriktiradi.

    BU FUNKSIYANI registratsiya view'ida, rieltor.hududlar.set(...) va
    rieltor.mulk_turlari.set(...) chaqirilgandan KEYIN ishlatish kerak.
    post_save signal'ga ulash XATO — ManyToMany maydonlar signal paytida
    hali bo'sh bo'ladi.

    ignore_conflicts=True: ArizaMaklerda unique_together=['ariza','rieltor'] bor,
    shuning uchun funksiya ikki marta chaqirilsa ham dublikat yaratilmaydi.

    Qaytaradi: yangi yaratilgan ArizaMakler yozuvlari soni.
    """
    from datetime import timedelta
    from django.utils import timezone

    chegara_vaqt = timezone.now() - timedelta(days=kun_chegarasi)

    mos_arizalar = Ariza.objects.filter(
        holat__in=[Ariza.Holat.YANGI, Ariza.Holat.KORILMOQDA],
        created_at__gte=chegara_vaqt,
        mulk_turi__in=rieltor.mulk_turlari.all(),
        hudud__in=rieltor.hududlar.all(),
    ).exclude(
        ariza_rieltorlar__rieltor=rieltor,
    )

    yangi_yozuvlar = [
        ArizaMakler(ariza=ariza, rieltor=rieltor)
        for ariza in mos_arizalar
    ]

    ArizaMakler.objects.bulk_create(yangi_yozuvlar, ignore_conflicts=True)
    return len(yangi_yozuvlar)