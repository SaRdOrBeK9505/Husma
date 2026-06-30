"""
Telegram kanalga xabar yuborish uchun umumiy funksiyalar.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def telegram_kanalga_yubor(text: str) -> bool:
    """
    Telegram kanalga xabar yuboradi.
    
    Args:
        text: Yuboriladigan xabar matni
        
    Returns:
        bool: Muvaffaqiyatli yuborilganda True, aks holda False
        
    Note:
        - Agar TELEGRAM_NOTIFY_CHANNEL_ID bo'sh bo'lsa, jim o'tadi (xato chiqarmaydi)
        - Xato bo'lsa logging yoziladi, lekin asosiy oqim to'xtatilmaydi
    """
    chat_id = getattr(settings, 'TELEGRAM_NOTIFY_CHANNEL_ID', '')
    if not chat_id:
        logger.info("[Telegram Channel] TELEGRAM_NOTIFY_CHANNEL_ID sozlanmagan, xabar yuborilmadi")
        return False
    
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not bot_token:
        logger.warning("[Telegram Channel] TELEGRAM_BOT_TOKEN sozlanmagan")
        return False
    
    try:
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
            logger.error(f"[Telegram Channel] API xatosi: {data}")
            return False
        
        logger.info("[Telegram Channel] Xabar muvaffaqiyatli yuborildi")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[Telegram Channel] Request xatosi: {e}")
        return False
    except Exception as e:
        logger.error(f"[Telegram Channel] Noma'lum xato: {e}")
        return False
