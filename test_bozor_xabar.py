"""
Bozor xabari test skripti — rasm va tugmani o'zingizga yuborib ko'rasiz.

ISHLATISH:
    python test_bozor_xabar.py <sizning_telegram_id> rieltor
    python test_bozor_xabar.py <sizning_telegram_id> user

MISOLLAR:
    python test_bozor_xabar.py 123456789 rieltor
    python test_bozor_xabar.py 123456789 user
"""
import sys
import os
import json
import mimetypes
import uuid
import urllib.request
import urllib.error
from pathlib import Path

# --- .env fayldan tokenni o'qish ---
BASE_DIR = Path(__file__).resolve().parent

def env_oqish(kalit: str) -> str:
    env_fayl = BASE_DIR / '.env'
    if env_fayl.is_file():
        for qator in env_fayl.read_text(encoding='utf-8').splitlines():
            qator = qator.strip()
            if qator.startswith('#') or '=' not in qator:
                continue
            k, _, v = qator.partition('=')
            if k.strip() == kalit:
                return v.strip().strip('"').strip("'")
    return os.environ.get(kalit, '')


BOT_TOKEN = env_oqish('TELEGRAM_BOT_TOKEN')
MINI_APP_URL = (
    env_oqish('MINI_APP_WEB_URL')
    or env_oqish('WEB_APP_URL')
    or env_oqish('TELEGRAM_MINI_APP_URL')
).rstrip('/')

RIELTOR_RASM = BASE_DIR / 'assets' / 'promo' / 'bozor_rieltor_promo.jpg'
USER_RASM = BASE_DIR / 'assets' / 'promo' / 'bozor_user_promo.jpg'

RIELTOR_MATN = (
    "🏠 <b>HUSMA ESTATE'DA UY BOZORI ISHGA TUSHDI!</b> 🎉\n\n"
    "Hurmatli rieltor!\n\n"
    "Siz kutgan yangi imkoniyat endi <b>Husma Estate</b> platformasida mavjud.\n\n"
    "✅ Endi sotuv va ijara e'lonlaringizni platformaga joylashingiz mumkin.\n"
    "✅ E'lonlaringiz minglab foydalanuvchilarga ko'rsatiladi.\n"
    "✅ Barcha e'lonlarni bitta joydan boshqarishingiz mumkin.\n\n"
    "🔒 <b>Muhim:</b> Uy bozoriga e'lon joylash huquqi <b>faqat Husma "
    "Estate'dan ro'yxatdan o'tgan rieltorlar</b> uchun mavjud.\n\n"
    "📈 Ko'proq e'lon → Ko'proq mijoz → Ko'proq bitim!\n\n"
    "🚀 <b>Hoziroq \"Bozor\" bo'limiga kiring va birinchi e'loningizni joylang!</b>\n\n"
    "<b>Husma Estate</b> — Professional rieltorlar uchun zamonaviy platforma. ❤️"
)

USER_MATN = (
    "🏠 <b>HUSMA ESTATE'DA UY BOZORI ISHGA TUSHDI!</b> 🎉\n\n"
    "Endi orzuingizdagi uyni topish yanada oson!\n\n"
    "Husma Estate'ning yangi <b>Uy bozori</b> bo'limida siz:\n\n"
    "🏡 Sotuvdagi uy va kvartiralarni topishingiz mumkin.\n"
    "🔑 Ijaraga berilayotgan uylarni ko'rishingiz mumkin.\n"
    "🏢 Tijorat obyektlari va yer maydonlarini qidirishingiz mumkin.\n"
    "🔍 Viloyat, tuman, narx, xona soni va boshqa filtrlar orqali "
    "o'zingizga mos variantni tez topishingiz mumkin.\n\n"
    "✅ Barcha e'lonlar ro'yxatdan o'tgan rieltorlar tomonidan joylashtiriladi. "
    "Bu esa sizga yanada ishonchli va sifatli takliflarni taqdim etadi.\n\n"
    "📱 <b>Hoziroq Husma Estate'ning \"Bozor\" bo'limiga kiring va yuzlab "
    "e'lonlarni ko'rishni boshlang!</b>\n\n"
    "<b>Husma Estate</b> — orzuingizdagi uyni topishning eng qulay yo'li. ❤️"
)


def ilova_tugmasi(url: str) -> dict:
    if 'startapp=' in url:
        final_url = url
    else:
        sep = '&' if '?' in url else '?'
        final_url = f"{url}{sep}startapp=bozor"

    return {
        "inline_keyboard": [
            [{"text": "Ilovani ochish", "web_app": {"url": final_url}}]
        ]
    }


def xabar_yuborish(tg_id: int, matn: str, tugma: dict = None) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": tg_id,
        "text": matn,
        "parse_mode": "HTML",
    }
    if tugma:
        data["reply_markup"] = tugma

    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get('ok', False)
    except Exception as e:
        print(f"  sendMessage xatosi: {e}")
        return False


def rasm_yuborish(tg_id: int, rasm_yoli: Path, caption: str, tugma: dict = None) -> bool:
    if not rasm_yoli.is_file():
        return False

    token = BOT_TOKEN
    fayl_baytlar = rasm_yoli.read_bytes()
    boundary = f"----HusmaBoundary{uuid.uuid4().hex}"
    crlf = "\r\n"

    def _qism(nom: str, qiymat: str) -> bytes:
        return (
            f"--{boundary}{crlf}"
            f'Content-Disposition: form-data; name="{nom}"{crlf}{crlf}'
            f"{qiymat}{crlf}"
        ).encode("utf-8")

    content_type = mimetypes.guess_type(rasm_yoli.name)[0] or "image/jpeg"

    qismlar = [_qism("chat_id", str(tg_id))]
    if caption:
        qismlar.append(_qism("caption", caption[:1024]))
        qismlar.append(_qism("parse_mode", "HTML"))
    if tugma:
        qismlar.append(_qism("reply_markup", json.dumps(tugma)))

    fayl_sarlavha = (
        f"--{boundary}{crlf}"
        f'Content-Disposition: form-data; name="photo"; filename="{rasm_yoli.name}"{crlf}'
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
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get('ok', False)
    except Exception as e:
        print(f"  sendPhoto xatosi: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    try:
        tg_id = int(sys.argv[1])
    except ValueError:
        print(f"❌ Noto'g'ri telegram_id: {sys.argv[1]}")
        sys.exit(1)

    tur = sys.argv[2].lower()
    if tur not in ('rieltor', 'user'):
        print(f"❌ Tur noto'g'ri: '{tur}'. Faqat 'rieltor' yoki 'user' bo'lishi kerak.")
        sys.exit(1)

    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN topilmadi! .env faylni tekshiring.")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  Test xabari yuborilmoqda...")
    print(f"  Telegram ID : {tg_id}")
    print(f"  Tur         : {tur}")
    print(f"{'='*50}\n")

    if tur == 'rieltor':
        rasm = RIELTOR_RASM
        matn = RIELTOR_MATN
    else:
        rasm = USER_RASM
        matn = USER_MATN

    # Tugma
    tugma = None
    if MINI_APP_URL:
        tugma = ilova_tugmasi(MINI_APP_URL)
        print(f"  Tugma URL   : {MINI_APP_URL}?startapp=bozor")
    else:
        print("  ⚠ MINI_APP_WEB_URL topilmadi — tugmasiz yuboriladi")

    # Rasm holati
    print(f"  Rasm        : {'✅ ' + str(rasm) if rasm.is_file() else '❌ topilmadi — ' + str(rasm)}")
    print()

    # Yuborish
    if rasm.is_file():
        print("  📤 Rasm + matn yuborilmoqda...")
        natija = rasm_yuborish(tg_id, rasm, matn, tugma)
        if not natija:
            print("  ⚠ Rasm yuborilmadi, faqat matn yuborilmoqda...")
            natija = xabar_yuborish(tg_id, matn, tugma)
    else:
        print("  📤 Faqat matn yuborilmoqda (rasm yo'q)...")
        natija = xabar_yuborish(tg_id, matn, tugma)

    if natija:
        print(f"\n✅ Muvaffaqiyatli yuborildi! Telegram'ni tekshiring.")
    else:
        print(f"\n❌ Yuborilmadi. BOT_TOKEN yoki telegram_id'ni tekshiring.")
        print(f"   BOT_TOKEN (boshlanishi): {BOT_TOKEN[:10]}...")
        print(f"   Telegram ID: {tg_id}")


if __name__ == '__main__':
    main()
