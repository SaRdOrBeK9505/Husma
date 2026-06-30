"""
Celery vazifalar — ariza notification tizimi.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from celery.exceptions import Retry

from .models import Ariza, ArizaMakler

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 daqiqa keyin qayta urinish
)
def yangi_ariza_xabari_yubor(self, ariza_makler_id: int) -> dict:
    """
    Rieltorga yangi ariza haqida Telegram xabari yuboradi.
    
    Idempotent: bir xil ariza_makler_id uchun bir necha marta chaqirilsa ham,
    faqat bitta xabar yuboriladi (ArizaMakler holatini tekshiradi).
    
    Retry: xato bo'lsa 3 marta qayta urinadi (har biridan keyin 1 daqiqa).
    
    Args:
        ariza_makler_id: ArizaMakler modeli ID si
        
    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        # ArizaMaklerni olish
        ariza_makler = ArizaMakler.objects.select_related(
            'rieltor__user',
            'ariza__mulk_turi',
            'ariza__hudud'
        ).get(id=ariza_makler_id)
        
        # Idempotency tekshiruvi: agar allaqachon ko'rildi bo'lsa, xabar yubormaslik
        if ariza_makler.holat != ArizaMakler.Holat.YANGI:
            logger.info(
                f"[Ariza Notification] ArizaMakler {ariza_makler_id} allaqachon "
                f"{ariza_makler.holat} holatida, xabar yuborilmadi."
            )
            return {
                "success": False,
                "message": f"Ariza allaqachon {ariza_makler.holat} holatida"
            }
        
        # Rieltorning telegram_id sini tekshirish
        telegram_id = ariza_makler.rieltor.user.telegram_id
        if not telegram_id:
            logger.warning(
                f"[Ariza Notification] Rieltor {ariza_makler.rieltor.id} da telegram_id yo'q"
            )
            return {
                "success": False,
                "message": "Rieltorda telegram_id yo'q"
            }
        
        # Xabar matnini tayyorlash
        xabar_matni = _xabar_matni_tayorla(ariza_makler)
        
        # Telegram API orqali yuborish
        _telegram_yubor(telegram_id, xabar_matni)
        
        # Muvaffaqiyatli yuborilgandan keyin holatni yangilash
        ariza_makler.holat = ArizaMakler.Holat.KORILDI
        ariza_makler.korilgan_vaqt = timezone.now()
        ariza_makler.save(update_fields=['holat', 'korilgan_vaqt'])
        
        logger.info(
            f"[Ariza Notification] Xabar muvaffaqiyatli yuborildi: "
            f"rieltor={ariza_makler.rieltor.user.username}, "
            f"ariza={ariza_makler.ariza.id}"
        )
        
        return {
            "success": True,
            "message": "Xabar muvaffaqiyatli yuborildi"
        }
        
    except ArizaMakler.DoesNotExist:
        logger.error(
            f"[Ariza Notification] ArizaMakler {ariza_makler_id} topilmadi"
        )
        return {
            "success": False,
            "message": "ArizaMakler topilmadi"
        }
        
    except Exception as exc:
        logger.error(
            f"[Ariza Notification] Xato: ariza_makler_id={ariza_makler_id}, err={exc}",
            exc_info=True
        )
        
        # Retry mechanism - 3 marta qayta urinish
        if self.request.retries < self.max_retries:
            logger.info(
                f"[Ariza Notification] Qayta urinish: {self.request.retries + 1}/{self.max_retries}"
            )
            raise self.retry(exc=exc)
        
        # Barcha urinishlar muvaffaqiyatsiz bo'lsa
        return {
            "success": False,
            "message": f"Xato: {str(exc)}"
        }


def _xabar_matni_tayorla(ariza_makler: ArizaMakler) -> str:
    """Xabar matnini tayyorlaydi."""
    ariza = ariza_makler.ariza
    mulk_turi = ariza.mulk_turi.nomi if ariza.mulk_turi else "Noma'lum"
    hudud = ariza.hudud.nomi if ariza.hudud else "Noma'lum"
    narx = f"{ariza.narx_min:,} - {ariza.narx_max:,} so'm"
    telefon_str = ariza.telefon or "Ko'rsatilmagan"
    
    matn = (
        f"🔔 *Yangi ariza kelgan!*\n\n"
        f"🏠 Mulk turi: {mulk_turi}\n"
        f"📍 Hudud: {hudud}\n"
        f"💰 Narx: {narx}\n"
        f"📞 Tel: {telefon_str}\n"
    )
    
    return matn


def _telegram_yubor(chat_id: str, text: str) -> None:
    """Telegram Bot API orqali xabar yuboradi."""
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN sozlanmagan")
    
    import requests
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    if not data.get('ok'):
        raise ValueError(f"Telegram API xatosi: {data}")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def kanalga_yangi_ariza_xabari_yubor(self, ariza_id: int) -> dict:
    """
    Yangi ariza haqida Telegram kanalga xabar yuboradi.
    
    Idempotent: bir xil ariza_id uchun bir necha marta chaqirilsa ham,
    faqat bitta xabar yuboriladi (ariza holatini tekshiradi).
    
    Retry: xato bo'lsa 3 marta qayta urinadi (har biridan keyin 1 daqiqa).
    
    Args:
        ariza_id: Ariza modeli ID si
        
    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        # Arizani olish
        ariza = Ariza.objects.select_related(
            'mulk_turi',
            'hudud'
        ).get(id=ariza_id)
        
        # Idempotency tekshiruvi: faqat yangi holatdagi arizalar uchun
        if ariza.holat != Ariza.Holat.YANGI:
            logger.info(
                f"[Kanal Notification] Ariza {ariza_id} allaqachon "
                f"{ariza.holat} holatida, kanalga xabar yuborilmadi."
            )
            return {
                "success": False,
                "message": f"Ariza allaqachon {ariza.holat} holatida"
            }
        
        # Xabar matnini tayyorlash
        mulk_turi = ariza.mulk_turi.nomi if ariza.mulk_turi else "Noma'lum"
        hudud = ariza.hudud.nomi if ariza.hudud else "Noma'lum"
        narx = f"{ariza.narx_min:,} - {ariza.narx_max:,} so'm"
        telefon_str = ariza.telefon or "Ko'rsatilmagan"
        
        xabar_matni = (
            f"📋 *Yangi ariza tushdi!*\n\n"
            f"🏠 Mulk turi: {mulk_turi}\n"
            f"📍 Hudud: {hudud}\n"
            f"💰 Narx: {narx}\n"
            f"📞 Tel: {telefon_str}\n"
        )
        
        # Kanalga yuborish
        from core.telegram_utils import telegram_kanalga_yubor
        yuborildi = telegram_kanalga_yubor(xabar_matni)
        
        if yuborildi:
            logger.info(
                f"[Kanal Notification] Ariza {ariza_id} haqida kanalga xabar yuborildi"
            )
            return {
                "success": True,
                "message": "Kanalga xabar muvaffaqiyatli yuborildi"
            }
        else:
            logger.warning(
                f"[Kanal Notification] Ariza {ariza_id} haqida kanalga xabar yuborilmadi"
            )
            return {
                "success": False,
                "message": "Kanalga xabar yuborilmadi"
            }
        
    except Ariza.DoesNotExist:
        logger.error(
            f"[Kanal Notification] Ariza {ariza_id} topilmadi"
        )
        return {
            "success": False,
            "message": "Ariza topilmadi"
        }
        
    except Exception as exc:
        logger.error(
            f"[Kanal Notification] Xato: ariza_id={ariza_id}, err={exc}",
            exc_info=True
        )
        
        # Retry mechanism - 3 marta qayta urinish
        if self.request.retries < self.max_retries:
            logger.info(
                f"[Kanal Notification] Qayta urinish: {self.request.retries + 1}/{self.max_retries}"
            )
            raise self.retry(exc=exc)
        
        # Barcha urinishlar muvaffaqiyatsiz bo'lsa
        return {
            "success": False,
            "message": f"Xato: {str(exc)}"
        }
