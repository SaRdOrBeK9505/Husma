"""
Eski "kutilmoqda" obunalarni bir martalik tozalash uchun management command.

Foydalanish:
    python manage.py tozalash_obunalar
    
    # Haqiqatda o'chirish (--dry-run ishlatmasdan):
    python manage.py tozalash_obunalar --execute
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from apps.obuna.models import Obuna, Tolov


class Command(BaseCommand):
    help = '30 daqiqadan ortiq "kutilmoqda" holatidagi obunalarni bekor qiladi'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Haqiqatda o\'chirish (aks holda faqat ko\'rsatadi)',
        )
        parser.add_argument(
            '--minutes',
            type=int,
            default=30,
            help='Necha daqiqadan katta obunalarni tozalash (default: 30)',
        )

    def handle(self, *args, **options):
        execute = options['execute']
        minutes = options['minutes']
        
        now = timezone.now()
        timeout_vaqt = now - timedelta(minutes=minutes)
        
        # Eski kutilayotgan obunalarni topish
        eski_obunalar = Obuna.objects.filter(
            holat=Obuna.Holat.KUTILMOQDA,
            created_at__lt=timeout_vaqt,
        ).select_related('rieltor__user')
        
        jami = eski_obunalar.count()
        
        if jami == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {minutes} daqiqadan ortiq "kutilmoqda" obuna topilmadi'
                )
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'\n⚠ {jami} ta eski "kutilmoqda" obuna topildi:\n'
            )
        )
        
        # Batafsil ma'lumot ko'rsatish
        for obuna in eski_obunalar[:10]:  # Faqat birinchi 10 tasini ko'rsatish
            rieltor_info = (
                f"{obuna.rieltor.user.telegram_id}"
                if obuna.rieltor.user
                else "noma'lum"
            )
            qachon = (now - obuna.created_at).total_seconds() / 60
            self.stdout.write(
                f"  - Obuna #{obuna.id}: {obuna.tarif.nomi} | "
                f"Rieltor: {rieltor_info} | "
                f"Yaratilgan: {obuna.created_at.strftime('%Y-%m-%d %H:%M')} "
                f"({qachon:.0f} daqiqa oldin)"
            )
        
        if jami > 10:
            self.stdout.write(f"  ... va yana {jami - 10} ta\n")
        
        if not execute:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠ Dry-run rejimi: hech narsa o\'zgartirilmadi.\n'
                    'Haqiqatda tozalash uchun --execute flag bilan ishga tushiring:\n'
                    '  python manage.py tozalash_obunalar --execute\n'
                )
            )
            return
        
        # Haqiqatda o'chirish
        self.stdout.write('\n🔄 Tozalash boshlanmoqda...\n')
        
        with transaction.atomic():
            # Tolovlarni bekor qilish
            tolov_count = Tolov.objects.filter(
                obuna__in=eski_obunalar,
                holat=Tolov.Holat.KUTILMOQDA,
            ).update(holat=Tolov.Holat.BEKOR)
            
            # Obunalarni bekor qilish
            obuna_count = eski_obunalar.update(holat=Obuna.Holat.BEKOR)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Muvaffaqiyatli:\n'
                f'  - {obuna_count} ta obuna bekor qilindi\n'
                f'  - {tolov_count} ta to\'lov bekor qilindi\n'
            )
        )
