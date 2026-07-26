"""
Bepul sinov muddati tugaganlarga obuna PROMO (aksiya) xabarini QO'LDA yuborish.

Bu — har kuni soat 10:00 da ishlaydigan `obuna_tugash_xabarnomasi` task'ining
PROMO qismini qo'lda (Celery/Redis'siz, to'g'ridan-to'g'ri) bajaradi.

Xuddi avtomatik task kabi:
  1. Bepul sinov muddati tugagan (bepul_muddat_tugash < now)
  2. Hech qachon pul to'lamagan (muvaffaqiyatli Tolov yo'q)
  3. Ayni paytda faol obunasi yo'q
  4. Promo xabar HALI YUBORILMAGAN (promo_xabar_yuborildi=False)
bo'lgan rieltorlarga rasm + matn yuboradi va flagni belgilaydi.

Flag umumiy bo'lgani uchun bu yerda xabar olganlar ertaga 10:00 dagi
avtomatik task'da QAYTA xabar OLMAYDI.

Foydalanish:
    # Haqiqiy yuborish:
    python manage.py promo_yubor

    # Faqat ko'rish (kimga boradi — hech narsa yubormaydi, flag tegmaydi):
    python manage.py promo_yubor --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.makler.models import MaklerProfil
from apps.obuna.models import Tolov
from apps.obuna.notifications import bepul_muddat_tugadi_xabar


class Command(BaseCommand):
    help = "Bepul muddati tugaganlarga obuna promo (aksiya) xabarini qo'lda yuboradi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Faqat kimga borishini ko'rsatadi, xabar yubormaydi va flagni o'zgartirmaydi",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        # Muvaffaqiyatli to'lov qilganlar (ularga yubormaymiz)
        tolagan_rieltor_idlari = (
            Tolov.objects
            .filter(holat=Tolov.Holat.MUVAFFAQIYATLI)
            .values_list('obuna__rieltor_id', flat=True)
            .distinct()
        )

        nomzodlar = (
            MaklerProfil.objects
            .filter(
                bepul_muddat_tugash__lte=now,
                bepul_muddat_tugash__isnull=False,
                promo_xabar_yuborildi=False,       # oldin xabar bormaganlar
            )
            .exclude(id__in=tolagan_rieltor_idlari)
            .select_related('user')
        )

        jami = nomzodlar.count()
        if jami == 0:
            self.stdout.write(self.style.WARNING(
                "Xabar yuboriladigan rieltor topilmadi (hammasiga borgan yoki shart bajarilmaydi)."
            ))
            return

        self.stdout.write(f"Nomzodlar soni (dastlabki): {jami}")
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN: hech narsa yuborilmaydi ---"))

        yuborilgan = 0
        otkazib = 0

        for rieltor in nomzodlar:
            # Faol obunasi bo'lsa o'tkazib yuboramiz (qo'shimcha xavfsizlik)
            if rieltor.obuna_faol:
                otkazib += 1
                continue

            tg_id = getattr(rieltor.user, 'telegram_id', None)
            ism = getattr(rieltor.user, 'full_name', None) or rieltor.user

            if dry_run:
                self.stdout.write(f"  → [DRY] {ism} (telegram_id={tg_id})")
                yuborilgan += 1
                continue

            try:
                if bepul_muddat_tugadi_xabar(rieltor):
                    rieltor.promo_xabar_yuborildi = True
                    rieltor.promo_xabar_vaqti = timezone.now()
                    rieltor.save(update_fields=[
                        'promo_xabar_yuborildi', 'promo_xabar_vaqti', 'updated_at'
                    ])
                    yuborilgan += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ Yuborildi: {ism} (telegram_id={tg_id})"
                    ))
                else:
                    otkazib += 1
                    self.stdout.write(self.style.WARNING(
                        f"  ✗ Yuborilmadi (tg yo'q yoki bloklangan): {ism}"
                    ))
            except Exception as exc:
                otkazib += 1
                self.stdout.write(self.style.ERROR(
                    f"  ! Xato: {ism} — {exc}"
                ))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"\nDRY RUN yakuni: {yuborilgan} ta rieltorga xabar borishi mumkin edi."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nYakun: {yuborilgan} ta yuborildi, {otkazib} ta o'tkazib yuborildi."
            ))
