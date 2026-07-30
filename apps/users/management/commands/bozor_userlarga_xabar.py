"""
Management command — barcha registered userlarga (role='user')
Uy bozori haqida bir martalik Telegram xabari (rasm + matn + tugma) yuboradi.

TEZLIK:
  Parallel yuborish (25 ta bir vaqtda) — 2000 kishi ~2 daqiqada tugaydi.
  Tashqi kutubxona shart emas (asyncio + ThreadPoolExecutor, stdlib).

RASM:
  assets/promo/bozor_user_promo.jpg  (yoki .png)
  Shu faylni avval assets/promo/ papkasiga qo'ying.

KIMGA YUBORILADI:
  ✅ role='user' bo'lgan hamma foydalanuvchilar
  ✅ telegram_id mavjud bo'lganlari
  ✅ is_active=True bo'lganlari

ISHLATISH:
    # Ko'rish — hech narsa yubormaydi
    python manage.py bozor_userlarga_xabar --dry-run

    # Sinov uchun o'zingizga
    python manage.py bozor_userlarga_xabar --telegram-id 123456789

    # Faqat dastlabki N tasiga
    python manage.py bozor_userlarga_xabar --limit 5

    # Hammaga (parallel, tez)
    python manage.py bozor_userlarga_xabar

    # Parallel miqdorini o'zgartirish (default 25)
    python manage.py bozor_userlarga_xabar --parallel 20
"""
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.users.otp_service import telegram_xabar_yuborish, telegram_rasm_yuborish

logger = logging.getLogger('bozor_userlarga_xabar')

RASM_YOL = settings.BASE_DIR / 'assets' / 'promo' / 'bozor_user_promo.jpg'

# Telegram flood limit: 30 xabar/sek
# 25 parallel + har batch orasida 1 sek pauza = xavfsiz
MAX_PARALLEL = 25
BATCH_PAUZA = 1.0  # har 25 ta batch orasida kutish (soniya)

DEFAULT_MATN = (
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


def _ilova_tugmasi():
    base_url = (
        getattr(settings, 'MINI_APP_WEB_URL', '')
        or getattr(settings, 'WEB_APP_URL', '')
        or getattr(settings, 'TELEGRAM_MINI_APP_URL', '')
        or ''
    ).rstrip('/')

    if not base_url:
        return None

    if 'startapp=' in base_url:
        final_url = base_url
    else:
        sep = '&' if '?' in base_url else '?'
        final_url = f"{base_url}{sep}startapp=bozor"

    return {
        "inline_keyboard": [
            [{"text": "Ilovani ochish", "web_app": {"url": final_url}}]
        ]
    }


def _bitta_yuborish(tg_id: int, matn: str, rasm_bor: bool, tugma) -> tuple[int, bool]:
    """
    Bitta foydalanuvchiga xabar yuboradi.
    (tg_id, muvaffaqiyatmi) qaytaradi.
    ThreadPoolExecutor ichida ishlatiladi.
    """
    try:
        if rasm_bor:
            natija = telegram_rasm_yuborish(
                tg_id, str(RASM_YOL),
                caption=matn[:1024],
                reply_markup=tugma,
            )
            if not natija:
                natija = telegram_xabar_yuborish(tg_id, matn, reply_markup=tugma)
        else:
            natija = telegram_xabar_yuborish(tg_id, matn, reply_markup=tugma)
        return tg_id, bool(natija)
    except Exception as exc:
        logger.error("[BozorUser] Xato: tg_id=%s err=%s", tg_id, exc)
        return tg_id, False


class Command(BaseCommand):
    help = (
        "Barcha userlarga (role='user') Uy bozori haqida bir martalik "
        "Telegram xabari yuboradi. Parallel yuborish — tez va xavfsiz."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Hech narsa yubormaydi, faqat kimga yuborilishini ko'rsatadi",
        )
        parser.add_argument(
            '--limit', type=int, default=None,
            help="Faqat birinchi N ta userlarga yuborish (sinov uchun)",
        )
        parser.add_argument(
            '--parallel', type=int, default=MAX_PARALLEL,
            help=f"Bir vaqtda nechta parallel yuborish (default: {MAX_PARALLEL}, max: 25)",
        )
        parser.add_argument(
            '--matn', type=str, default=None,
            help="Xabar matni (ko'rsatilmasa standart matn ishlatiladi)",
        )
        parser.add_argument(
            '--telegram-id', type=int, default=None, dest='sinov_tg_id',
            help="SINOV: faqat shu telegram_id'ga yuboradi",
        )

    def _nomzodlar(self):
        from apps.users.models import CustomUser
        return (
            CustomUser.objects
            .filter(
                role=CustomUser.Role.USER,
                is_active=True,
                telegram_id__isnull=False,
            )
            .values_list('id', 'telegram_id', 'full_name')
            .order_by('id')
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        parallel = min(options['parallel'], 25)  # max 25, Telegram limit
        matn = options['matn'] or DEFAULT_MATN
        sinov_tg_id = options['sinov_tg_id']

        rasm_bor = Path(RASM_YOL).is_file()
        tugma = _ilova_tugmasi()

        # ---- SINOV REJIMI ----
        if sinov_tg_id:
            self.stdout.write(self.style.WARNING(
                f"⚙ SINOV REJIMI: faqat telegram_id={sinov_tg_id} ga yuboriladi"
            ))
            self.stdout.write(
                f"Rasm: {'✅ ' + str(RASM_YOL) if rasm_bor else '❌ topilmadi — faqat matn'}"
            )
            _, natija = _bitta_yuborish(sinov_tg_id, matn, rasm_bor, tugma)
            if natija:
                self.stdout.write(self.style.SUCCESS(f"✅ Yuborildi: tg_id={sinov_tg_id}"))
            else:
                self.stdout.write(self.style.ERROR(
                    f"❌ Yuborilmadi: tg_id={sinov_tg_id} (bot bloklangan yoki token xato?)"
                ))
            return

        # ---- ASOSIY YUBORISH ----
        nomzodlar = list(self._nomzodlar())
        jami = len(nomzodlar)

        if limit:
            nomzodlar = nomzodlar[:limit]
            self.stdout.write(self.style.WARNING(
                f"DIQQAT: faqat birinchi {limit} taga yuboriladi"
            ))

        ko_rsatiladigan = len(nomzodlar)
        taxminiy_vaqt = (ko_rsatiladigan / parallel) * BATCH_PAUZA

        self.stdout.write(self.style.WARNING(
            f"Mos userlar    : {jami} ta\n"
            f"Yuboriladigan  : {ko_rsatiladigan} ta\n"
            f"Parallel       : {parallel} ta\n"
            f"Rasm           : {'✅ ' + str(RASM_YOL) if rasm_bor else '❌ topilmadi — faqat matn'}\n"
            f"Taxminiy vaqt  : ~{taxminiy_vaqt:.0f} sek ({taxminiy_vaqt/60:.1f} daq)"
        ))

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n=== DRY RUN — hech narsa yuborilmadi ==="))
            for user_id, tg_id, full_name in nomzodlar:
                self.stdout.write(
                    f"  → {(full_name or '-'):30s}  tg={tg_id}"
                )
            self.stdout.write(self.style.SUCCESS(f"\nJami: {ko_rsatiladigan} ta"))
            return

        # ---- PARALLEL YUBORISH ----
        yuborildi = 0
        xato = 0
        boshlanish = time.time()

        # Batchlarga bo'lib yuborish
        # Har batch = parallel ta, keyin 1 sek kutish (flood limit himoya)
        for i in range(0, ko_rsatiladigan, parallel):
            batch = nomzodlar[i: i + parallel]
            batch_num = i // parallel + 1
            batch_jami = (ko_rsatiladigan + parallel - 1) // parallel

            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                futures = {
                    executor.submit(_bitta_yuborish, tg_id, matn, rasm_bor, tugma): (user_id, full_name)
                    for user_id, tg_id, full_name in batch
                }

                for future in as_completed(futures):
                    user_id, full_name = futures[future]
                    tg_id_res, muvaffaq = future.result()

                    if muvaffaq:
                        yuborildi += 1
                        logger.info("[BozorUser] Yuborildi: user_id=%s tg_id=%s",
                                    user_id, tg_id_res)
                    else:
                        xato += 1
                        logger.warning("[BozorUser] Yuborilmadi: user_id=%s tg_id=%s",
                                       user_id, tg_id_res)

            # Har batch hisoboti
            o_tgan = time.time() - boshlanish
            qolgan = ko_rsatiladigan - (i + len(batch))
            self.stdout.write(
                f"  Batch {batch_num}/{batch_jami} — "
                f"✅ {yuborildi}  ❌ {xato}  |  "
                f"Qoldi: {qolgan} ta  |  "
                f"Vaqt: {o_tgan:.0f}s"
            )

            # Flood limit himoyasi: oxirgi batch emas bo'lsa kutish
            if i + parallel < ko_rsatiladigan:
                time.sleep(BATCH_PAUZA)

        jami_vaqt = time.time() - boshlanish
        self.stdout.write(self.style.SUCCESS(
            f"\n=== Tugadi ===\n"
            f"✅ Yuborildi  : {yuborildi} ta\n"
            f"❌ Xato       : {xato} ta\n"
            f"📊 Jami       : {yuborildi + xato} ta\n"
            f"⏱ Ketgan vaqt: {jami_vaqt:.1f} sek ({jami_vaqt/60:.1f} daq)"
        ))
