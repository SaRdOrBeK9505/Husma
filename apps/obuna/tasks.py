"""
Celery vazifalar — obuna avtomatik boshqaruvi.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from celery import shared_task

from .models import Obuna, Tolov
from apps.makler.models import MaklerProfil

logger = logging.getLogger(__name__)


@shared_task
def bekor_qilish_kutilayotgan_obunalar():
    """
    30 daqiqadan ortiq kutilayotgan (KUTILMOQDA holatidagi) obunalarni bekor qiladi.
    
    Celery Beat tomonidan har 15 daqiqada ishga tushiriladi.
    
    Mantiq:
      - Obuna holati = KUTILMOQDA
      - created_at dan 30 daqiqa o'tgan
      - Holat → BEKOR
      - Bog'langan barcha KUTILMOQDA to'lovlar → BEKOR
    """
    now = timezone.now()
    timeout_vaqt = now - timedelta(minutes=30)
    
    # Kutilayotgan va 30 daqiqadan katta obunalarni topish
    eski_obunalar = Obuna.objects.filter(
        holat=Obuna.Holat.KUTILMOQDA,
        created_at__lt=timeout_vaqt,
    ).select_related('rieltor__user')
    
    bekor_qilingan_soni = 0
    
    for obuna in eski_obunalar:
        try:
            # Atomik tranzaksiya — agar xato bo'lsa hech narsa o'zgarmaydi
            with transaction.atomic():
                # Obunani bekor qilish
                obuna.holat = Obuna.Holat.BEKOR
                obuna.save(update_fields=['holat', 'updated_at'])
                
                # Bog'langan barcha kutilayotgan to'lovlarni bekor qilish
                bekor_tolovlar = obuna.tolovlar.filter(
                    holat=Tolov.Holat.KUTILMOQDA
                ).update(holat=Tolov.Holat.BEKOR)
            
            bekor_qilingan_soni += 1
            
            logger.info(
                "[Obuna Auto-Cancel] Obuna bekor qilindi: id=%s rieltor=%s "
                "yaratilgan=%s tolovlar=%s",
                obuna.id,
                obuna.rieltor.user.telegram_id if obuna.rieltor.user else 'unknown',
                obuna.created_at,
                bekor_tolovlar,
            )
            
            # Ixtiyoriy: Rieltorga Telegram xabarnoma (agar kerak bo'lsa)
            # try:
            #     from .notifications import obuna_bekor_xabar
            #     obuna_bekor_xabar(obuna)
            # except Exception:
            #     pass
            
        except Exception as exc:
            logger.error(
                "[Obuna Auto-Cancel] Xato: obuna_id=%s err=%s",
                obuna.id, exc, exc_info=True
            )
    
    if bekor_qilingan_soni > 0:
        logger.info(
            "[Obuna Auto-Cancel] Umumiy: %s ta obuna bekor qilindi",
            bekor_qilingan_soni
        )
    else:
        logger.info("[Obuna Auto-Cancel] Bekor qilinadigan obuna topilmadi")
    
    return {
        "bekor_qilingan_soni": bekor_qilingan_soni,
        "tekshirilgan_vaqt": now.isoformat(),
    }


@shared_task
def tozalash_eski_kutilayotgan_obunalar():
    """
    Bir martalik ishlatish uchun — bazada qolgan barcha eski "kutilmoqda" 
    obunalarni o'chirish (30 daqiqadan ko'p vaqt o'tgan).
    
    Bu task'ni terminal orqali qo'lda ishga tushiring:
    python manage.py shell
    >>> from apps.obuna.tasks import tozalash_eski_kutilayotgan_obunalar
    >>> tozalash_eski_kutilayotgan_obunalar.delay()
    """
    now = timezone.now()
    timeout_vaqt = now - timedelta(minutes=30)
    
    # Barcha eski kutilayotgan obunalarni topish
    eski_obunalar = Obuna.objects.filter(
        holat=Obuna.Holat.KUTILMOQDA,
        created_at__lt=timeout_vaqt,
    )
    
    jami_soni = eski_obunalar.count()
    
    if jami_soni == 0:
        logger.info("[Tozalash] Tozalanadigan obuna yo'q")
        return {"tozalangan_soni": 0, "vaqt": now.isoformat()}
    
    logger.info("[Tozalash] %s ta eski kutilayotgan obuna topildi, o'chirilmoqda...", jami_soni)
    
    # Barcha tolovlarni bekor qilish
    with transaction.atomic():
        Tolov.objects.filter(
            obuna__in=eski_obunalar,
            holat=Tolov.Holat.KUTILMOQDA,
        ).update(holat=Tolov.Holat.BEKOR)
        
        # Obunalarni bekor qilish
        tozalangan = eski_obunalar.update(holat=Obuna.Holat.BEKOR)
    
    logger.info("[Tozalash] %s ta obuna va ularga tegishli to'lovlar bekor qilindi", tozalangan)
    
    return {
        "tozalangan_soni": tozalangan,
        "vaqt": now.isoformat(),
    }


@shared_task
def obuna_tugash_xabarnomasi():
    """
    Muddati tugagan obunalar uchun Telegram xabarnoma yuborish.
    
    Ikkita holatni tekshiradi:
    1. To'liq obunalar (Tarif bo'yicha) - tugash_vaqti o'tgan
    2. Bepul sinov muddati - bepul_muddat_tugash o'tgan
    
    Celery Beat tomonidan kuniga 1 marta (har kuni 10:00 da) ishga tushiriladi.
    
    Qaysi obuna/rieltorga xabar yuborilgani `xabarnoma_yuborildi` flagidan
    kuzatiladi (bu task keyinchalik qo'shiladi - avval logika ishlaydi).
    """
    now = timezone.now()
    
    # ===== 1. To'liq obunalar tugash xabarnomasi =====
    # FAOL holatdagi, lekin tugash_vaqti o'tgan obunalarni topish
    tugagan_obunalar = Obuna.objects.filter(
        holat=Obuna.Holat.FAOL,
        tugash_vaqti__lte=now,
    ).select_related('rieltor__user', 'tarif')
    
    obuna_xabar_soni = 0
    
    for obuna in tugagan_obunalar:
        try:
            # Obuna holatini TUGAGAN ga o'zgartirish
            with transaction.atomic():
                obuna.holat = Obuna.Holat.TUGAGAN
                obuna.save(update_fields=['holat', 'updated_at'])
            
            # Telegram xabarnoma yuborish
            try:
                from .notifications import obuna_tugadi_xabar
                if obuna_tugadi_xabar(obuna):
                    obuna_xabar_soni += 1
                    logger.info(
                        "[Obuna Tugash] Xabar yuborildi: obuna_id=%s rieltor=%s tarif=%s",
                        obuna.id,
                        obuna.rieltor.user.telegram_id,
                        obuna.tarif.nomi,
                    )
            except Exception as notif_exc:
                # Xabarnoma xatosi biznes logikani to'xtatmasligi kerak
                logger.warning(
                    "[Obuna Tugash] Xabar yuborishda xato: obuna_id=%s err=%s",
                    obuna.id, notif_exc
                )
            
        except Exception as exc:
            logger.error(
                "[Obuna Tugash] Obunani yangilashda xato: obuna_id=%s err=%s",
                obuna.id, exc, exc_info=True
            )
    
    # ===== 2. Bepul sinov muddati tugash — PROMO (aksiya) xabarnomasi =====
    # Kimga yuboriladi:
    #   1. Bepul sinov muddati tugagan (bepul_muddat_tugash < now)
    #   2. HECH QACHON pul to'lamagan — muvaffaqiyatli to'lovi (Tolov) yo'q
    #   3. Ayni paytda faol obunasi yo'q (qo'shimcha xavfsizlik sharti)
    #   4. Bu rieltorga promo xabari HALI YUBORILMAGAN
    #      (promo_xabar_yuborildi=False) — bir marta borgan odamga qayta bormaydi.
    bepul_xabar_soni = 0

    # Hech qachon muvaffaqiyatli to'lov qilgan rieltorlar (ularga yubormaymiz)
    tolagan_rieltor_idlari = (
        Tolov.objects
        .filter(holat=Tolov.Holat.MUVAFFAQIYATLI)
        .values_list('obuna__rieltor_id', flat=True)
        .distinct()
    )

    tugagan_bepul = (
        MaklerProfil.objects
        .filter(
            bepul_muddat_tugash__lte=now,
            bepul_muddat_tugash__isnull=False,
            promo_xabar_yuborildi=False,       # oldin xabar bormaganlar
        )
        .exclude(id__in=tolagan_rieltor_idlari)  # pul to'laganlarni chiqarib tashlash
        .select_related('user')
    )

    for rieltor in tugagan_bepul:
        try:
            # Qo'shimcha xavfsizlik: faol obunasi bo'lsa yubormaymiz
            if rieltor.obuna_faol:
                continue

            try:
                from .notifications import bepul_muddat_tugadi_xabar
                if bepul_muddat_tugadi_xabar(rieltor):
                    # Faqat xabar HAQIQATDA yuborilganda flagni belgilaymiz —
                    # shunda qayta yuborilmaydi. Yuborilmasa keyingi kuni
                    # yana urinib ko'riladi.
                    rieltor.promo_xabar_yuborildi = True
                    rieltor.promo_xabar_vaqti = timezone.now()
                    rieltor.save(update_fields=[
                        'promo_xabar_yuborildi', 'promo_xabar_vaqti', 'updated_at'
                    ])
                    bepul_xabar_soni += 1
                    logger.info(
                        "[Bepul Muddat Tugash] Promo xabar yuborildi: rieltor_id=%s telegram_id=%s",
                        rieltor.id,
                        rieltor.user.telegram_id,
                    )
            except Exception as notif_exc:
                logger.warning(
                    "[Bepul Muddat Tugash] Xabar yuborishda xato: rieltor_id=%s err=%s",
                    rieltor.id, notif_exc
                )

        except Exception as exc:
            logger.error(
                "[Bepul Muddat Tugash] Rieltorni tekshirishda xato: rieltor_id=%s err=%s",
                rieltor.id, exc, exc_info=True
            )
    
    logger.info(
        "[Obuna Tugash Task] Umumiy: obuna xabarlari=%s, bepul muddat xabarlari=%s",
        obuna_xabar_soni,
        bepul_xabar_soni,
    )
    
    return {
        "obuna_xabarnomalar": obuna_xabar_soni,
        "bepul_muddat_xabarnomalar": bepul_xabar_soni,
        "tekshirilgan_vaqt": now.isoformat(),
    }


@shared_task
def obuna_tugashidan_oldin_eslatma(kunlar: int = 3):
    """
    Obuna tugashidan {kunlar} kun oldin eslatma xabarnomasi.
    
    Args:
        kunlar: Necha kun oldin xabar yuborish (default: 3)
    
    Celery Beat tomonidan kuniga 1 marta (har kuni 09:00 da) ishga tushiriladi.
    
    Masalan: Agar obuna 3 kundan keyin tugasa, bugun eslatma xabari yuboriladi.
    """
    now = timezone.now()
    eslatma_vaqt = now + timedelta(days=kunlar)
    eslatma_vaqt_end = eslatma_vaqt + timedelta(days=1)
    
    # Kelgusi {kunlar} kun ichida tugaydigan FAOL obunalarni topish
    # (Masalan: 3 kun - bugun 10:00, tugash_vaqti 3 kundan 4 kungacha oraliq)
    tugash_yaqinlashgan = Obuna.objects.filter(
        holat=Obuna.Holat.FAOL,
        tugash_vaqti__gte=eslatma_vaqt,
        tugash_vaqti__lt=eslatma_vaqt_end,
    ).select_related('rieltor__user', 'tarif')
    
    xabar_yuborilgan = 0
    
    for obuna in tugash_yaqinlashgan:
        try:
            from .notifications import obuna_tugashi_haqida_xabar
            if obuna_tugashi_haqida_xabar(obuna, qolgan_kun=kunlar):
                xabar_yuborilgan += 1
                logger.info(
                    "[Obuna Eslatma] Xabar yuborildi: obuna_id=%s rieltor=%s qolgan_kun=%s",
                    obuna.id,
                    obuna.rieltor.user.telegram_id,
                    kunlar,
                )
        except Exception as exc:
            logger.warning(
                "[Obuna Eslatma] Xabar yuborishda xato: obuna_id=%s err=%s",
                obuna.id, exc
            )
    
    logger.info(
        "[Obuna Eslatma Task] %s kun oldin eslatma: %s ta xabar yuborildi",
        kunlar,
        xabar_yuborilgan,
    )
    
    return {
        "xabar_yuborilgan": xabar_yuborilgan,
        "kunlar": kunlar,
        "tekshirilgan_vaqt": now.isoformat(),
    }
