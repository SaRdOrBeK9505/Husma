import hashlib
import hmac
import time
from django.conf import settings


def verify_telegram_auth(data: dict) -> bool:
    """
    Telegram WebApp initData yoki Login Widget ma'lumotlarini tekshiradi.
    """
    auth_date = int(data.get('auth_date', 0))

    # 24 soatdan eski bo'lsa — rad etish
    if time.time() - auth_date > 86400:
        return False

    received_hash = data.get('hash')
    if not received_hash:
        return False

    # hash ni olib tashlaymiz
    data_check = {k: v for k, v in data.items() if k != 'hash'}

    # Satrni tartib bilan yasaymiz
    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(data_check.items())
    )

    # HMAC-SHA256
    secret_key = hmac.new(
        b'WebAppData',
        settings.TELEGRAM_BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return calculated_hash == received_hash


def parse_webapp_user(init_data: str) -> dict:
    """
    Telegram WebApp initData string ni parse qiladi.
    """
    from urllib.parse import parse_qs, unquote
    import json

    parsed = parse_qs(unquote(init_data))
    result = {k: v[0] for k, v in parsed.items()}

    if 'user' in result:
        result['user'] = json.loads(result['user'])

    return result