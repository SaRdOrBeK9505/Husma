"""
Obuna PROMO (aksiya) xabarini test qilish scripti.

Rasmdagi xabarni (rasm + matn + "Obunalar sahifasiga o'tish" tugmasi)
o'zingizga yuboradi. Bu AYNAN har kuni 10:00 dagi task va `promo_yubor`
komandasi yuboradigan xabarning o'zi — chunki xuddi shu `obuna_promo_xabar()`
funksiyasi chaqiriladi (tugma ham bir xil web_app tugmasi).

Ishlatish:
    # Telegram ID orqali (istalgan odamga):
    python test_obuna_button.py <TELEGRAM_ID>

    # Yoki bazadagi rieltor profili orqali (obuna_promo_xabar aynan shunday chaqiradi):
    python test_obuna_button.py --rieltor <TELEGRAM_ID>

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
    _obunalar_tugmasi,
    PROMO_OBUNA_RASM,
)
from apps.users.otp_service import (
    telegram_xabar_yuborish,
    telegram_rasm_yuborish,
)


def _yuborish_telegram_id(telegram_id: int) -> bool:
    """
    To'g'ridan-to'g'ri telegram_id ga yuboradi (bazada rieltor bo'lmasa ham).
    Natija AYNAN obuna_promo_xabar() bilan bir xil: rasm/matn + tugma.
    """
    matn = _obuna_promo_matni()
    tugma = _obunalar_tugmasi()

    if Path(PROMO_OBUNA_RASM).is_file():
        natija = telegram_rasm_yuborish(
            telegram_id, str(PROMO_OBUNA_RASM), caption=matn, reply_markup=tugma
        )
        if natija:
            return True
        print("⚠️  Rasm yuborilmadi, matnli ko'rinishga o'tilmoqda...")
    return telegram_xabar_yuborish(telegram_id, matn, reply_markup=tugma)


def _yuborish_rieltor(telegram_id: int) -> bool:
    """
    Bazadagi MaklerProfil orqali obuna_promo_xabar() ni chaqiradi —
    real (task/komanda) oqimning to'liq nusxasi.
    """
    from apps.makler.models import MaklerProfil
    try:
        rieltor = MaklerProfil.objects.get(user__telegram_id=telegram_id)
    except MaklerProfil.DoesNotExist:
        print(f"❌ telegram_id={telegram_id} uchun rieltor profili topilmadi.")
        print("   Oddiy test uchun --rieltor'siz ishlating.")
        return False
    return obuna_promo_xabar(rieltor)


def main():
    args = [a for a in sys.argv[1:]]
    rieltor_rejimi = '--rieltor' in args
    args = [a for a in args if a != '--rieltor']

    if not args:
        print("Xato: Telegram ID kiritilmadi.")
        print("Ishlatish: python test_obuna_button.py <TELEGRAM_ID> [--rieltor]")
        sys.exit(1)

    try:
        telegram_id = int(args[0])
    except ValueError:
        print(f"Xato: '{args[0]}' - butun son bo'lishi kerak.")
        sys.exit(1)

    rasm_bor = Path(PROMO_OBUNA_RASM).is_file()

    print("=" * 70)
    print("Obuna PROMO xabari — TEST")
    print(f"  Rejim       = {'RIELTOR (obuna_promo_xabar)' if rieltor_rejimi else 'TELEGRAM_ID'}")
    print(f"  Rasm yo'li  = {PROMO_OBUNA_RASM}")
    print(f"  Rasm bormi  = {'HA (rasm bilan)' if rasm_bor else 'YO‘Q (faqat matn)'}")
    print("=" * 70)
    print(f"\nXabar {telegram_id} ga yuborilmoqda...")

    if rieltor_rejimi:
        natija = _yuborish_rieltor(telegram_id)
    else:
        natija = _yuborish_telegram_id(telegram_id)

    if natija:
        print("✅ Xabar muvaffaqiyatli yuborildi! Telegram'ni tekshiring.")
        print("   Tugmani bosib, ilova auth'dan o'tishini (Open kabi) tekshiring.")
    else:
        print("❌ Xabar yuborilmadi.")
        print("   Sabablari:")
        print("   - TELEGRAM_BOT_TOKEN sozlanmagan bo'lishi mumkin")
        print("   - Telegram ID noto'g'ri yoki bot bloklangan")
        print("   - Foydalanuvchi bot bilan hali start bosmagan")
        print("   - Rasm fayli buzuq yoki juda katta (Telegram limiti 10 MB)")


if __name__ == "__main__":
    main()
