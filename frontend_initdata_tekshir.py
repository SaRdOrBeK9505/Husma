"""
Frontendchi bergan REAL initData qaysi bot tokeni bilan imzolanganini aniqlaydi.

Bu — backend kodi to'g'ri ekanini ISBOTLAYDI va token mosligini tekshiradi.

ISHLATISH:
  1. INIT_DATA ga frontendchi bergan TO'LIQ initData stringini qo'ying.
  2. TOKENLAR ro'yxatiga tekshirmoqchi bo'lgan token(lar)ni qo'ying.
  3. .venv\\Scripts\\python.exe frontend_initdata_tekshir.py
"""
import hashlib
import hmac
from urllib.parse import parse_qsl

# --- Frontendchi bergan TO'LIQ initData stringini shu yerga qo'ying ---
INIT_DATA = "BU_YERGA_FRONTENDCHI_BERGAN_INITDATA"

# --- Tekshiriladigan token(lar). BotFather'dan olingan tokenlarni qo'ying ---
TOKENLAR = [
    # "8810767573:AAH9QBZB68CSKLHKjQ_Elxim1odstce3mvI",
    # "8958937075:AAEFyjH6v_6_Gfy-eYNhH2-AmgEbHPpNI8U",
]


def hisobla(init_data: str, token: str):
    parsed = dict(parse_qsl(init_data, strict_parsing=False))
    received = parsed.pop("hash", None)
    parsed.pop("signature", None)  # yangi Telegram maydoni — hashga kirmaydi
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return received, calc, dcs


def main():
    if INIT_DATA.startswith("BU_YERGA"):
        raise SystemExit("Avval INIT_DATA ga frontendchi bergan initData ni qo'ying.")
    if not TOKENLAR:
        raise SystemExit("Avval TOKENLAR ro'yxatiga token(lar) qo'ying.")

    parsed = dict(parse_qsl(INIT_DATA, strict_parsing=False))
    print("initData kalitlari:", list(parsed.keys()))
    print("Kelgan hash:", parsed.get("hash"))
    print()

    topildi = False
    for token in TOKENLAR:
        received, calc, dcs = hisobla(INIT_DATA, token)
        mos = (received == calc)
        belgi = "✅ MOS KELDI" if mos else "❌ mos emas"
        print(f"Token ...{token[-6:]}: {belgi}")
        if mos:
            topildi = True
            print("\n  >>> Mini App AYNAN shu token egasi bo'lgan botda ochilgan.")
            print("  >>> Server .env ga SHU tokenni qo'ying va Reload qiling.\n")

    if not topildi:
        print("\nHech bir token mos kelmadi. Sabablar:")
        print("  - Bu tokenlardan birortasi ham Mini App'ni ochgan bot emas.")
        print("  - Frontendchidan to'g'ri bot tokenini so'rang.")
        print("\nDiagnostika uchun data_check_string:")
        _, _, dcs = hisobla(INIT_DATA, TOKENLAR[0])
        print(dcs)


if __name__ == "__main__":
    main()
