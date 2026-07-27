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
            'ariza__user',
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
        
        # Mijoz bilan Telegram orqali bog'lanish tugmasi
        reply_markup = _bogla_tugma(ariza_makler.ariza.user)
        
        # Telegram API orqali yuborish
        _telegram_yubor(telegram_id, xabar_matni, reply_markup=reply_markup)
        
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


def _telefon_tozala(telefon: str) -> str:
    """
    Telefon raqamni Telegram avtomatik aniqlaydigan (dialer ochiladigan)
    xalqaro formatga keltiradi: faqat '+' va raqamlar.

    Masalan: "+998 (93) 577-15-07" -> "+998935771507"
    """
    if not telefon:
        return ""
    raqamlar = "".join(ch for ch in telefon if ch.isdigit())
    if not raqamlar:
        return ""
    return f"+{raqamlar}"


def _telegram_bogla_url(user) -> str:
    """
    Mijoz bilan Telegram orqali bog'lanish uchun URL qaytaradi.

    - Agar telegram_username bo'lsa -> https://t.me/<username>
    - Aks holda telegram_id orqali -> tg://user?id=<telegram_id>
    - Ikkalasi ham bo'lmasa -> bo'sh string
    """
    if user is None:
        return ""

    username = (getattr(user, 'telegram_username', '') or '').lstrip('@').strip()
    if username:
        return f"https://t.me/{username}"

    telegram_id = getattr(user, 'telegram_id', None)
    if telegram_id:
        return f"tg://user?id={telegram_id}"

    return ""


def _bogla_tugma(user) -> dict | None:
    """
    Mijoz bilan Telegram orqali bog'lanish uchun inline tugma (reply_markup)
    yasaydi. Agar bog'lanish uchun ma'lumot bo'lmasa None qaytaradi.
    """
    url = _telegram_bogla_url(user)
    if not url:
        return None

    return {
        "inline_keyboard": [
            [
                {
                    "text": "✈️ Telegram orqali bog'lanish",
                    "url": url,
                }
            ]
        ]
    }


def _xabar_matni_tayorla(ariza_makler: ArizaMakler) -> str:
    """Xabar matnini tayyorlaydi."""
    ariza = ariza_makler.ariza
    mulk_turi = ariza.mulk_turi.nomi if ariza.mulk_turi else "Noma'lum"
    hudud = ariza.hudud.nomi if ariza.hudud else "Noma'lum"
    valyuta = ariza.get_valyuta_display()
    narx = f"{ariza.narx_min:,} - {ariza.narx_max:,} {valyuta}"
    # Telefonni dialer ochiladigan toza formatda ko'rsatamiz
    telefon_str = _telefon_tozala(ariza.telefon) or "Ko'rsatilmagan"
    
    # Ariza turi (maqsad) - ijaraga olish yoki sotib olish
    ariza_turi = ariza.get_ariza_turi_display()
    
    # Xonalar soni
    xonalar = ariza.get_xonalar_soni_display()
    
    # Ism (agar mavjud bo'lsa)
    ism_qatori = f"👤 Ism: {ariza.ism}\n" if ariza.ism else ""
    # Qo'shimcha izoh (agar mavjud bo'lsa)
    izoh_qatori = f"📝 Izoh: {ariza.qoshimcha_izoh}\n" if ariza.qoshimcha_izoh else ""

    matn = (
        f"🔔 *Mijozdan yangi ariza tushdi!*\n\n"
        f"🎯 Maqsad: {ariza_turi}\n"
        f"🏠 Mulk turi: {mulk_turi}\n"
        f"🛏 Xonalar: {xonalar}\n"
        f"📌 Hudud: {hudud}\n"
        f"💰 Narx: {narx}\n"
        f"{ism_qatori}"
        f"📞 Tel: {telefon_str}\n"
        f"{izoh_qatori}"
    )
    
    return matn


def _telegram_yubor(chat_id: str, text: str, reply_markup: dict | None = None) -> None:
    """Telegram Bot API orqali xabar yuboradi.

    Args:
        chat_id: Qabul qiluvchi chat/telegram ID
        text: Xabar matni (Markdown)
        reply_markup: (ixtiyoriy) inline tugmalar uchun markup
    """
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
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
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
        valyuta = ariza.get_valyuta_display()
        narx = f"{ariza.narx_min:,} - {ariza.narx_max:,} {valyuta}"
        telefon_str = _telefon_tozala(ariza.telefon) or "Ko'rsatilmagan"
        
        # Ariza turi (maqsad) - ijaraga olish yoki sotib olish
        ariza_turi = ariza.get_ariza_turi_display()
        
        # Xonalar soni
        xonalar = ariza.get_xonalar_soni_display()
        
        # Ism (agar mavjud bo'lsa)
        ism_qatori = f"👤 Ism: {ariza.ism}\n" if ariza.ism else ""
        # Qo'shimcha izoh (agar mavjud bo'lsa)
        izoh_qatori = f"📝 Izoh: {ariza.qoshimcha_izoh}\n" if ariza.qoshimcha_izoh else ""

        xabar_matni = (
            f"📋 *Mijozdan yangi ariza tushdi!*\n\n"
            f"🎯 Maqsad: {ariza_turi}\n"
            f"🏠 Mulk turi: {mulk_turi}\n"
            f"🛏 Xonalar: {xonalar}\n"
            f"📌 Hudud: {hudud}\n"
            f"💰 Narx: {narx}\n"
            f"{ism_qatori}"
            f"📞 Tel: {telefon_str}\n"
            f"{izoh_qatori}"
        )
        
        # Kanalga yuborish - ARIZA kanali
        from core.telegram_utils import telegram_kanalga_yubor
        yuborildi = telegram_kanalga_yubor(xabar_matni, channel_type='ariza')
        
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
