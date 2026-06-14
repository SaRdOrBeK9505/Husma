"""
Bot token orqali HAQIQIY imzolangan initData yasaydi.

Telegram initData'ni bot tokeni bilan HMAC-SHA256 imzolaydi.
Token sizda bo'lsa — aynan o'sha imzoni siz ham yasashingiz mumkin.
Natija backend tomonidan haqiqiy Telegram initData kabi qabul qilinadi.

ISHLATISH:
  .venv\\Scripts\\python.exe initdata_yasash.py

Foydalanuvchi ma'lumotlarini quyida USER da o'zgartiring.
Chiqgan {"init_data": "..."} ni Swagger / Postman ga qo'yib
/api/auth/telegram/ ni sinashingiz mumkin.
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
from django.conf import settings

# --- Foydalanuvchi (xohlagancha o'zgartiring) ---
USER = {
    "id": 123456789,
    "first_name": "Ali",
    "last_name": "Valiyev",
    "username": "ali_uz",
    "language_code": "uz",
}


def yasash(token: str) -> str:
    fields = {
        "user": json.dumps(USER, separators=(",", ":")),
        "auth_date": str(int(time.time())),
        "query_id": "AATEST123",
    }
    # data_check_string — hash va signature'siz, alfavit tartibida
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def main():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise SystemExit("XATO: .env da TELEGRAM_BOT_TOKEN yo'q.")

    init_data = yasash(token)
    print(f"Token oxiri: ...{token[-6:]}")
    print("\n--- Swagger/Postman body (JSON) ---\n")
    print(json.dumps({"init_data": init_data}, ensure_ascii=False))
    print("\n--- Faqat initData string ---\n")
    print(init_data)


if __name__ == "__main__":
    main()
