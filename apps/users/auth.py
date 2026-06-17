import hashlib
import hmac
import time
import json
import logging
from urllib.parse import parse_qsl
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_telegram_auth(data: dict) -> bool:
    """
    Telegram WebApp initData yoki Login Widget ma'lumotlarini tekshiradi.

    Args:
        data: Telegram'dan kelgan parse qilingan ma'lumotlar

    Returns:
        bool: Agar hash to'g'ri bo'lsa True, aks holda False
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN sozlanmagan")
        return False

    # auth_date ni tekshirish
    auth_date = data.get('auth_date')
    if not auth_date:
        logger.warning("auth_date topilmadi")
        return False

    try:
        auth_date = int(auth_date)
    except (ValueError, TypeError):
        logger.warning(f"auth_date noto'g'ri formatda: {auth_date}")
        return False

    # 24 soatdan eski bo'lsa — rad etish
    if time.time() - auth_date > 86400:
        logger.warning(f"Auth date eskirgan: {auth_date}")
        return False

    # Hash ni tekshirish
    received_hash = data.get('hash')
    if not received_hash:
        logger.warning("Hash topilmadi")
        return False

    # Secret key yaratish
    secret_key = hmac.new(
        b'WebAppData',
        token.encode(),
        hashlib.sha256
    ).digest()

    def _hash_for(keys_to_exclude):
        """Berilgan key'lar chiqarib tashlangan holda hash hisoblaydi"""
        check = {k: v for k, v in data.items() if k not in keys_to_exclude}
        # Sorted qilish va '=' bilan birlashtirish
        dcs = '\n'.join(f"{k}={v}" for k, v in sorted(check.items()))
        return hmac.new(secret_key, dcs.encode(), hashlib.sha256).hexdigest()

    # Telegram'ning turli klientlari uchun ikkita variant
    # 1) Standart: hash va signature chiqarib tashlanadi
    # 2) Ba'zi klientlar: faqat hash chiqarib tashlanadi
    if _hash_for(('hash', 'signature')) == received_hash:
        logger.debug("Hash tekshiruvi muvaffaqiyatli (standart variant)")
        return True

    if _hash_for(('hash',)) == received_hash:
        logger.debug("Hash tekshiruvi muvaffaqiyatli (faqat hash chiqarildi)")
        return True

    logger.warning(f"Hash mos kelmadi. Received: {received_hash[:10]}...")
    return False


def parse_webapp_user(init_data: str) -> dict:
    """
    Telegram WebApp initData string ni parse qiladi.

    MUHIM: 'user' maydoni XOM JSON string holida qoldiriladi, chunki
    Telegram hash'ni aynan xom string ustidan hisoblaydi.

    Args:
        init_data: Telegram'dan kelgan initData string

    Returns:
        dict: Parse qilingan ma'lumotlar
    """
    if not init_data:
        logger.warning("init_data bo'sh")
        return {}

    try:
        result = dict(parse_qsl(init_data, strict_parsing=False))
        logger.debug(f"Parse qilindi, keys: {list(result.keys())}")
        return result
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return {}


def parse_webapp_user_dict(init_data: str) -> dict:
    """
    initData ni parse qilib, 'user' maydonini dict ga aylantiradi.

    Bu funksiyani FAQAT verify_telegram_auth() muvaffaqiyatli
    o'tgandan keyin chaqiring!

    Args:
        init_data: Telegram'dan kelgan initData string

    Returns:
        dict: 'user' maydoni dict ko'rinishida bo'lgan ma'lumotlar
    """
    result = parse_webapp_user(init_data)

    if not result:
        return {}

    if 'user' in result and result['user']:
        try:
            result['user'] = json.loads(result['user'])
            logger.debug(f"User dict ga aylantirildi: {result['user'].get('id')}")
        except json.JSONDecodeError as e:
            logger.error(f"User JSON parse error: {e}")
            result['user'] = {}
        except Exception as e:
            logger.error(f"User parse error: {e}")
            result['user'] = {}

    return result


def get_telegram_user_data(init_data: str) -> dict:
    """
    Telegram initData dan foydalanuvchi ma'lumotlarini olish uchun
    qulay funksiya. Avtomatik ravishda hash tekshiruvini ham bajaradi.

    Args:
        init_data: Telegram'dan kelgan initData string

    Returns:
        dict: {
            'verified': bool,
            'user': dict,  # Agar verified=True bo'lsa
            'error': str   # Agar verified=False bo'lsa
        }
    """
    # 1. Parse qilish
    parsed = parse_webapp_user(init_data)
    if not parsed:
        return {
            'verified': False,
            'error': "initData parse qilishda xatolik"
        }

    # 2. Hash tekshiruvi
    if not verify_telegram_auth(parsed):
        return {
            'verified': False,
            'error': "Telegram autentifikatsiya muvaffaqiyatsiz"
        }

    # 3. User ma'lumotlarini olish
    parsed_full = parse_webapp_user_dict(init_data)
    tg_user = parsed_full.get('user', {})

    if not tg_user:
        return {
            'verified': False,
            'error': "Telegram user ma'lumotlari topilmadi"
        }

    return {
        'verified': True,
        'user': tg_user
    }


# Qisqa va qulay nomlar (backward compatibility uchun)
parse_telegram_user = parse_webapp_user
parse_telegram_user_dict = parse_webapp_user_dict
verify_telegram = verify_telegram_auth