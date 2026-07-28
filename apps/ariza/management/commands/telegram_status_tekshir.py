"""
Management command — Telegram bloklangan maklerlar monitoringi.

Barcha telegram_bloklangan=True maklerlar sonini va oxirgi 7 kunda
bloklangan yangi maklerlar sonini konsolga chiqaradi.

ISHLATISH:
    python manage.py telegram_status_tekshir

    # Bloklangan maklerlar ro'yxatini to'liq ko'rish
    python manage.py telegram_status_tekshir --verbose

    # Oxirgi N kunda bloklanganlarni ko'rsatish (default: 7)
    python manage.py telegram_status_tekshir --kunlar 14
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "Telegram bloklangan maklerlar sonini va oxirgi N kunda "
        "bloklangan yangi maklerlar ro'yxatini chiqaradi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose', action='store_true',
            help="Bloklangan maklerlar to'liq ro'yxatini ko'rsatish",
        )
        parser.add_argument(
            '--kunlar', type=int, default=7,
            help="Oxirgi N kun ichida bloklanganlarni ko'rsatish (default: 7)",
        )

    def handle(self, *args, **options):
        from apps.makler.models import MaklerProfil

        verbose = options['verbose']
        kunlar = options['kunlar']
        now = timezone.now()
        chegara = now - timedelta(days=kunlar)

        # Jami bloklangan
        jami_bloklangan = MaklerProfil.objects.filter(
            telegram_bloklangan=True
        )
        jami_son = jami_bloklangan.count()

        # Oxirgi N kunda bloklangan
        yangi_bloklangan = MaklerProfil.objects.filter(
            telegram_bloklangan=True,
            telegram_bloklangan_vaqt__gte=chegara,
        )
        yangi_son = yangi_bloklangan.count()

        # Jami maklerlar soni
        jami_makler = MaklerProfil.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f"\n{'=' * 50}\n"
            f"  TELEGRAM BLOKLANGAN MAKLERLAR MONITORINGI\n"
            f"{'=' * 50}"
        ))
        self.stdout.write(
            f"  Jami maklerlar          : {jami_makler} ta\n"
            f"  Telegram bloklangan     : {jami_son} ta\n"
            f"  Oxirgi {kunlar} kunda bloklangan: {yangi_son} ta\n"
        )

        if jami_son > 0:
            bloklangan_foiz = round(jami_son / jami_makler * 100, 1) if jami_makler else 0
            self.stdout.write(
                f"  Bloklangan ulushi       : {bloklangan_foiz}%\n"
            )

        self.stdout.write(f"{'=' * 50}\n")

        if verbose and jami_son > 0:
            self.stdout.write(self.style.WARNING(
                "\nBloklangan maklerlar ro'yxati:\n"
            ))
            for profil in jami_bloklangan.select_related('user').order_by(
                '-telegram_bloklangan_vaqt'
            ):
                bloklangan_vaqt = (
                    profil.telegram_bloklangan_vaqt.strftime('%d.%m.%Y %H:%M')
                    if profil.telegram_bloklangan_vaqt else 'noma\'lum'
                )
                full_name = profil.user.full_name or '—'
                telegram_id = profil.user.telegram_id or '—'
                self.stdout.write(
                    f"  profil_id={profil.id:<6}  "
                    f"tg_id={telegram_id:<15}  "
                    f"ism={full_name:<25}  "
                    f"bloklangan={bloklangan_vaqt}"
                )
            self.stdout.write('')

        elif verbose and jami_son == 0:
            self.stdout.write(self.style.SUCCESS(
                "  Bloklangan makler yo'q.\n"
            ))
