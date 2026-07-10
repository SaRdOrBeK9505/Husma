"""
Obuna bilan bog'liq Telegram xabarnomalari.

Mavjud `apps.users.otp_service.telegram_xabar_yuborish` infratuzilmasidan
foydalanadi. Xabar yuborilmasa (bot bloklangan va h.k.) jim o'tadi — bu
biznes-logikani to'xtatmasligi kerak.
"""
from django.conf import settings
from apps.users.otp_service import telegram_xabar_yuborish


def _telegram_id(obuna) -> int | None:
    return getattr(obuna.rieltor.user, 'telegram_id', None)


def _obunalar_tugmasi():
    """Obunalar sahifasiga o'tish tugmasi."""
    # Telegram xabarlar uchun TELEGRAM_MINI_APP_URL ishlatiladi
    telegram_url = settings.TELEGRAM_MINI_APP_URL.rstrip('/')
    
    # Agar URL da allaqachon /obuna yoki ?startapp=... bo'lsa, qayta qo'shmaymiz
    # Aks holda /obuna qo'shamiz
    if '/obuna' in telegram_url or 'startapp=' in telegram_url:
        # URL allaqachon to'liq - hech narsa qo'shmaslik kerak
        final_url = telegram_url
    else:
        # Base URL - /obuna qo'shamiz
        final_url = f"{telegram_url}/obuna"
    
    # MUHIM: "url" emas, "web_app" ishlatish kerak!
    # "web_app" - Mini App sifatida ochiladi (initData bilan)
    # "url" - oddiy link (initData yo'q, login so'raydi)
    return {
        "inline_keyboard": [
            [
                {
                    "text": "📦 Obunalar sahifasiga o'tish",
                    "web_app": {"url": final_url}
                }
            ]
        ]
    }


def obuna_faollashdi_xabar(obuna):
    """Obuna muvaffaqiyatli faollashganda rieltorga xabar."""
    tg_id = _telegram_id(obuna)
    if not tg_id:
        return False

    tugash = obuna.tugash_vaqti.strftime('%d.%m.%Y') if obuna.tugash_vaqti else '-'
    matn = (
        f"✅ <b>Obunangiz faollashtirildi!</b>\n\n"
        f"📦 Tarif: <b>{obuna.tarif.nomi}</b>\n"
        f"💳 To'langan: <b>{obuna.narx:,} so'm</b>\n"
        f"📅 Amal qilish muddati: <b>{tugash}</b> gacha\n\n"
        f"Endi arizalarni qabul qilishingiz mumkin. Omad!"
    )
    return telegram_xabar_yuborish(tg_id, matn, reply_markup=_obunalar_tugmasi())


def obuna_tugashi_haqida_xabar(obuna, qolgan_kun: int):
    """Obuna tugashiga oz qolganda eslatma."""
    tg_id = _telegram_id(obuna)
    if not tg_id:
        return False

    matn = (
        f"⏰ <b>Obuna eslatmasi</b>\n\n"
        f"Sizning <b>{obuna.tarif.nomi}</b> obunangiz tugashiga "
        f"<b>{qolgan_kun} kun</b> qoldi.\n\n"
        f"Uzluksiz ishlash uchun obunani yangilashni unutmang."
    )
    return telegram_xabar_yuborish(tg_id, matn, reply_markup=_obunalar_tugmasi())


def obuna_tugadi_xabar(obuna):
    """Obuna muddati tugaganda xabar."""
    tg_id = _telegram_id(obuna)
    if not tg_id:
        return False

    matn = (
        f"🔔 <b>Obuna muddati tugadi</b>\n\n"
        f"<b>{obuna.tarif.nomi}</b> obunangiz muddati tugadi. "
        f"Arizalarni qabul qilishni davom ettirish uchun obunani yangilang."
    )
    return telegram_xabar_yuborish(tg_id, matn, reply_markup=_obunalar_tugmasi())


def bepul_muddat_tugadi_xabar(rieltor):
    """
    7 kunlik bepul sinov muddati tugaganda rieltorga xabar.
    
    Args:
        rieltor: MaklerProfil instance
    """
    tg_id = getattr(rieltor.user, 'telegram_id', None)
    if not tg_id:
        return False

    matn = (
        f"🎁 <b>Bepul sinov muddati tugadi</b>\n\n"
        f"7 kunlik bepul sinov muddatingiz tugadi. "
        f"Xizmatdan foydalanishni davom ettirish uchun obuna sotib oling.\n\n"
        f"💎 Bizning tariflarimiz bilan tanishing va o'zingizga mos tarifni tanlang!"
    )
    return telegram_xabar_yuborish(tg_id, matn, reply_markup=_obunalar_tugmasi())
