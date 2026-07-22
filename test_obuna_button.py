"""
Obuna xabaridagi tugmani (web_app -> /obuna) test qilish scripti.

Ishlatish:
    python test_obuna_button.py <TELEGRAM_ID>

Misol:
    python test_obuna_button.py 123456789

Bu script haqiqiy _obunalar_tugmasi() funksiyasidan foydalanib,
"Obuna eslatmasi" ko'rinishidagi xabarni sizga yuboradi. Shunda
tugmani bosib, u to'g'ri obunalar sahifasini ochishini tekshirasiz.
"""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from apps.users.otp_service import telegram_xabar_yuborish
from apps.obuna.notifications import _obunalar_tugmasi


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

    tugma = _obunalar_tugmasi()
    button = tugma['inline_keyboard'][0][0]
    if 'web_app' in button:
        tugma_turi = 'web_app (Mini App)'
        tugma_url = button['web_app']['url']
    else:
        tugma_turi = 'url (direct-link Mini App)'
        tugma_url = button['url']

    print("=" * 70)
    print("Sozlamalar:")
    print(f"  WEB_APP_URL           = {settings.WEB_APP_URL or '(bosh)'}")
    print(f"  TELEGRAM_MINI_APP_URL = {settings.TELEGRAM_MINI_APP_URL or '(bosh)'}")
    print(f"  Tugma turi            = {tugma_turi}")
    print(f"  Tugma URL             = {tugma_url}")
    print("=" * 70)

    matn = (
        f"⏰ <b>Obuna eslatmasi</b> (TEST)\n\n"
        f"Sizning <b>Birinchi oy</b> obunangiz tugashiga "
        f"<b>3 kun</b> qoldi.\n\n"
        f"Uzluksiz ishlash uchun obunani yangilashni unutmang.\n\n"
        f"<i>Bu test xabari. Quyidagi tugmani bosib, obunalar "
        f"sahifasi to'g'ri ochilishini tekshiring.</i>"
    )

    print(f"\nXabar {telegram_id} ga yuborilmoqda...")
    natija = telegram_xabar_yuborish(telegram_id, matn, reply_markup=tugma)

    if natija:
        print("✅ Xabar muvaffaqiyatli yuborildi! Telegram'ni tekshiring.")
    else:
        print("❌ Xabar yuborilmadi.")
        print("   Sabablari:")
        print("   - TELEGRAM_BOT_TOKEN sozlanmagan bo'lishi mumkin")
        print("   - Telegram ID noto'g'ri yoki bot bloklangan")
        print("   - Foydalanuvchi bot bilan hali start bosmagan")


if __name__ == "__main__":
    main()
