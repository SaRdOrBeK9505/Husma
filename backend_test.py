"""
=================================================================
 HUSMA — Backend auth oqimini FRONTEND'siz to'liq test qilish.
=================================================================

Bu skript .env dagi TELEGRAM_BOT_TOKEN bilan HAQIQIY imzolangan
initData yasaydi va backend endpointlarini ketma-ket sinaydi:

  1. Telegram login            -> /api/auth/telegram/
  2. Rieltor OTP so'rov         -> /api/auth/rieltor/otp-sorov/
  3. Rieltor OTP verify         -> /api/auth/rieltor/otp-verify/
  4. Rieltor login (username)   -> /api/auth/rieltor/login/

MUHIM:
  - Token .env dagi token bilan IMZOLANADI, shuning uchun hash mos keladi.
    (Telegram aynan shu ishni qiladi — demak bu haqiqiy test.)
  - 2-3 qadam OTP ni Telegram orqali yuboradi. Token haqiqiy bot bo'lsa
    va siz o'sha botga /start bosgan bo'lsangiz — kod Telegramingizga keladi.
    Test rejimida OTP ni to'g'ridan-to'g'ri bazadan o'qiymiz (--otp-bazadan).

ISHLATISH:
  1. Avval serverni ishga tushiring (alohida terminalda):
       .venv\\Scripts\\python.exe manage.py runserver
  2. Keyin shu skriptni ishga tushiring:
       .venv\\Scripts\\python.exe backend_test.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode
from urllib import request as urlrequest
from urllib import error as urlerror
from django.conf import settings

BASE = "http://127.0.0.1:8000"

# --- Test foydalanuvchisi (xohlagancha o'zgartiring) ---
TG_USER = {
    "id": 7634681769,
    "first_name": "Test",
    "last_name": "Foydalanuvchi",
    "username": "test_user",
}


def make_init_data():
    """.env token bilan haqiqiy imzolangan initData yasaydi."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise SystemExit("XATO: .env da TELEGRAM_BOT_TOKEN yo'q!")
    fields = {
        "user": json.dumps(TG_USER, separators=(",", ":")),
        "auth_date": str(int(time.time())),
        "query_id": "AATEST_QUERY_ID",
    }
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def post(path, body, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urlrequest.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urlerror.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except urlerror.URLError as e:
        raise SystemExit(
            f"XATO: serverga ulanib bo'lmadi ({e}). "
            "Avval 'manage.py runserver' ni ishga tushiring."
        )


def chiziq(matn):
    print("\n" + "=" * 60)
    print(matn)
    print("=" * 60)


def main():
    # ---------- 0. ESKI TEST USER'NI TOZALASH ----------
    # Skript qayta-qayta sof oqimni sinashi uchun avvalgi test ma'lumotlarini o'chiramiz.
    from apps.users.models import CustomUser, OTPKode
    OTPKode.objects.filter(telegram_id=TG_USER["id"]).delete()
    CustomUser.objects.filter(telegram_id=TG_USER["id"]).delete()
    CustomUser.objects.filter(username="test_rieltor").delete()
    print("Eski test ma'lumotlari tozalandi.")

    # ---------- 1. TELEGRAM LOGIN ----------
    chiziq("1) TELEGRAM LOGIN  /api/auth/telegram/")
    init_data = make_init_data()
    code, data = post("/api/auth/telegram/", {"init_data": init_data})
    print("Status:", code)
    if code != 200:
        print("Javob:", data)
        raise SystemExit("Telegram login muvaffaqiyatsiz. Token to'g'riligini tekshiring.")
    access = data["access"]
    print("OK — user:", data["user"]["full_name"], "| role:", data["user"]["role"],
          "| yangi:", data["is_new"])

    # ---------- Hudud / mulk turi tayyorlash ----------
    from apps.hudud.models import Hudud, MulkTuri
    hudud = Hudud.objects.filter(is_active=True).first()
    mulk = MulkTuri.objects.filter(is_active=True).first()
    if not hudud or not mulk:
        print("\nDIQQAT: Bazada hudud yoki mulk turi yo'q.")
        print("Avvalo seed qiling: manage.py seed_hudud")
        raise SystemExit(0)

    # ---------- 2. RIELTOR OTP SO'ROV ----------
    chiziq("2) RIELTOR OTP SO'ROV  /api/auth/rieltor/otp-sorov/")
    body = {
        "full_name": "Test Rieltor",
        "phone": "+998901234567",
        "username": "test_rieltor",
        "password": "parol123",
        "hududlar": [hudud.id],
        "mulk_turlari": [mulk.id],
    }
    code, data = post("/api/auth/rieltor/otp-sorov/", body, token=access)
    print("Status:", code, "| Javob:", data)

    from apps.users.models import OTPKode

    if code == 200:
        # OTP haqiqatan Telegram'ga yuborildi (token haqiqiy bot).
        otp = OTPKode.objects.filter(telegram_id=TG_USER["id"]).order_by("-id").first()
        print("OTP yuborildi. Bazadagi kod:", otp.kode if otp else "—")
    elif code == 503:
        # Token soxta/test bo'lgani uchun Telegram'ga yuborilmadi va OTP o'chirildi.
        # Verify + login mantiqini test qilish uchun OTP ni QO'LDA bazaga yozamiz.
        print("\nDIQQAT: OTP Telegram'ga yuborilmadi (token haqiqiy bot emas).")
        print("Verify+login mantiqini test qilish uchun OTP ni bazaga qo'lda yozamiz.")
        otp = OTPKode.objects.create(
            telegram_id=TG_USER["id"],
            kode="123456",
            register_data={
                "full_name": body["full_name"],
                "phone": body["phone"],
                "username": body["username"],
                "password": body["password"],
                "hududlar": [hudud.id],
                "mulk_turlari": [mulk.id],
            },
        )
        print("Qo'lda yozilgan OTP kod:", otp.kode)
    else:
        raise SystemExit("OTP so'rov kutilmagan status qaytardi.")

    # ---------- 3. RIELTOR OTP VERIFY ----------
    chiziq("3) RIELTOR OTP VERIFY  /api/auth/rieltor/otp-verify/")
    code, data = post("/api/auth/rieltor/otp-verify/", {"kode": otp.kode}, token=access)
    print("Status:", code)
    if code != 201:
        print("Javob:", data)
        raise SystemExit("OTP verify muvaffaqiyatsiz.")
    print("OK — rieltor:", data["rieltor"]["username"],
          "| role:", data["rieltor"]["role"],
          "| faol:", data["rieltor"]["faol"])

    # ---------- 4. RIELTOR LOGIN ----------
    chiziq("4) RIELTOR LOGIN  /api/auth/rieltor/login/")
    code, data = post(
        "/api/auth/rieltor/login/",
        {"username": "test_rieltor", "password": "parol123"},
    )
    print("Status:", code)
    if code != 200:
        print("Javob:", data)
        raise SystemExit("Rieltor login muvaffaqiyatsiz.")
    print("OK — rieltor login muvaffaqiyatli:", data["rieltor"]["username"])

    chiziq("HAMMASI ISHLADI — backend auth oqimi to'liq to'g'ri ✅")


if __name__ == "__main__":
    main()
