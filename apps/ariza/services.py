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
            # Yangi ariza biriktirilganda notification yuborish
            _xabar_navbatiga_qosh(rieltor, ariza)

    return yuborildi


# Backward compatibility
arizani_maklerlarga_yuborish = arizani_rieltorlarga_yuborish


def _xabar_navbatiga_qosh(rieltor, ariza) -> None:
    """
    Celery orqali rieltorga yangi ariza haqida Telegram xabari yuboradi.

    Bu funksiya HTTP request ichida sinxron Telegram API chaqirig'i qilmaydi.
    Buning o'rniga Celery task'ni background'da ishga tushiradi.

    Idempotent: bir xil ariza_makler uchun bir necha marta chaqirilsa ham,
    faqat bitta xabar yuboriladi (task ichida holat tekshiriladi).

    Parametrlar:
        rieltor: MaklerProfil — xabar yuborish kerak bo'lgan rieltor
        ariza:   Ariza        — yangi biriktirilgan ariza
    """
    from .tasks import yangi_ariza_xabari_yubor

    # ArizaMaklerni topish
    ariza_makler = ArizaMakler.objects.filter(
        ariza=ariza,
        rieltor=rieltor
    ).first()

    if ariza_makler:
        # Celery task'ni background'da ishga tushirish
        yangi_ariza_xabari_yubor.delay(ariza_makler.id)


def yangi_rieltorga_eski_arizalarni_biriktir(
    rieltor,
    kun_chegarasi: int = 30,
    xabar_yubor: bool = False,
) -> int:
    """
    Berilgan rieltorning hududlar/mulk_turlari'iga mos keluvchi,
    hali yopilmagan (holat != yopilgan) va belgilangan vaqt oralig'idagi
    arizalarni topib, ArizaMakler orqali rieltorga biriktiradi.
    Allaqachon biriktirilganlarni qayta qo'shmaydi (idempotent).

    Parametrlar:
        rieltor        : MaklerProfil — kimga biriktirish kerak
        kun_chegarasi  : int  — necha kun oldingi arizalargacha (standart: 30)
        xabar_yubor    : bool — True bo'lsa har bir yangi biriktirilgan ariza
                                uchun _xabar_navbatiga_qosh() chaqiriladi.
                                Eski arizalar uchun (backfill) DOIM False qoldirilsin —
                                eski arizalarga "yangi ariza keldi" signali yuborish noto'g'ri.

    MUHIM — ManyToMany vaqt tartibi:
        Bu funksiyani rieltor.hududlar.set(...) va rieltor.mulk_turlari.set(...)
        chaqirilgandan KEYIN ishlatish kerak. post_save signal'ga ulash XATO —
        ManyToMany maydonlar signal paytida hali bo'sh bo'ladi (loyihada ilgari
        shunga o'xshash token tartibi xatosi yuz bergan edi).

    Idempotentlik:
        ignore_conflicts=True ishlatilgan: ArizaMaklerda unique_together=['ariza','rieltor']
        bor, shuning uchun funksiya ikki marta chaqirilsa ham dublikat yaratilmaydi.

    Qaytaradi: yangi yaratilgan ArizaMakler yozuvlari soni.
    """
    from datetime import timedelta
    from django.utils import timezone

    chegara_vaqt = timezone.now() - timedelta(days=kun_chegarasi)

    mos_arizalar = list(
        Ariza.objects.filter(
            holat__in=[Ariza.Holat.YANGI, Ariza.Holat.KORILMOQDA],
            created_at__gte=chegara_vaqt,
            mulk_turi__in=rieltor.mulk_turlari.all(),
            hudud__in=rieltor.hududlar.all(),
        ).exclude(
            ariza_rieltorlar__rieltor=rieltor,
        )
    )

    yangi_yozuvlar = [
        ArizaMakler(ariza=ariza, rieltor=rieltor)
        for ariza in mos_arizalar
    ]

    ArizaMakler.objects.bulk_create(yangi_yozuvlar, ignore_conflicts=True)

    # Agar xabar_yubor=True bo'lsa (masalan, yangi registratsiyada),
    # har bir yangi biriktirilgan ariza uchun xabar navbatiga qo'shamiz.
    # Eski arizalar (backfill/update) uchun xabar_yubor=False qoldirilsin.
    if xabar_yubor:
        for ariza in mos_arizalar:
            _xabar_navbatiga_qosh(rieltor, ariza)

    return len(yangi_yozuvlar)
