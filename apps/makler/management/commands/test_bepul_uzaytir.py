"""
Management command — TEST rieltorlariga bepul sinov muddatini qo'lda uzaytirish.

Loyihani test qilayotgan rieltorlar uchun mo'ljallangan. Ular aniq
`telegram_id` yoki `telefon` bo'yicha ko'rsatiladi va ularga bepul sinov
muddati (default 30 kun) qo'shib beriladi.

`promo_qoshimcha_bepul` command'idan farqi:
  - Bir martalik aksiya EMAS — istalgancha marta qayta ishga tushirish mumkin.
  - `qoshimcha_bepul_muddat_berildi` bayrog'iga TEGMAYDI (ommaviy aksiyaga xalal
    bermaydi).
  - Faqat siz ko'rsatgan rieltorlar bilan ishlaydi, boshqasiga tegmaydi.

Muddat hisoblash mantig'i:
  - Agar rieltorning bepul muddati hali tugamagan bo'lsa — mavjud tugash
    sanasiga qo'shiladi (muddat yo'qolmaydi).
  - Agar tugagan yoki umuman bo'lmasa — hozirgi vaqtdan boshlab hisoblanadi.

Ishlatish:
    # Ko'rish (hech narsa o'zgartirmaydi)
    python manage.py test_bepul_uzaytir --telegram-id 123456789 --telegram-id 987654321 --dry-run

    # 30 kun qo'shish (default)
    python manage.py test_bepul_uzaytir --telegram-id 123456789 --telegram-id 987654321

    # Telefon raqami bo'yicha, 60 kun
    python manage.py test_bepul_uzaytir --telefon 901234567 --telefon 935556677 --kun 60
"""
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.makler.models import MaklerProfil

logger = logging.getLogger('test_bepul_uzaytir')


class Command(BaseCommand):
    help = (
        "Test rieltorlariga (telegram_id yoki telefon bo'yicha) bepul sinov "
        "muddatini qo'lda uzaytiradi. Istalgancha marta ishlatish mumkin."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--telegram-id', action='append', type=int, default=[],
            dest='telegram_ids',
            help="Rieltorning telegram_id'si. Bir nechta marta yozish mumkin.",
        )
        parser.add_argument(
            '--telefon', action='append', type=str, default=[],
            dest='telefonlar',
            help="Rieltorning telefon raqami. Bir nechta marta yozish mumkin.",
        )
        parser.add_argument(
            '--kun', type=int, default=30,
            help="Necha kun bepul muddat qo'shish (default: 30)",
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Hech narsa o'zgartirmaydi, faqat nima bo'lishini ko'rsatadi",
        )

    def _rieltorlarni_topish(self, telegram_ids, telefonlar):
        """Ko'rsatilgan identifikatorlar bo'yicha rieltor profillarini topadi."""
        topilgan = []
        topilmagan = []

        for tg_id in telegram_ids:
            r = (
                MaklerProfil.objects
                .filter(user__telegram_id=tg_id)
                .select_related('user')
                .first()
            )
            if r:
                topilgan.append(r)
            else:
                topilmagan.append(f"telegram_id={tg_id}")

        for tel in telefonlar:
            r = (
                MaklerProfil.objects
                .filter(user__phone=tel)
                .select_related('user')
                .first()
            )
            if r:
                topilgan.append(r)
            else:
                topilmagan.append(f"telefon={tel}")

        return topilgan, topilmagan

    def handle(self, *args, **options):
        telegram_ids = options['telegram_ids']
        telefonlar = options['telefonlar']
        kun = options['kun']
        dry_run = options['dry_run']

        if not telegram_ids and not telefonlar:
            raise CommandError(
                "Kamida bitta --telegram-id yoki --telefon ko'rsating.\n"
                "Masalan: python manage.py test_bepul_uzaytir "
                "--telegram-id 123456789 --telegram-id 987654321"
            )

        now = timezone.now()
        topilgan, topilmagan = self._rieltorlarni_topish(telegram_ids, telefonlar)

        if topilmagan:
            self.stdout.write(self.style.ERROR(
                f"Topilmadi: {', '.join(topilmagan)}"
            ))

        if not topilgan:
            raise CommandError("Hech qanday rieltor topilmadi. To'xtatildi.")

        self.stdout.write(self.style.WARNING(
            f"Topilgan rieltorlar: {len(topilgan)} ta | Qo'shiladigan muddat: {kun} kun"
        ))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                "\n=== DRY RUN — hech narsa o'zgartirilmadi ==="
            ))

        muvaffaqiyatli = 0
        for rieltor in topilgan:
            # Boshlang'ich nuqta: agar muddat hali amal qilsa — ustiga qo'shamiz,
            # aks holda hozirdan boshlaymiz.
            mavjud = rieltor.bepul_muddat_tugash
            boshlanish = mavjud if (mavjud and mavjud > now) else now
            yangi_tugash = boshlanish + timedelta(days=kun)

            tg = getattr(rieltor.user, 'phone', None) or getattr(
                rieltor.user, 'telegram_id', None
            )
            eski_str = mavjud.strftime('%d.%m.%Y %H:%M') if mavjud else '-'
            yangi_str = yangi_tugash.strftime('%d.%m.%Y %H:%M')

            self.stdout.write(
                f"  - {rieltor.user.full_name or tg} "
                f"(id={rieltor.id}): {eski_str}  →  {yangi_str}"
            )

            if dry_run:
                continue

            try:
                with transaction.atomic():
                    rieltor.bepul_muddat_tugash = yangi_tugash
                    rieltor.save(update_fields=[
                        'bepul_muddat_tugash', 'updated_at',
                    ])
                muvaffaqiyatli += 1
                logger.info(
                    "[TestBepulUzaytir] rieltor_id=%s kun=%s yangi_tugash=%s",
                    rieltor.id, kun, yangi_tugash.isoformat(),
                )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f"    XATO: rieltor_id={rieltor.id} — {exc}"
                ))
                logger.error(
                    "[TestBepulUzaytir] Xato: rieltor_id=%s err=%s",
                    rieltor.id, exc, exc_info=True,
                )

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"\n=== Tugadi === Muddat uzaytirildi: {muvaffaqiyatli} ta"
            ))
