from django.core.management.base import BaseCommand
from apps.obuna.models import Tarif


# Boshlang'ich obuna tariflari.
# Narxlar so'mda — admin paneldan keyin o'zgartirish mumkin.
TARIFLAR = [
    {
        'kod': 'oylik',
        'nomi': 'Oylik obuna',
        'narx': 99000,
        'davomiylik_kun': 30,
        'izoh': '1 oylik to\'liq kirish. Arizalarni cheksiz qabul qiling.',
        'tartib': 1,
    },
    {
        'kod': 'choraklik',
        'nomi': 'Choraklik obuna',
        'narx': 249000,
        'davomiylik_kun': 90,
        'izoh': '3 oylik obuna — oylikka nisbatan tejamkor.',
        'tartib': 2,
    },
    {
        'kod': 'yillik',
        'nomi': 'Yillik obuna',
        'narx': 849000,
        'davomiylik_kun': 365,
        'izoh': '12 oylik obuna — eng foydali taklif.',
        'tartib': 3,
    },
]


class Command(BaseCommand):
    help = "Boshlang'ich obuna tariflarini bazaga yuklaydi"

    def handle(self, *args, **options):
        for data in TARIFLAR:
            obj, created = Tarif.objects.update_or_create(
                kod=data['kod'],
                defaults={
                    'nomi': data['nomi'],
                    'narx': data['narx'],
                    'davomiylik_kun': data['davomiylik_kun'],
                    'izoh': data['izoh'],
                    'tartib': data['tartib'],
                    'is_active': True,
                },
            )
            holat = '+ yaratildi' if created else '~ yangilandi'
            self.stdout.write(
                self.style.SUCCESS(f"{holat}: {obj.nomi} — {obj.narx:,} so'm / {obj.davomiylik_kun} kun")
            )

        self.stdout.write(self.style.SUCCESS("Tayyor! Obuna tariflari yuklandi."))
