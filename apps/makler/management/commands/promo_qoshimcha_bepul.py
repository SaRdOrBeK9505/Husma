"""
Management command — bepul sinov muddati tugagan rieltorlarga
qo'shimcha (default 14) kunlik BEPUL sinov muddati aksiyasini berish.

Xavfsizlik tamoyillari:
  - Idempotent: `qoshimcha_bepul_muddat_berildi` bayrog'i orqali bir rieltorga
    aksiya faqat bir marta beriladi. Skript ikki marta ishga tushsa ham
    ikki marta muddat qo'shilmaydi.
  - Dry-run: `--dry-run` bilan hech narsa o'zgartirmasdan kimlarga tegishini
    ko'rsatadi.
  - Bosqichma-bosqich: `--limit=N` bilan avval kichik guruhda sinash mumkin.
  - Xatolarni yutmaydi: bitta rieltorda xato bo'lsa, jarayon to'xtamaydi —
    xato ro'yxatga yoziladi va oxirida hisobot beriladi.
  - Telegram flood-limitidan himoya: har yuborish orasida kichik pauza.

Ishlatish (VPS'da tartib bilan):
    python manage.py promo_qoshimcha_bepul --dry-run
    python manage.py promo_qoshimcha_bepul --limit=3
    python manage.py promo_qoshimcha_bepul
"""
import time
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.makler.models import MaklerProfil
from apps.obuna.models import Obuna

logger = logging.getLogger('promo_qoshimcha_bepul')


class Command(BaseCommand):
    help = (
        "Bepul muddati tugagan rieltorlarga qo'shimcha bepul sinov muddati "
        "(default 14 kun) beradi va Telegram orqali tabrik yuboradi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Hech narsa o'zgartirmaydi, faqat kimlarga tegishini ko'rsatadi",
        )
        parser.add_argument(
            '--limit', type=int, default=None,
            help="Faqat birinchi N ta rieltor bilan ishlash (sinov uchun)",
        )
        parser.add_argument(
            '--kun', type=int, default=14,
            help="Necha kun qo'shimcha bepul muddat berish (default: 14)",
        )
        parser.add_argument(
            '--xabar-yubormaslik', action='store_true',
            help="Muddatni uzaytiradi, lekin Telegram tabrik yubormaydi",
        )
        parser.add_argument(
            '--pauza', type=float, default=0.1,
            help="Har xabar orasidagi pauza soniyada (flood-limit himoyasi)",
        )
        parser.add_argument(
            '--telegram-id', type=int, default=None,
            help=(
                "Faqat shu telegram_id egasiga ishlash (sinov uchun). "
                "Bu holatda 'muddati tugagan' va 'aksiya berilmagan' shartlari "
                "tekshirilmaydi — o'zingizda sinash uchun qulay."
            ),
        )

    def _nomzodlar(self, now, telegram_id=None):
        """
        Aksiyaga mos rieltorlar:
          1. Bepul muddati allaqachon tugagan (bepul_muddat_tugash < now)
          2. Hali bu aksiya berilmagan (qoshimcha_bepul_muddat_berildi=False)
          3. Admin bloklamagan (verify_holat != rejected)
          4. Hozir faol (to'langan) obunasi yo'q

        Agar telegram_id berilsa — faqat shu bitta rieltor qaytariladi va
        yuqoridagi shartlar TEKSHIRILMAYDI (sinov uchun).
        """
        if telegram_id is not None:
            return (
                MaklerProfil.objects
                .filter(user__telegram_id=telegram_id)
                .select_related('user')
                .order_by('id')
            )

        faol_obuna_rieltor_idlari = Obuna.objects.filter(
            holat=Obuna.Holat.FAOL,
            tugash_vaqti__gt=now,
        ).values_list('rieltor_id', flat=True)

        return (
            MaklerProfil.objects
            .filter(
                bepul_muddat_tugash__lt=now,
                bepul_muddat_tugash__isnull=False,
                qoshimcha_bepul_muddat_berildi=False,
            )
            .exclude(verify_holat=MaklerProfil.VerifyHolat.REJECTED)
            .exclude(id__in=list(faol_obuna_rieltor_idlari))
            .select_related('user')
            .order_by('id')
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        kun = options['kun']
        xabar_yubormaslik = options['xabar_yubormaslik']
        pauza = options['pauza']
        telegram_id = options['telegram_id']
        now = timezone.now()

        nomzodlar = self._nomzodlar(now, telegram_id=telegram_id)
        jami = nomzodlar.count()

        if telegram_id is not None:
            self.stdout.write(self.style.WARNING(
                f"SINOV REJIMI: faqat telegram_id={telegram_id} bilan ishlanadi "
                f"(muddat/aksiya shartlari tekshirilmaydi)"
            ))
        self.stdout.write(self.style.WARNING(
            f"Aksiyaga mos rieltorlar: {jami} ta"
        ))
        self.stdout.write(f"Beriladigan muddat: {kun} kun")

        if limit:
            nomzodlar = nomzodlar[:limit]
            self.stdout.write(self.style.WARNING(
                f"DIQQAT: faqat birinchi {limit} ta bilan ishlanadi"
            ))

        # ---- DRY RUN ----
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                "\n=== DRY RUN — hech narsa o'zgartirilmadi ==="
            ))
            for r in nomzodlar:
                tg = getattr(r.user, 'telegram_id', None)
                eski_tugash = (
                    r.bepul_muddat_tugash.strftime('%d.%m.%Y')
                    if r.bepul_muddat_tugash else '-'
                )
                self.stdout.write(
                    f"  - rieltor_id={r.id}, telegram_id={tg}, "
                    f"eski_tugash={eski_tugash}"
                )
            self.stdout.write(self.style.SUCCESS(
                f"\nJami tegishli: {min(jami, limit) if limit else jami} ta"
            ))
            return

        # ---- HAQIQIY ISHLASH ----
        muvaffaqiyatli = 0
        xabar_yuborildi = 0
        xato_royxati = []

        for rieltor in nomzodlar:
            try:
                # DB o'zgarishi atomik — muddat uzaytirish va bayroq birga saqlanadi
                with transaction.atomic():
                    rieltor.bepul_muddat_tugash = now + timedelta(days=kun)
                    rieltor.qoshimcha_bepul_muddat_berildi = True
                    rieltor.qoshimcha_bepul_muddat_vaqti = now
                    rieltor.save(update_fields=[
                        'bepul_muddat_tugash',
                        'qoshimcha_bepul_muddat_berildi',
                        'qoshimcha_bepul_muddat_vaqti',
                        'updated_at',
                    ])
                muvaffaqiyatli += 1
                logger.info(
                    "[Promo] Qo'shimcha muddat berildi: rieltor_id=%s kun=%s",
                    rieltor.id, kun
                )

                # Telegram tabrik — DB tranzaksiyasidan TASHQARIDA.
                # Telegram xato bersa ham DB o'zgarishi saqlanib qoladi.
                if not xabar_yubormaslik:
                    try:
                        from apps.obuna.notifications import (
                            qoshimcha_bepul_muddat_tabrik_xabar,
                        )
                        if qoshimcha_bepul_muddat_tabrik_xabar(rieltor, kun):
                            xabar_yuborildi += 1
                    except Exception as notif_exc:
                        logger.warning(
                            "[Promo] Tabrik yuborishda xato: rieltor_id=%s err=%s",
                            rieltor.id, notif_exc
                        )

            except Exception as exc:
                xato_royxati.append((rieltor.id, str(exc)))
                logger.error(
                    "[Promo] Xato: rieltor_id=%s err=%s",
                    rieltor.id, exc, exc_info=True
                )

            # Telegram flood-limitidan himoya
            if pauza > 0:
                time.sleep(pauza)

        # ---- HISOBOT ----
        self.stdout.write(self.style.SUCCESS(
            f"\n=== Tugadi ===\n"
            f"Muddat uzaytirildi: {muvaffaqiyatli} ta\n"
            f"Tabrik yuborildi:   {xabar_yuborildi} ta"
        ))
        if xato_royxati:
            self.stdout.write(self.style.ERROR(
                f"\nXatolar: {len(xato_royxati)} ta"
            ))
            for rid, err in xato_royxati:
                self.stdout.write(f"  - rieltor_id={rid}: {err}")
