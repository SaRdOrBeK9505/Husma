"""
Celery vazifalar — ariza notification tizimi.

Telegram 403 xatolari (bot bloklangan / user /start bosmaganligi):
  - _telegram_yubor() doimiy xatolarni aniqlaydi va maklerni
    telegram_bloklangan=True qilib belgilaydi (retry yo'q).
  - Tasklar boshida telegram_bloklangan=True bo'lsa darhol chiqib ketadi.
  - Bu qayta-qayta bekorga so'rov yuborilishining oldini oladi.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from celery.exceptions import Retry

from .models import Ariza, ArizaMakler

logger = logging.getLogger(__name__)

# Doimiy blok sifatida qabul qilinadigan Telegram error descriptionlari
# (kichik harfda taqqoslanadi)
_DOIMIY_BLOK_XABARLAR = (
    "bot was blocked by the user",
    "chat not found",
    "user is deactivated",
    "bot can't initiate conversation",
)


def _makler_bloklangan_mi(telegram_id) -> bool:
    """
    Berilgan telegram_id ga ega maklerning telegram_bloklangan holatini tekshiradi.

    Returns:
        True — bloklangan (xabar yubormaslik kerak)
        False — bloklangan emas yoki makler topilmadi
    """
    from apps.makler.models import MaklerProfil
    try:
        profil = MaklerProfil.objects.select_related('user').get(
            user__telegram_id=telegram_id
        )
        return profil.telegram_bloklangan
    except MaklerProfil.DoesNotExist:
        return False


def _maklerni_bloklangan_deb_belGila(telegram_id: int, sabab: str) -> None:
    """
    Telegram 403 doimiy xatosi kelganda maklerni bloklangan deb belgilaydi.

    Args:
        telegram_id: Bloqlanadigan foydalanuvchining Telegram IDsi
        sabab: Telegram API dan kelgan error description (log uchun)
    """
    from apps.makler.models import MaklerProfil
    try:
        profil = MaklerProfil.objects.select_related('user').get(
            user__telegram_id=telegram_id
        )
        if not profil.telegram_bloklangan:
            profil.telegram_bloklangan = True
            profil.telegram_bloklangan_vaqt = timezone.now()
            profil.save(update_fields=['telegram_bloklangan', 'telegram_bloklangan_vaqt'])
            logger.warning(
                "[Telegram Blok] Makler telegram_bloklangan=True qilindi: "
                "makler_profil_id=%s, telegram_id=%s, sabab='%s'",
                profil.id, telegram_id, sabab,
            )
        else:
            logger.info(
                "[Telegram Blok] Makler allaqachon bloklangan holda: "
                "makler_profil_id=%s, telegram_id=%s",
                profil.id, telegram_id,
            )
    except MaklerProfil.DoesNotExist:
        logger.warning(
            "[Telegram Blok] telegram_id=%s uchun MaklerProfil topilmadi, "
            "bloklash o'tkazib yuborildi.", telegram_id,
        )


@shared_task(
    bind=True,
    max_retries=2,           # 3 dan 2 ga kamaytiriildi — faqat haqiqiy vaqtinchalik xatolar
    default_retry_delay=60,  # 1 daqiqa keyin qayta urinish
)
def yangi_ariza_xabari_yubor(self, ariza_makler_id: int) -> dict:
    """
    Rieltorga yangi ariza haqida Telegram xabari yuboradi.

    Idempotent: bir xil ariza_makler_id uchun bir necha marta chaqirilsa ham,
    faqat bitta xabar yuboriladi (ArizaMakler holatini tekshiradi).

    Retry: faqat vaqtinchalik xatolar (tarmoq, 429, 500) uchun 2 marta qayta urinadi.
    403 (bot bloklangan) uchun retry yo'q — makler DB'da bloklangan deb belgilanadi.

    Args:
        ariza_makler_id: ArizaMakler modeli ID si

    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        # ArizaMaklerni olish
        ariza_makler = ArizaMakler.objects.select_related(
            'rieltor__user',
            'ariza__user',
            'ariza__mulk_turi',
            'ariza__hudud'
        ).get(id=ariza_makler_id)

        # Idempotency tekshiruvi: agar allaqachon ko'rildi bo'lsa, xabar yubormaslik
        if ariza_makler.holat != ArizaMakler.Holat.YANGI:
            logger.info(
                "[Ariza Notification] ArizaMakler %s allaqachon %s holatida, "
                "xabar yuborilmadi.",
                ariza_makler_id, ariza_makler.holat,
            )
            return {
                "success": False,
                "message": f"Ariza allaqachon {ariza_makler.holat} holatida"
            }

        # Rieltorning telegram_id sini tekshirish
        telegram_id = ariza_makler.rieltor.user.telegram_id
        if not telegram_id:
            logger.warning(
                "[Ariza Notification] Rieltor %s da telegram_id yo'q",
                ariza_makler.rieltor.id,
            )
            return {
                "success": False,
                "message": "Rieltorda telegram_id yo'q"
            }

        # --- BLOK TEKSHIRUVI: Telegram bloklagan bo'lsa so'rov yubormaymiz ---
        if _makler_bloklangan_mi(telegram_id):
            logger.info(
                "[Ariza Notification] O'tkazib yuborildi — makler Telegram bloklangan: "
                "rieltor_id=%s, telegram_id=%s, ariza_makler_id=%s",
                ariza_makler.rieltor.id, telegram_id, ariza_makler_id,
            )
            return {
                "success": False,
                "message": "Makler Telegram bloklangan, xabar yuborilmadi"
            }

        # Xabar matnini tayyorlash
        xabar_matni = _xabar_matni_tayorla(ariza_makler)

        # Mijoz bilan Telegram orqali bog'lanish tugmasi
        reply_markup = _bogla_tugma(ariza_makler.ariza.user)

        # Telegram API orqali yuborish
        _telegram_yubor(telegram_id, xabar_matni, reply_markup=reply_markup)

        # Muvaffaqiyatli yuborilgandan keyin holatni yangilash
        ariza_makler.holat = ArizaMakler.Holat.KORILDI
        ariza_makler.korilgan_vaqt = timezone.now()
        ariza_makler.save(update_fields=['holat', 'korilgan_vaqt'])

        logger.info(
            "[Ariza Notification] Xabar muvaffaqiyatli yuborildi: "
            "rieltor=%s, ariza=%s",
            ariza_makler.rieltor.user.username,
            ariza_makler.ariza.id,
        )

        return {
            "success": True,
            "message": "Xabar muvaffaqiyatli yuborildi"
        }

    except ArizaMakler.DoesNotExist:
        logger.error(
            "[Ariza Notification] ArizaMakler %s topilmadi", ariza_makler_id
        )
        return {
            "success": False,
            "message": "ArizaMakler topilmadi"
        }

    except _TelegramDoimiyXato as exc:
        # Doimiy xato (403 bloklangan) — retry qilmaymiz, shunchaki qaytamiz
        logger.warning(
            "[Ariza Notification] Doimiy Telegram xatosi, retry yo'q: "
            "ariza_makler_id=%s, xato='%s'",
            ariza_makler_id, exc,
        )
        return {
            "success": False,
            "message": f"Telegram doimiy xato: {exc}"
        }

    except Exception as exc:
        logger.error(
            "[Ariza Notification] Xato: ariza_makler_id=%s, err=%s",
            ariza_makler_id, exc,
            exc_info=True,
        )

        # Retry mechanism — faqat vaqtinchalik xatolar (tarmoq, 429, 500) uchun
        if self.request.retries < self.max_retries:
            logger.info(
                "[Ariza Notification] Qayta urinish: %s/%s",
                self.request.retries + 1, self.max_retries,
            )
            raise self.retry(exc=exc)

        # Barcha urinishlar muvaffaqiyatsiz bo'lsa
        return {
            "success": False,
            "message": f"Xato: {str(exc)}"
        }


def _telefon_tozala(telefon: str) -> str:
    """
    Telefon raqamni Telegram avtomatik aniqlaydigan (dialer ochiladigan)
    xalqaro formatga keltiradi: faqat '+' va raqamlar.

    Masalan: "+998 (93) 577-15-07" -> "+998935771507"
    """
    if not telefon:
        return ""
    raqamlar = "".join(ch for ch in telefon if ch.isdigit())
    if not raqamlar:
        return ""
    return f"+{raqamlar}"


def _telegram_bogla_url(user) -> str:
    """
    Mijoz bilan Telegram orqali bog'lanish uchun URL qaytaradi.

    - Agar telegram_username bo'lsa -> https://t.me/<username>
    - Aks holda -> bo'sh string (telegram_id orqali inline tugma ishlamaydi)

    MUHIM: tg://user?id=<telegram_id> deep link Telegram Bot API
    inline_keyboard da qo'llab-quvvatlanmaydi — faqat https:// URLlar ishlaydi.
    """
    if user is None:
        return ""

    username = (getattr(user, 'telegram_username', '') or '').lstrip('@').strip()
    if username:
        return f"https://t.me/{username}"

    return ""


def _bogla_tugma(user) -> dict | None:
    """
    Mijoz bilan Telegram orqali bog'lanish uchun inline tugma (reply_markup)
    yasaydi. Agar bog'lanish uchun ma'lumot bo'lmasa None qaytaradi.
    """
    url = _telegram_bogla_url(user)
    if not url:
        return None

    return {
        "inline_keyboard": [
            [
                {
                    "text": "✈️ Telegram orqali bog'lanish",
                    "url": url,
                }
            ]
        ]
    }


def _xabar_matni_tayorla(ariza_makler: ArizaMakler) -> str:
    """Xabar matnini tayyorlaydi."""
    ariza = ariza_makler.ariza
    mulk_turi = ariza.mulk_turi.nomi if ariza.mulk_turi else "Noma'lum"
    hudud = ariza.hudud.nomi if ariza.hudud else "Noma'lum"
    valyuta = ariza.get_valyuta_display()
    if ariza.narx_max is not None:
        narx = f"{ariza.narx_min:,} - {ariza.narx_max:,} {valyuta}"
    else:
        narx = f"{ariza.narx_min:,}+ {valyuta}"
    # Telefonni dialer ochiladigan toza formatda ko'rsatamiz
    telefon_str = _telefon_tozala(ariza.telefon) or "Ko'rsatilmagan"

    # Ariza turi (maqsad) - ijaraga olish, sotib olish, ijaraga berish yoki sotish
    ariza_turi = ariza.get_ariza_turi_display()

    # Xonalar soni
    xonalar = ariza.get_xonalar_soni_display()

    # Ism (agar mavjud bo'lsa)
    ism_qatori = f"👤 Ism: {ariza.ism}\n" if ariza.ism else ""
    # Qo'shimcha izoh (agar mavjud bo'lsa)
    izoh_qatori = f"📝 Izoh: {ariza.qoshimcha_izoh}\n" if ariza.qoshimcha_izoh else ""

    matn = (
        f"🔔 *Mijozdan yangi ariza tushdi!*\n\n"
        f"🎯 Maqsad: {ariza_turi}\n"
        f"🏠 Mulk turi: {mulk_turi}\n"
        f"🛏 Xonalar: {xonalar}\n"
        f"📌 Hudud: {hudud}\n"
        f"💰 Narx: {narx}\n"
        f"{ism_qatori}"
        f"📞 Tel: {telefon_str}\n"
        f"{izoh_qatori}"
    )

    return matn


class _TelegramDoimiyXato(Exception):
    """
    Telegram 403 javobidan kelinadigan doimiy xato.

    Bu exception celery retry mexanizmini chetlab o'tadi.
    Faqat _telegram_yubor() tomonidan raise qilinadi.
    """
    pass


def _telegram_yubor(chat_id: int, text: str, reply_markup: dict | None = None) -> None:
    """
    Telegram Bot API orqali xabar yuboradi.

    Xato turlari:
      - 403 + doimiy sabab (bot bloklangan, deactivated va h.k.):
          maklerni DB'da bloklaydi, _TelegramDoimiyXato raise qiladi
          (Celery retry QILINMAYDI).
      - 403 + noma'lum sabab, 429, 500, tarmoq xatosi:
          oddiy Exception raise qiladi (Celery retry QILADI).

    Args:
        chat_id: Qabul qiluvchi chat/telegram ID
        text: Xabar matni (Markdown)
        reply_markup: (ixtiyoriy) inline tugmalar uchun markup
    """
    import requests

    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN sozlanmagan")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup

    try:
        response = requests.post(url, json=payload, timeout=10)
    except requests.exceptions.RequestException as exc:
        # Tarmoq xatosi — vaqtinchalik, retry qilinadi
        raise Exception(f"Tarmoq xatosi: {exc}") from exc

    # --- 403: bot bloklangan yoki user /start bosmagan ---
    if response.status_code == 403:
        description = ""
        try:
            description = response.json().get('description', '').lower()
        except Exception:
            pass

        logger.warning(
            "[Telegram 403] chat_id=%s, description='%s'", chat_id, description
        )

        # Doimiy blok sabablarini tekshiramiz
        doimiy = any(sabab in description for sabab in _DOIMIY_BLOK_XABARLAR)
        if doimiy:
            # Maklerni DB'da belgilaymiz
            _maklerni_bloklangan_deb_belGila(chat_id, description)
            raise _TelegramDoimiyXato(description)

        # 403 lekin noma'lum sabab — oddiy exception (retry qilinadi)
        noma_lum = "noma'lum sabab"
        raise Exception(f"Telegram 403: {description or noma_lum}")

    # --- Boshqa HTTP xatolar (429, 500, ...) — vaqtinchalik, retry ---
    try:
        response.raise_for_status()
    except Exception as exc:
        raise Exception(f"Telegram HTTP {response.status_code}: {exc}") from exc

    data = response.json()
    if not data.get('ok'):
        raise Exception(f"Telegram API xatosi: {data}")


@shared_task(
    bind=True,
    max_retries=2,           # 3 dan 2 ga kamaytirildi
    default_retry_delay=60,
)
def kanalga_yangi_ariza_xabari_yubor(self, ariza_id: int) -> dict:
    """
    Yangi ariza haqida Telegram kanalga xabar yuboradi.

    Idempotent: bir xil ariza_id uchun bir necha marta chaqirilsa ham,
    faqat bitta xabar yuboriladi (ariza holatini tekshiradi).

    Retry: xato bo'lsa 2 marta qayta urinadi (har biridan keyin 1 daqiqa).

    Args:
        ariza_id: Ariza modeli ID si

    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        # Arizani olish
        ariza = Ariza.objects.select_related(
            'mulk_turi',
            'hudud'
        ).get(id=ariza_id)

        # Idempotency tekshiruvi: faqat yangi holatdagi arizalar uchun
        if ariza.holat != Ariza.Holat.YANGI:
            logger.info(
                "[Kanal Notification] Ariza %s allaqachon %s holatida, "
                "kanalga xabar yuborilmadi.",
                ariza_id, ariza.holat,
            )
            return {
                "success": False,
                "message": f"Ariza allaqachon {ariza.holat} holatida"
            }

        # Xabar matnini tayyorlash
        mulk_turi = ariza.mulk_turi.nomi if ariza.mulk_turi else "Noma'lum"
        hudud = ariza.hudud.nomi if ariza.hudud else "Noma'lum"
        valyuta = ariza.get_valyuta_display()
        if ariza.narx_max is not None:
            narx = f"{ariza.narx_min:,} - {ariza.narx_max:,} {valyuta}"
        else:
            narx = f"{ariza.narx_min:,}+ {valyuta}"
        telefon_str = _telefon_tozala(ariza.telefon) or "Ko'rsatilmagan"

        ariza_turi = ariza.get_ariza_turi_display()
        xonalar = ariza.get_xonalar_soni_display()

        ism_qatori = f"👤 Ism: {ariza.ism}\n" if ariza.ism else ""
        izoh_qatori = f"📝 Izoh: {ariza.qoshimcha_izoh}\n" if ariza.qoshimcha_izoh else ""

        xabar_matni = (
            f"📋 *Mijozdan yangi ariza tushdi!*\n\n"
            f"🎯 Maqsad: {ariza_turi}\n"
            f"🏠 Mulk turi: {mulk_turi}\n"
            f"🛏 Xonalar: {xonalar}\n"
            f"📌 Hudud: {hudud}\n"
            f"💰 Narx: {narx}\n"
            f"{ism_qatori}"
            f"📞 Tel: {telefon_str}\n"
            f"{izoh_qatori}"
        )

        # Kanalga yuborish - ARIZA kanali
        from core.telegram_utils import telegram_kanalga_yubor
        yuborildi = telegram_kanalga_yubor(xabar_matni, channel_type='ariza')

        if yuborildi:
            logger.info(
                "[Kanal Notification] Ariza %s haqida kanalga xabar yuborildi",
                ariza_id,
            )
            return {
                "success": True,
                "message": "Kanalga xabar muvaffaqiyatli yuborildi"
            }
        else:
            logger.warning(
                "[Kanal Notification] Ariza %s haqida kanalga xabar yuborilmadi",
                ariza_id,
            )
            return {
                "success": False,
                "message": "Kanalga xabar yuborilmadi"
            }

    except Ariza.DoesNotExist:
        logger.error("[Kanal Notification] Ariza %s topilmadi", ariza_id)
        return {
            "success": False,
            "message": "Ariza topilmadi"
        }

    except Exception as exc:
        logger.error(
            "[Kanal Notification] Xato: ariza_id=%s, err=%s",
            ariza_id, exc,
            exc_info=True,
        )

        if self.request.retries < self.max_retries:
            logger.info(
                "[Kanal Notification] Qayta urinish: %s/%s",
                self.request.retries + 1, self.max_retries,
            )
            raise self.retry(exc=exc)

        return {
            "success": False,
            "message": f"Xato: {str(exc)}"
        }
