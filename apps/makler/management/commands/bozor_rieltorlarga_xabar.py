"""
Management command — barcha aktiv rieltorlarga Uy bozori haqida
bir martalik Telegram xabari (rasm + matn + tugma) yuboradi.

RASM:
  assets/promo/bozor_rieltor_promo.jpg  (yoki .png)
  Shu faylni avval assets/promo/ papkasiga qo'ying.

KIMGA YUBORILADI:
  ✅ role='makler' bo'lgan hamma foydalanuvchilar
  ✅ telegram_id mavjud bo'lganlari
  ❌ Admin bloklangan (REJECTED) rieltorlar o'tkazib yuboriladi

ISHLATISH:
    # Ko'rish — hech narsa yubormaydi
    python manage.py bozor_rieltorlarga_xabar --dry-run

    # Sinov uchun o'zingizga
    python manage.py bozor_rieltorlarga_xabar --telegram-id 123456789

    # Faqat dastlabki N tasiga
    python manage.py bozor_rieltorlarga_xabar --limit 5

    # Hammaga
    python manage.py bozor_rieltorlarga_xabar
"""
import time
import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.users.otp_service import telegram_xabar_yuborish, telegram_rasm_yuborish

logger = logging.getLogger('bozor_rieltorlarga_xabar')

RASM_YOL = settings.BASE_DIR / 'assets' / 'promo' / 'bozor_rieltor_promo.jpg'

DEFAULT_MATN = (
    "🏠 <b>HUSMA ESTATE'DA UY BOZORI ISHGA TUSHDI!</b> 🎉\n\n"
    "Hurmatli rieltor!\n\n"
    "Siz kutgan yangi imkoniyat endi <b>Husma Estate</b> platformasida mavjud.\n\n"
    "✅ Endi sotuv va ijara e'lonlaringizni platformaga joylashingiz mumkin.\n"
    "✅ E'lonlaringiz minglab foydalanuvchilarga ko'rsatiladi.\n"
    "✅ Barcha e'lonlarni bitta joydan boshqarishingiz mumkin.\n\n"
    "🔒 <b>Muhim:</b> Uy bozoriga e'lon joylash huquqi <b>faqat Husma "
    "Estate'dan ro'yxatdan o'tgan rieltorlar</b> uchun mavjud.\n\n"
    "📈 Ko'proq e'lon → Ko'proq mijoz → Ko'proq bitim!\n\n"
    "🚀 <b>Hoziroq \"Bozor\" bo'limiga kiring va birinchi e'loningizni joylang!</b>\n\n"
    "<b>Husma Estate</b> — Professional rieltorlar uchun zamonaviy platforma. ❤️"
)


def _ilova_tugmasi():
    """Ilovani ochish inline tugmasi."""
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
            [
                {
                    "text": "Ilovani ochish",
                    "web_app": {"url": final_url},
                }
            ]
        ]
    }


class Command(BaseCommand):
    help = (
        "Barcha rieltorlarga Uy bozori haqida bir martalik "
        "Telegram xabari (rasm + matn + tugma) yuboradi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Hech narsa yubormaydi, faqat kimga yuborilishini ko'rsatadi",
        )
        parser.add_argument(
            '--limit', type=int, default=None,
            help="Faqat birinchi N ta rieltorga yuborish (sinov uchun)",
        )
        parser.add_argument(
            '--pauza', type=float, default=0.3,
            help="Har xabar orasidagi pauza soniyada (default: 0.3)",
        )
        parser.add_argument(
            '--matn', type=str, default=None,
            help="Xabar matni (ko'rsatilmasa standart matn ishlatiladi)",
        )
        parser.add_argument(
            '--telegram-id', type=int, default=None, dest='sinov_tg_id',
            help=(
                "SINOV: faqat shu telegram_id'ga yuboradi. "
                "Masalan: --telegram-id 123456789"
            ),
        )

    def _nomzodlar(self):
        """Barcha aktiv rieltorlar (makler role + telegram_id mavjud)."""
        from apps.makler.models import MaklerProfil

        return (
            MaklerProfil.objects
            .exclude(verify_holat=MaklerProfil.VerifyHolat.REJECTED)
            .select_related('user')
            .filter(user__telegram_id__isnull=False)
            .order_by('id')
        )

    def _yuborish(self, tg_id: int, matn: str, rasm_bor: bool, tugma):
        """Bitta foydalanuvchiga xabar yuboradi."""
        if rasm_bor:
            natija = telegram_rasm_yuborish(
                tg_id, str(RASM_YOL),
                caption=matn[:1024],
                reply_markup=tugma,
            )
            if not natija:
                # Rasm kelmasa matnli fallback
                natija = telegram_xabar_yuborish(tg_id, matn, reply_markup=tugma)
        else:
            natija = telegram_xabar_yuborish(tg_id, matn, reply_markup=tugma)
        return natija

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        pauza = options['pauza']
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
            natija = self._yuborish(sinov_tg_id, matn, rasm_bor, tugma)
            if natija:
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Yuborildi: tg_id={sinov_tg_id}"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"❌ Yuborilmadi: tg_id={sinov_tg_id}  "
                    f"(bot bloklangan yoki noto'g'ri token?)"
                ))
            return

        # ---- ASOSIY YUBORISH ----
        nomzodlar = self._nomzodlar()
        jami = nomzodlar.count()

        self.stdout.write(self.style.WARNING(
            f"Mos rieltorlar: {jami} ta  |  "
            f"Rasm: {'✅ ' + str(RASM_YOL) if rasm_bor else '❌ topilmadi — faqat matn'}"
        ))

        if limit:
            nomzodlar = nomzodlar[:limit]
            self.stdout.write(self.style.WARNING(
                f"DIQQAT: faqat birinchi {limit} taga yuboriladi"
            ))

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n=== DRY RUN — hech narsa yuborilmadi ==="))
            for r in nomzodlar:
                self.stdout.write(
                    f"  → {r.user.full_name or '-':30s}  tg={r.user.telegram_id}"
                )
            self.stdout.write(self.style.SUCCESS(
                f"\nJami: {min(jami, limit) if limit else jami} ta"
            ))
            return

        yuborildi = 0
        xato = 0

        for rieltor in nomzodlar:
            tg_id = rieltor.user.telegram_id
            if not tg_id:
                continue

            try:
                natija = self._yuborish(tg_id, matn, rasm_bor, tugma)
                if natija:
                    yuborildi += 1
                    logger.info("[BozorRieltor] Yuborildi: rieltor_id=%s tg_id=%s",
                                rieltor.id, tg_id)
                    self.stdout.write(f"  ✅ {rieltor.user.full_name or tg_id}")
                else:
                    xato += 1
                    logger.warning("[BozorRieltor] Yuborilmadi: rieltor_id=%s tg_id=%s",
                                   rieltor.id, tg_id)
                    self.stdout.write(self.style.ERROR(
                        f"  ❌ {rieltor.user.full_name or tg_id} — API xatosi"
                    ))
            except Exception as exc:
                xato += 1
                logger.error("[BozorRieltor] Xato: rieltor_id=%s err=%s",
                             rieltor.id, exc, exc_info=True)
                self.stdout.write(self.style.ERROR(
                    f"  ❌ rieltor_id={rieltor.id} — {exc}"
                ))

            if pauza > 0:
                time.sleep(pauza)

        self.stdout.write(self.style.SUCCESS(
            f"\n=== Tugadi ===\n"
            f"✅ Yuborildi : {yuborildi} ta\n"
            f"❌ Xato      : {xato} ta\n"
            f"📊 Jami      : {yuborildi + xato} ta"
        ))
