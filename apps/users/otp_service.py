import random
import json
import urllib.request
import urllib.error
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def kode_generatsiya():
    """6 xonali tasodifiy kod"""
    return str(random.randint(100000, 999999))


def telegram_xabar_yuborish(telegram_id: int, matn: str) -> bool:
    """
    Telegram bot orqali foydalanuvchiga xabar yuboradi.
    True — muvaffaqiyatli, False — xato.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": telegram_id,
        "text": matn,
        "parse_mode": "HTML",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.URLError:
        return False


def otp_yuborish(otp_obj) -> bool:
    """
    OTPKode obyektiga qarab Telegram ga xabar yuboradi.
    """
    matn = (
        f"🔐 <b>Husma — Tasdiqlash kodi</b>\n\n"
        f"Sizning ro'yxatdan o'tish kodingiz:\n\n"
        f"<b>{otp_obj.kode}</b>\n\n"
        f"⏱ Kod 5 daqiqa amal qiladi.\n"
        f"Bu kodni hech kimga bermang."
    )
    return telegram_xabar_yuborish(otp_obj.telegram_id, matn)
