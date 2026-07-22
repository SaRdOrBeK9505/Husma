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
    """Obunalar sahifasiga o'tish tugmasi.

    Bot ichidagi "Open" tugmasi bilan AYNAN BIR XIL ishlashi uchun inline
    `web_app` tugmasi ilovaning hosted domeni ROOT'iga yo'naltiriladi:
      - `web_app` tugmasi Telegram tomonidan `initData` (auth) bilan ochiladi,
        xuddi "Open" tugmasi kabi -> rieltor paneli/arizalar yuklanadi.
      - Desktop va mobil'da bir xil ishlaydi.
      - ROOT'ga yo'naltiramiz (path QO'SHMAYMIZ), chunki `/obuna` kabi chuqur
        path SPA/auth init'ini buzadi (ilgari shu sabab ma'lumot kelmagan).
      - Obuna sahifasiga o'tish signali `startapp` QUERY parametri orqali
        beriladi. Frontend `Telegram.WebApp.initDataUnsafe.start_param` yoki
        URL query'dagi `startapp` ni o'qib obuna sahifasiga o'tkazishi kerak.

    MUHIM: bu yerda `t.me/...` link (direct-link) ISHLATILMAYDI, chunki uni
    oddiy `url` tugma orqali ochish "Open" bilan bir xil launch kontekstini
    (initData) bermaydi -> ilova autentifikatsiyasiz ochiladi.
    """
    # Mini App HOSTED domeni (BotFather "Open" ochadigan URL) ishlatiladi.
    # Bu MULTICARD uchun ishlatiladigan WEB_APP_URL dan farq qilishi mumkin.
    base_url = (
        settings.MINI_APP_WEB_URL
        or settings.WEB_APP_URL
        or settings.TELEGRAM_MINI_APP_URL
    ).rstrip('/')

    # startapp query obuna sahifasini signal qiladi (path QO'SHILMAYDI).
    if 'startapp=' in base_url:
        final_url = base_url
    else:
        sep = '&' if '?' in base_url else '?'
        final_url = f"{base_url}{sep}startapp=obuna"

    return {
        "inline_keyboard": [
            [
                {
                    "text": "📦 Obunalar sahifasiga o'tish",
                    "web_app": {"url": final_url},
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


def qoshimcha_bepul_muddat_tabrik_xabar(rieltor, kun: int):
    """
    14 kunlik qo'shimcha bepul sinov muddati berilganda rieltorga tabrik xabari.

    Args:
        rieltor: MaklerProfil instance
        kun: Berilgan qo'shimcha kunlar soni (masalan 14)

    Returns:
        bool: xabar yuborilgan bo'lsa True, aks holda False
    """
    tg_id = getattr(rieltor.user, 'telegram_id', None)
    if not tg_id:
        return False

    tugash = (
        rieltor.bepul_muddat_tugash.strftime('%d.%m.%Y')
        if rieltor.bepul_muddat_tugash else '-'
    )
    matn = (
        f"🎉 <b>Sizga sovg'a bor!</b>\n\n"
        f"Hurmatli hamkorimiz, sizga qo'shimcha "
        f"<b>{kun} kunlik BEPUL</b> foydalanish muddati taqdim etildi! 🎁\n\n"
        f"📅 Yangi muddat: <b>{tugash}</b> gacha amal qiladi.\n\n"
        f"Ushbu muddat ichida barcha imkoniyatlardan bemalol "
        f"foydalanishingiz mumkin. Omad tilaymiz! 🚀"
    )
    return telegram_xabar_yuborish(tg_id, matn)
