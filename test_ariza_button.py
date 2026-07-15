"""
TEST: Ariza xabari — telefon (dialer) + Telegram bog'lanish tugmasi.

Bu script o'zingizga (admin) test xabar yuboradi va tekshirishga yordam beradi:
  1. Telefon raqamni bosganda telefon (dialer) ilovasi ochilishi
  2. "Telegram orqali bog'lanish" tugmasi mijoz chatini ochishi

Ishga tushirish:
    python test_ariza_button.py
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ariza.tasks import (
    _telefon_tozala,
    _telegram_bogla_url,
    _bogla_tugma,
    _telegram_yubor,
)


def send_test_message(telegram_id: int, test_username: str, test_user_id: int):
    """Real ariza xabari ko'rinishida test xabar yuboradi."""

    # --- Namuna ariza ma'lumotlari ---
    ariza_turi = "Ijaraga olish"
    mulk_turi = "Kvartira"
    xonalar = "2 xonali"
    hudud = "Shayxontohur"
    narx = "3,500,000 - 4,500,000 so'm"
    ism = "Farangiz"
    xom_telefon = "+998 (93) 577-15-07"

    # Telefonni dialer ochiladigan toza formatga keltiramiz
    telefon_str = _telefon_tozala(xom_telefon) or "Ko'rsatilmagan"

    matn = (
        f"🔔 *Mijozdan yangi ariza tushdi!* (TEST)\n\n"
        f"🎯 Maqsad: {ariza_turi}\n"
        f"🏠 Mulk turi: {mulk_turi}\n"
        f"🛏 Xonalar: {xonalar}\n"
        f"📌 Hudud: {hudud}\n"
        f"💰 Narx: {narx}\n"
        f"👤 Ism: {ism}\n"
        f"📞 Tel: {telefon_str}\n"
    )

    # --- Telegram bog'lanish tugmasini yasash ---
    # test_username / test_user_id — bu "mijoz" ni ifodalaydi.
    class _SoxtaUser:
        telegram_username = test_username
        telegram_id = test_user_id

    reply_markup = _bogla_tugma(_SoxtaUser())

    bogla_url = _telegram_bogla_url(_SoxtaUser())
    print(f"\n🔗 Bog'lanish tugmasi URL: {bogla_url or '(yo‘q)'}")
    print(f"📞 Toza telefon (dialer): {telefon_str}\n")

    try:
        _telegram_yubor(telegram_id, matn, reply_markup=reply_markup)
        print("✅ Test xabar muvaffaqiyatli yuborildi!")
        return True
    except Exception as e:
        print(f"❌ Xato yuz berdi: {e}")
        return False


def main():
    print("=" * 60)
    print("🧪 TEST: Ariza xabari — telefon + Telegram tugma")
    print("=" * 60)

    telegram_id = input("\n👤 Xabar yuboriladigan Telegram ID (o'zingiz): ").strip()
    if not telegram_id.lstrip('-').isdigit():
        print("❌ Telegram ID faqat raqamlardan iborat bo'lishi kerak!")
        return
    telegram_id = int(telegram_id)

    print("\n--- Bog'lanish tugmasi uchun 'mijoz' ma'lumoti ---")
    print("(Tekshirish uchun o'zingizning username/ID ni kiritsangiz bo'ladi)")
    test_username = input("Mijoz Telegram username (@siz, bo'sh qoldirsa ID ishlatiladi): ").strip().lstrip('@')
    test_user_id_raw = input("Mijoz Telegram ID (username bo'lmasa ishlatiladi): ").strip()
    test_user_id = int(test_user_id_raw) if test_user_id_raw.isdigit() else None

    print(f"\n📤 {telegram_id} ga test xabar yuborilmoqda...\n")
    send_test_message(telegram_id, test_username or "", test_user_id)

    print("\n💡 Tekshiring:")
    print("   1. 📞 Telefon raqamni bosing → qo'ng'iroq ilovasi ochilishi kerak")
    print("   2. ✈️ 'Telegram orqali bog'lanish' tugmasini bosing → chat ochilishi kerak")
    print()


if __name__ == "__main__":
    main()
