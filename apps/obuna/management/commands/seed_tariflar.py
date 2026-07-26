from django.core.management.base import BaseCommand
from apps.obuna.models import Tarif


# Boshlang'ich obuna tariflari.
# Narxlar so'mda — admin paneldan keyin o'zgartirish mumkin.
TARIFLAR = [
    {
        'kod': 'birinchi_oy',
        'nomi': 'Birinchi oy (aksiya)',
        'narx': 49500,          # haqiqatda to'lanadigan summa (50% chegirma)
        'asl_narx': 99000,      # ustidan chiziladigan asl narx
        'davomiylik_kun': 30,
        'izoh': 'Yangi rieltorlar uchun birinchi oy aksiya narxi — 50% chegirma.',
        'tartib': 1,
    },
    {
        'kod': 'oylik',
        'nomi': 'Oylik obuna',
        'narx': 199000,
        'asl_narx': None,
        'davomiylik_kun': 30,
        'izoh': 'Davomiy oylik obuna narxi. Arizalarni cheksiz qabul qiling.',
        'tartib': 2,
    },
    {
        'kod': 'choraklik',
        'nomi': 'Choraklik obuna',
        'narx': 249000,
        'asl_narx': None,
        'davomiylik_kun': 90,
        'izoh': '3 oylik obuna — oylikka nisbatan tejamkor.',
        'tartib': 3,
    },
    {
        'kod': 'yillik',
        'nomi': 'Yillik obuna',
        'narx': 849000,
        'asl_narx': None,
        'davomiylik_kun': 365,
        'izoh': '12 oylik obuna — eng foydali taklif.',
        'tartib': 4,
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
                    'asl_narx': data.get('asl_narx'),
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
