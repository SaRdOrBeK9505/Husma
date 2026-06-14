import hashlib
import hmac
import time
import logging
from django.conf import settings

logger = logging.getLogger("telegram_auth")


def verify_telegram_auth(data: dict) -> bool:
    """
    Telegram WebApp initData yoki Login Widget ma'lumotlarini tekshiradi.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_AUTH: .env da TELEGRAM_BOT_TOKEN yo'q!")
        return False

    auth_date = int(data.get('auth_date', 0))

    # 24 soatdan eski bo'lsa — rad etish
    yosh = time.time() - auth_date
    if yosh > 86400:
        logger.warning("TELEGRAM_AUTH: auth_date eski (%.0f s). initData eskirgan.", yosh)
        return False

    received_hash = data.get('hash')
    if not received_hash:
        logger.warning("TELEGRAM_AUTH: 'hash' maydoni yo'q. Kalitlar: %s", list(data.keys()))
        return False

    # hash va signature ni olib tashlaymiz.
    # 'signature' — Telegram qo'shgan yangi maydon (uchinchi tomon Ed25519
    # validatsiyasi uchun). U data_check_string ga KIRMASLIGI kerak,
    # aks holda bot-token HMAC hash mos kelmaydi.
    data_check = {
        k: v for k, v in data.items() if k not in ('hash', 'signature')
    }

    # Satrni tartib bilan yasaymiz
    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(data_check.items())
    )

    # HMAC-SHA256
    secret_key = hmac.new(
        b'WebAppData',
        token.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if calculated_hash != received_hash:
        logger.warning(
            "TELEGRAM_AUTH: HASH MOS EMAS.\n"
            "  Token oxiri: ...%s\n"
            "  data_check_string:\n%s\n"
            "  Kelgan hash:      %s\n"
            "  Hisoblangan hash: %s\n"
            "  >>> Sabab odatda: .env token Mini App'ni ochgan botga mos emas.",
            token[-6:], data_check_string, received_hash, calculated_hash,
        )
        return False

    logger.info("TELEGRAM_AUTH: hash mos keldi, verify OK.")
    return True


def parse_webapp_user(init_data: str) -> dict:
    """
    Telegram WebApp initData string ni parse qiladi.

    MUHIM: 'user' maydoni XOM JSON string holida qoldiriladi, chunki
    Telegram hash'ni aynan xom string ustidan hisoblaydi. Agar uni shu yerda
    dict ga aylantirsak, verify_telegram_auth() hash'ni Python dict repr
    ustidan hisoblab, hech qachon mos kelmaydi.
    'user' dict ko'rinishida `parse_webapp_user_dict()` orqali olinadi.
    """
    from urllib.parse import parse_qsl

    # parse_qsl bir marta URL-decode qiladi. unquote + parse_qs ishlatsak,
    # qator IKKI marta decode bo'lib, 'user' ichidagi maxsus belgilar
    # (masalan '+', '%') buzilib, hash mos kelmay qoladi.
    return dict(parse_qsl(init_data, strict_parsing=False))


def parse_webapp_user_dict(init_data: str) -> dict:
    """
    initData ni parse qilib, 'user' maydonini dict ga aylantiradi.
    Faqat verify_telegram_auth() muvaffaqiyatli o'tgandan keyin chaqiriladi.
    """
    import json

    result = parse_webapp_user(init_data)
    if 'user' in result:
        result['user'] = json.loads(result['user'])
    return result