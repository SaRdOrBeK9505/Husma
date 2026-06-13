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