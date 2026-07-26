"""
Management command — bepul obunasi hali tugamagan va hech qachon
to'liq obuna sotib olmagan rieltorlarga Telegram orqali aksiya xabari
(rasm + matn) yuboradi.

KIMGA YUBORILADI:
  ✅ bepul muddati hali tugamagan  (bepul_muddat_tugash > hozir)
  ✅ hech qachon muvaffaqiyatli to'lov qilmagan  (to'liq obuna yo'q)
  ❌ Admin bloklagan rieltorlar o'tkazib yuboriladi
  ❌ Faol (to'langan) obunasi bor rieltorlar o'tkazib yuboriladi

XABAR MATNI va RASMI:
  Rasmni shu yo'lga joylashtiring:
    assets/promo/aksiya_promo.jpg   (yoki .png)
  Rasm bo'lmasa — faqat matnli xabar yuboriladi.

ISHLATISH (VPS'da):
    # Avval ko'rish — hech narsa yubormasdan
    python manage.py promo_xabar_yuborish --dry-run

    # Faqat birinchi 3 tasiga sinab ko'rish
    python manage.py promo_xabar_yuborish --limit 3

    # Hammaga yuborish
    python manage.py promo_xabar_yuborish

    # Matn o'zgartirish kerak bo'lsa
    python manage.py promo_xabar_yuborish --matn "Maxsus taklif..."

    # Pauza (flood-limit himoyasi) o'zgartirish, default 0.3 sek
    python manage.py promo_xabar_yuborish --pauza 0.5
"""
import time
import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.makler.models import MaklerProfil
from apps.obuna.models import Obuna, Tolov
from apps.users.otp_service import telegram_xabar_yuborish, telegram_rasm_yuborish

logger = logging.getLogger('promo_xabar_yuborish')

# Rasm yo'li — shu faylni VPS'da joylashtirasiz
RASM_YOL = settings.BASE_DIR / 'assets' / 'promo' / 'aksiya_promo.jpg'

# Obunalar sahifasiga yo'naltiruvchi inline tugma
def _obunalar_tugmasi():
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
        final_url = f"{base_url}{sep}startapp=obuna"

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


DEFAULT_MATN = (
    "🏠 <b>Hurmatli HUSMA Estate rieltorlari!</b>\n\n"
    "Sizlar uchun maxsus aksiyani e'lon qilamiz! 🎉\n\n"
    "Endi birinchi oylik obuna narxi 99 000 so'm emas!\n\n"
    "🔥 <b>50% chegirma - faqat 3 kun!</b>\n\n"
    "❌ <s>99 000 so'm</s>\n"
    "✅ <b>49 500 so'm</b>\n\n"
    "HUSMA Estate orqali siz:\n"
    "✅ Tayyor mijozlardan lidlar olasiz.\n"
    "✅ Har kuni yangi buyurtmalarga ega bo'lasiz.\n"
    "✅ Mijoz qidirishga ketadigan vaqt va reklama xarajatlarini kamaytirasiz.\n\n"
    "⏳ <b>Aksiya cheklangan muddat davom etadi.</b>\n\n"
    "Botga kirib obunangizni faollashtiring va mijozlarni qabul qilishni boshlang!\n\n"
    "<b>HUSMA Estate</b> — mijoz va rieltorni birlashtiruvchi platforma."
)


class Command(BaseCommand):
    help = (
        "Bepul obunasi hali tugamagan va hech qachon to'liq obuna "
        "sotib olmagan rieltorlarga aksiya xabari yuboradi. "
        "Bir martalik ishlatish uchun mo'ljallangan."
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
            help="Har xabar orasidagi pauza soniyada (default: 0.3, flood-limit himoyasi)",
        )
        parser.add_argument(
            '--matn', type=str, default=None,
            help="Xabar matni (ko'rsatilmasa standart matn ishlatiladi)",
        )
        parser.add_argument(
            '--telegram-id', type=int, default=None, dest='sinov_tg_id',
            help=(
                "SINOV: faqat shu telegram_id'ga yuboradi. "
                "Rieltor profil shartlari tekshirilmaydi. "
                "Masalan: --telegram-id 123456789"
            ),
        )

    def _nomzodlar(self, now):
        """
        Kimga yuboramiz:
        1. Bepul muddati hali tugamagan
        2. Hech qachon muvaffaqiyatli to'lov qilmagan (TUGAGAN holati ham hisoblanadi)
        3. Admin bloklagan emas
        """
        # Kamida bitta muvaffaqiyatli to'lov qilgan rieltor IDlari
        tolagan_ids = (
            Tolov.objects
            .filter(holat=Tolov.Holat.MUVAFFAQIYATLI)
            .values_list('obuna__rieltor_id', flat=True)
            .distinct()
        )

        return (
            MaklerProfil.objects
            .filter(
                bepul_muddat_tugash__gt=now,        # hali tugamagan
                bepul_muddat_tugash__isnull=False,
            )
            .exclude(verify_holat=MaklerProfil.VerifyHolat.REJECTED)  # bloklanmagan
            .exclude(id__in=list(tolagan_ids))       # to'lov qilmaganlar
            .select_related('user')
            .order_by('id')
        )

    def handle(self, *args, **options):
        from django.utils import timezone
        dry_run = options['dry_run']
        limit = options['limit']
        pauza = options['pauza']
        matn = options['matn'] or DEFAULT_MATN
        sinov_tg_id = options['sinov_tg_id']

        now = timezone.now()

        # ---- SINOV REJIMI: faqat bitta telegram_id'ga yuborish ----
        if sinov_tg_id:
            self.stdout.write(self.style.WARNING(
                f"SINOV REJIMI: faqat telegram_id={sinov_tg_id} ga yuboriladi"
            ))
            rasm_bor = Path(RASM_YOL).is_file()
            tugma = _obunalar_tugmasi()
            self.stdout.write(
                f"Rasm: {'✅ ' + str(RASM_YOL) if rasm_bor else '❌ topilmadi — faqat matn'}"
            )
            if rasm_bor:
                natija = telegram_rasm_yuborish(
                    sinov_tg_id, str(RASM_YOL),
                    caption=matn[:1024],
                    reply_markup=tugma,
                )
                if not natija:
                    natija = telegram_xabar_yuborish(sinov_tg_id, matn, reply_markup=tugma)
            else:
                natija = telegram_xabar_yuborish(sinov_tg_id, matn, reply_markup=tugma)

            if natija:
                self.stdout.write(self.style.SUCCESS(f"✅ Yuborildi: tg_id={sinov_tg_id}"))
            else:
                self.stdout.write(self.style.ERROR(
                    f"❌ Yuborilmadi: tg_id={sinov_tg_id}  "
                    f"(bot bloklangan yoki noto'g'ri token?)"
                ))
            return
        nomzodlar = self._nomzodlar(now)
        jami = nomzodlar.count()

        rasm_bor = Path(RASM_YOL).is_file()
        tugma = _obunalar_tugmasi()

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
            self.stdout.write(self.style.SUCCESS(
                "\n=== DRY RUN — hech narsa yuborilmadi ==="
            ))
            for r in nomzodlar:
                tugash = (
                    r.bepul_muddat_tugash.strftime('%d.%m.%Y')
                    if r.bepul_muddat_tugash else '-'
                )
                self.stdout.write(
                    f"  → {r.user.full_name or '-':30s}  "
                    f"tg={r.user.telegram_id}  "
                    f"bepul_tugash={tugash}"
                )
            self.stdout.write(self.style.SUCCESS(
                f"\nJami: {min(jami, limit) if limit else jami} ta"
            ))
            return

        # ---- HAQIQIY YUBORISH ----
        yuborildi = 0
        xato = 0

        for rieltor in nomzodlar:
            tg_id = getattr(rieltor.user, 'telegram_id', None)
            if not tg_id:
                self.stdout.write(f"  ⚠ tg_id yo'q: rieltor_id={rieltor.id}")
                continue

            try:
                if rasm_bor:
                    # Rasm + caption + tugma (caption 1024 belgi limit bor)
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

                if natija:
                    yuborildi += 1
                    logger.info(
                        "[PromoXabar] Yuborildi: rieltor_id=%s tg_id=%s",
                        rieltor.id, tg_id,
                    )
                    self.stdout.write(f"  ✅ {rieltor.user.full_name or tg_id}")
                else:
                    xato += 1
                    logger.warning(
                        "[PromoXabar] Yuborilmadi (API xatosi): rieltor_id=%s tg_id=%s",
                        rieltor.id, tg_id,
                    )
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ {rieltor.user.full_name or tg_id} — API xatosi")
                    )

            except Exception as exc:
                xato += 1
                logger.error(
                    "[PromoXabar] Xato: rieltor_id=%s err=%s",
                    rieltor.id, exc, exc_info=True,
                )
                self.stdout.write(
                    self.style.ERROR(f"  ❌ rieltor_id={rieltor.id} — {exc}")
                )

            if pauza > 0:
                time.sleep(pauza)

        # ---- HISOBOT ----
        self.stdout.write(self.style.SUCCESS(
            f"\n=== Tugadi ===\n"
            f"✅ Yuborildi : {yuborildi} ta\n"
            f"❌ Xato      : {xato} ta\n"
            f"📊 Jami      : {yuborildi + xato} ta"
        ))
