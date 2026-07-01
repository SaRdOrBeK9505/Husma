"""
Telegram kanalga xabar yuborish uchun umumiy funksiyalar.
"""
import logging
import requests
from typing import Literal
from django.conf import settings

logger = logging.getLogger(__name__)

# Kanal turlari - faqat 2 ta
ChannelType = Literal['rieltor', 'ariza']


def telegram_kanalga_yubor(
    text: str,
    channel_type: ChannelType
) -> bool:
    """
    Telegram kanalga xabar yuboradi.
    
    Args:
        text: Yuboriladigan xabar matni
        channel_type: Kanal turi ('rieltor' yoki 'ariza')
            - 'rieltor': Yangi rieltor ro'yxatdan o'tganda
            - 'ariza': Yangi ariza tushganda
        
    Returns:
        bool: Muvaffaqiyatli yuborilganda True, aks holda False
        
    Note:
        - Agar kanal ID bo'sh bo'lsa, jim o'tadi (xato chiqarmaydi)
        - Xato bo'lsa logging yoziladi, lekin asosiy oqim to'xtatilmaydi
    """
    # Kanal ID ni aniqlash
    channel_id = _get_channel_id(channel_type)
    
    if not channel_id:
        logger.info(
            f"[Telegram Channel] {channel_type.upper()} kanal ID sozlanmagan, "
            f"xabar yuborilmadi"
        )
        return False
    
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not bot_token:
        logger.warning("[Telegram Channel] TELEGRAM_BOT_TOKEN sozlanmagan")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': channel_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if not data.get('ok'):
            logger.error(
                f"[Telegram Channel:{channel_type.upper()}] API xatosi: {data}"
            )
            return False
        
        logger.info(
            f"[Telegram Channel:{channel_type.upper()}] "
            f"Xabar muvaffaqiyatli yuborildi"
        )
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(
            f"[Telegram Channel:{channel_type.upper()}] Request xatosi: {e}"
        )
        return False
    except Exception as e:
        logger.error(
            f"[Telegram Channel:{channel_type.upper()}] Noma'lum xato: {e}"
        )
        return False


def _get_channel_id(channel_type: ChannelType) -> str:
    """
    Kanal turi bo'yicha kanal ID ni qaytaradi.
    
    Args:
        channel_type: Kanal turi ('rieltor' yoki 'ariza')
        
    Returns:
        str: Kanal ID yoki bo'sh string
    """
    channel_mapping = {
        'rieltor': 'TELEGRAM_RIELTOR_CHANNEL_ID',
        'ariza': 'TELEGRAM_ARIZA_CHANNEL_ID',
    }
    
    setting_name = channel_mapping[channel_type]
    return getattr(settings, setting_name, '')
