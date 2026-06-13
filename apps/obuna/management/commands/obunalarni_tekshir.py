"""
Obunalarni davriy tekshirish komandasi.

Cron yoki rejalashtiruvchi orqali kuniga bir marta ishga tushirish tavsiya etiladi:
    python manage.py obunalarni_tekshir

Vazifalari:
1. Muddati o'tgan FAOL obunalarni TUGAGAN deb belgilaydi va xabar yuboradi.
2. Tugashiga belgilangan kun qolgan obunalar egasiga eslatma yuboradi.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.obuna.models import Obuna
from apps.obuna.notifications import obuna_tugadi_xabar, obuna_tugashi_haqida_xabar

# Tugashiga shuncha kun qolganda eslatma yuboriladi
ESLATMA_KUNLARI = [3, 1]


class Command(BaseCommand):
    help = "Muddati o'tgan obunalarni belgilaydi va tugash eslatmalarini yuboradi"

    def handle(self, *args, **options):
        now = timezone.now()

        # 1. Muddati o'tgan faol obunalar
        tugaganlar = Obuna.objects.filter(
            holat=Obuna.Holat.FAOL,
            tugash_vaqti__lt=now,
        ).select_related('tarif', 'rieltor__user')

        tugagan_soni = 0
        for obuna in tugaganlar:
            obuna.holat = Obuna.Holat.TUGAGAN
            obuna.save(update_fields=['holat', 'updated_at'])
            obuna_tugadi_xabar(obuna)
            tugagan_soni += 1

        self.stdout.write(
            self.style.SUCCESS(f"{tugagan_soni} ta obuna 'tugagan' deb belgilandi.")
        )

        # 2. Tugashiga oz qolganlarga eslatma
        eslatma_soni = 0
        for kun in ESLATMA_KUNLARI:
            kun_boshi = (now + timedelta(days=kun)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            kun_oxiri = kun_boshi + timedelta(days=1)
            yaqinlar = Obuna.objects.filter(
                holat=Obuna.Holat.FAOL,
                tugash_vaqti__gte=kun_boshi,
                tugash_vaqti__lt=kun_oxiri,
            ).select_related('tarif', 'rieltor__user')

            for obuna in yaqinlar:
                obuna_tugashi_haqida_xabar(obuna, kun)
                eslatma_soni += 1

        self.stdout.write(
            self.style.SUCCESS(f"{eslatma_soni} ta tugash eslatmasi yuborildi.")
        )
        self.stdout.write(self.style.SUCCESS("Tayyor!"))
