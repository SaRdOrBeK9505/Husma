"""
Celery vazifalar — rieltor notification tizimi.
"""
import logging
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from celery.exceptions import Retry

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 daqiqa keyin qayta urinish
)
def kanalga_yangi_rieltor_xabari_yubor(self, rieltor_id: int) -> dict:
    """
    Yangi rieltor ro'yxatdan o'tganda Telegram kanalga xabar yuboradi.
    
    Idempotent: bir xil rieltor_id uchun bir necha marta chaqirilsa ham,
    faqat bitta xabar yuboriladi (rieltor yaratilgan vaqtni tekshiradi).
    
    Retry: xato bo'lsa 3 marta qayta urinadi (har biridan keyin 1 daqiqa).
    
    Args:
        rieltor_id: MaklerProfil modeli ID si
        
    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        from apps.makler.models import MaklerProfil
        from datetime import timedelta
        
        # Rieltorni olish
        rieltor = MaklerProfil.objects.select_related(
            'user'
        ).prefetch_related('hududlar').get(id=rieltor_id)
        
        # Idempotency tekshiruvi: faqat yangi (10 daqiqadan kam) rieltorlar uchun
        yangi_muddat = timezone.now() - timedelta(minutes=10)
        if rieltor.created_at < yangi_muddat:
            logger.info(
                f"[Kanal Rieltor Notification] Rieltor {rieltor_id} eski rieltor "
                f"(created_at={rieltor.created_at}), kanalga xabar yuborilmadi."
            )
            return {
                "success": False,
                "message": "Rieltor eski, xabar yuborilmadi"
            }
        
        # Xabar matnini tayyorlash
        full_name = rieltor.user.full_name or "Noma'lum"
        telefon = rieltor.user.phone or "Ko'rsatilmagan"
        
        # Hududlarni olish
        hududlar = rieltor.hududlar.all()
        hudud_str = ", ".join([h.nomi for h in hududlar[:3]]) if hududlar else "Ko'rsatilmagan"
        if hududlar.count() > 3:
            hudud_str += f" va yana {hududlar.count() - 3} ta"
        
        # Sana formatlash
        sana = rieltor.created_at.strftime("%d.%m.%Y %H:%M")
        
        xabar_matni = (
            f"🆕 *Yangi rieltor ro'yxatdan o'tdi!*\n\n"
            f"👤 Ism: {full_name}\n"
            f"📞 Tel: {telefon}\n"
            f"📍 Hudud: {hudud_str}\n"
            f"🗓 Sana: {sana}"
        )
        
        # Kanalga yuborish - RIELTOR kanali
        from core.telegram_utils import telegram_kanalga_yubor
        yuborildi = telegram_kanalga_yubor(xabar_matni, channel_type='rieltor')
        
        if yuborildi:
            logger.info(
                f"[Kanal Rieltor Notification] Rieltor {rieltor_id} haqida kanalga xabar yuborildi"
            )
            return {
                "success": True,
                "message": "Kanalga xabar muvaffaqiyatli yuborildi"
            }
        else:
            logger.warning(
                f"[Kanal Rieltor Notification] Rieltor {rieltor_id} haqida kanalga xabar yuborilmadi"
            )
            return {
                "success": False,
                "message": "Kanalga xabar yuborilmadi"
            }
        
    except MaklerProfil.DoesNotExist:
        logger.error(
            f"[Kanal Rieltor Notification] Rieltor {rieltor_id} topilmadi"
        )
        return {
            "success": False,
            "message": "Rieltor topilmadi"
        }
        
    except Exception as exc:
        logger.error(
            f"[Kanal Rieltor Notification] Xato: rieltor_id={rieltor_id}, err={exc}",
            exc_info=True
        )
        
        # Retry mechanism - 3 marta qayta urinish
        if self.request.retries < self.max_retries:
            logger.info(
                f"[Kanal Rieltor Notification] Qayta urinish: {self.request.retries + 1}/{self.max_retries}"
            )
            raise self.retry(exc=exc)
        
        # Barcha urinishlar muvaffaqiyatsiz bo'lsa
        return {
            "success": False,
            "message": f"Xato: {str(exc)}"
        }
