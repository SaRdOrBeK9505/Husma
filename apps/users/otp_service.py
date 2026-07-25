import random
import json
import mimetypes
import uuid
import urllib.request
import urllib.error
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def kode_generatsiya():
    """6 xonali tasodifiy kod"""
    return str(random.randint(100000, 999999))


def telegram_xabar_yuborish(telegram_id: int, matn: str, reply_markup: dict = None) -> bool:
    """
    Telegram bot orqali foydalanuvchiga xabar yuboradi.
    True — muvaffaqiyatli, False — xato.
    
    Args:
        telegram_id: Telegram foydalanuvchi IDsi
        matn: Yuborilishi kerak bo'lgan xabar matni
        reply_markup: Inline keyboard yoki boshqa markup (optional)
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": telegram_id,
        "text": matn,
        "parse_mode": "HTML",
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    payload = json.dumps(data).encode("utf-8")

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


def telegram_rasm_yuborish(
    telegram_id: int,
    rasm_yoli: str,
    caption: str = "",
    reply_markup: dict = None,
) -> bool:
    """
    Telegram bot orqali foydalanuvchiga rasm (photo) + caption yuboradi.

    Lokal fayl `sendPhoto` ga multipart/form-data ko'rinishida yuboriladi
    (tashqi kutubxona kerak emas, faqat urllib).

    Args:
        telegram_id: Telegram foydalanuvchi IDsi
        rasm_yoli: Yuboriladigan rasmning lokal to'liq yo'li
        caption: Rasm ostidagi matn (HTML). Telegram limiti — 1024 belgi.
        reply_markup: Inline keyboard yoki boshqa markup (optional)

    Returns:
        bool: True — muvaffaqiyatli, False — xato (fayl yo'q yoki API xatosi).
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False

    rasm = Path(rasm_yoli)
    if not rasm.is_file():
        return False

    try:
        fayl_baytlar = rasm.read_bytes()
    except OSError:
        return False

    # --- multipart/form-data qo'lda yig'iladi ---
    boundary = f"----HusmaBoundary{uuid.uuid4().hex}"
    crlf = "\r\n"

    def _matn_qism(nom: str, qiymat: str) -> bytes:
        return (
            f"--{boundary}{crlf}"
            f'Content-Disposition: form-data; name="{nom}"{crlf}{crlf}'
            f"{qiymat}{crlf}"
        ).encode("utf-8")

    content_type = mimetypes.guess_type(rasm.name)[0] or "image/jpeg"

    qismlar = [_matn_qism("chat_id", str(telegram_id))]
    if caption:
        # Telegram caption limiti 1024 belgi
        qismlar.append(_matn_qism("caption", caption[:1024]))
        qismlar.append(_matn_qism("parse_mode", "HTML"))
    if reply_markup:
        qismlar.append(_matn_qism("reply_markup", json.dumps(reply_markup)))

    # Rasm fayli qismi
    fayl_sarlavha = (
        f"--{boundary}{crlf}"
        f'Content-Disposition: form-data; name="photo"; filename="{rasm.name}"{crlf}'
        f"Content-Type: {content_type}{crlf}{crlf}"
    ).encode("utf-8")

    body = (
        b"".join(qismlar)
        + fayl_sarlavha
        + fayl_baytlar
        + crlf.encode("utf-8")
        + f"--{boundary}--{crlf}".encode("utf-8")
    )

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
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
