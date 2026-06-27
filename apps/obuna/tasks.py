"""
Celery vazifalar — obuna avtomatik boshqaruvi.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from celery import shared_task

from .models import Obuna, Tolov

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
