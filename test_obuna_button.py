"""
Obuna PROMO (aksiya) xabarini test qilish scripti.

Rasmdagi xabarni (rasm + matn) o'zingizga yuboradi. Rasm
`assets/promo/obuna_promo.jpg` yo'lida bo'lsa rasm bilan, bo'lmasa faqat
matnli ko'rinishda yuboriladi.

Ishlatish:
    python test_obuna_button.py <TELEGRAM_ID>

Misol:
    python test_obuna_button.py 123456789
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from pathlib import Path

from apps.obuna.notifications import (
    obuna_promo_xabar,
    _obuna_promo_matni,
    PROMO_OBUNA_RASM,
)
from apps.users.otp_service import (
    telegram_xabar_yuborish,
    telegram_rasm_yuborish,
)


def main():
    if len(sys.argv) < 2:
        print("Xato: Telegram ID kiritilmadi.")
        print("Ishlatish: python test_obuna_button.py <TELEGRAM_ID>")
        sys.exit(1)

    try:
        telegram_id = int(sys.argv[1])
    except ValueError:
        print(f"Xato: '{sys.argv[1]}' - butun son bo'lishi kerak.")
        sys.exit(1)

    rasm_bor = Path(PROMO_OBUNA_RASM).is_file()

    print("=" * 70)
    print("Obuna PROMO xabari — TEST")
    print(f"  Rasm yo'li  = {PROMO_OBUNA_RASM}")
    print(f"  Rasm bormi  = {'HA (rasm bilan yuboriladi)' if rasm_bor else 'YO‘Q (faqat matn yuboriladi)'}")
    print("=" * 70)

    matn = _obuna_promo_matni()

    print(f"\nXabar {telegram_id} ga yuborilmoqda...")

    # obuna_promo_xabar() MaklerProfil kutadi; bu yerda esa to'g'ridan-to'g'ri
    # telegram_id ga yuborish uchun ichki funksiyalarni chaqiramiz — natija
    # AYNAN obuna_promo_xabar() bilan bir xil bo'ladi.
    if rasm_bor:
        natija = telegram_rasm_yuborish(telegram_id, str(PROMO_OBUNA_RASM), caption=matn)
        if not natija:
            print("⚠️  Rasm yuborilmadi, matnli ko'rinishga o'tilmoqda...")
            natija = telegram_xabar_yuborish(telegram_id, matn)
    else:
        natija = telegram_xabar_yuborish(telegram_id, matn)

    if natija:
        print("✅ Xabar muvaffaqiyatli yuborildi! Telegram'ni tekshiring.")
    else:
        print("❌ Xabar yuborilmadi.")
        print("   Sabablari:")
        print("   - TELEGRAM_BOT_TOKEN sozlanmagan bo'lishi mumkin")
        print("   - Telegram ID noto'g'ri yoki bot bloklangan")
        print("   - Foydalanuvchi bot bilan hali start bosmagan")
        print("   - Rasm fayli buzuq yoki juda katta (Telegram limiti 10 MB)")


if __name__ == "__main__":
    main()
