"""
Obuna bilan bog'liq Telegram xabarnomalari.

Mavjud `apps.users.otp_service.telegram_xabar_yuborish` infratuzilmasidan
foydalanadi. Xabar yuborilmasa (bot bloklangan va h.k.) jim o'tadi — bu
biznes-logikani to'xtatmasligi kerak.
"""
from apps.users.otp_service import telegram_xabar_yuborish


def _telegram_id(obuna) -> int | None:
    return getattr(obuna.rieltor.user, 'telegram_id', None)


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
    return telegram_xabar_yuborish(tg_id, matn)


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
    return telegram_xabar_yuborish(tg_id, matn)


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
    return telegram_xabar_yuborish(tg_id, matn)
