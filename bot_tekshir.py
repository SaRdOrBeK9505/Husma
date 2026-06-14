"""
Bot tokenini tekshiradi — token haqiqiymi va qaysi botga tegishli.

ISHLATISH:
  .venv\\Scripts\\python.exe bot_tekshir.py

Standart holda .env dagi TELEGRAM_BOT_TOKEN ni tekshiradi.
Boshqa tokenni tekshirish uchun argument bering:
  .venv\\Scripts\\python.exe bot_tekshir.py 1234567890:AAxxxxx
"""
import os
import sys
import json
import django
from urllib import request as urlrequest
from urllib import error as urlerror

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.conf import settings


def getme(token: str):
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        with urlrequest.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urlerror.HTTPError as e:
        return json.loads(e.read().decode())
    except urlerror.URLError as e:
        return {"ok": False, "error": str(e)}


def main():
    token = sys.argv[1] if len(sys.argv) > 1 else settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise SystemExit("Token yo'q (.env da TELEGRAM_BOT_TOKEN yoki argument bering).")

    print(f"Token oxiri: ...{token[-6:]}")
    natija = getme(token)

    if not natija.get("ok"):
        print("\n❌ TOKEN NOTO'G'RI yoki bekor qilingan.")
        print("Telegram javobi:", natija)
        return

    bot = natija["result"]
    print("\n✅ TOKEN HAQIQIY. Quyidagi botga tegishli:")
    print("  Bot nomi   :", bot.get("first_name"))
    print("  Username   : @" + bot.get("username", ""))
    print("  Bot ID     :", bot.get("id"))
    print("  Web App    :", "Ha" if bot.get("has_main_web_app") else "—")
    print("\n>>> Bu @" + bot.get("username", "") + " sizning ishlatayotgan botingizmi?")
    print(">>> Frontend Mini App ham AYNAN shu botda ochilishi kerak.")


if __name__ == "__main__":
    main()
