from django.core.management.base import BaseCommand
from apps.hudud.models import Viloyat, MulkTuri


MULK_TURLARI = [
    ('kvartira', 'Kvartira'),
    ('hovli', 'Hovli'),
    ('offis', 'Offis'),
    ('dalahovli', 'Dalahovli'),
    ('bosh_yer', "Bo'sh yer"),
]

# O'zbekiston shahar va viloyatlari
VILOYATLAR = [
    'Toshkent shahar',
    'Toshkent viloyati',
    'Andijon viloyati',
    "Farg'ona viloyati",
    'Namangan viloyati',
    'Samarqand viloyati',
    'Buxoro viloyati',
    'Navoiy viloyati',
    "Qashqadaryo viloyati",
    'Surxondaryo viloyati',
    'Jizzax viloyati',
    'Sirdaryo viloyati',
    'Xorazm viloyati',
    "Qoraqalpog'iston Respublikasi",
]


class Command(BaseCommand):
    help = "Mulk turlari va shahar/viloyatlar ro'yxatini bazaga yuklaydi"

    def handle(self, *args, **options):
        for tartib, (kod, nomi) in enumerate(MULK_TURLARI):
            obj, created = MulkTuri.objects.update_or_create(
                kod=kod,
                defaults={'nomi': nomi, 'tartib': tartib, 'is_active': True},
            )
            self.stdout.write(
                self.style.SUCCESS(f"{'+ yaratildi' if created else '~ yangilandi'}: {nomi}")
            )

        for tartib, nomi in enumerate(VILOYATLAR):
            obj, created = Viloyat.objects.update_or_create(
                nomi=nomi,
                defaults={'tartib': tartib, 'is_active': True},
            )
            self.stdout.write(
                self.style.SUCCESS(f"{'+ yaratildi' if created else '~ yangilandi'}: {nomi}")
            )

        self.stdout.write(self.style.SUCCESS("Tayyor! Mulk turlari va viloyatlar yuklandi."))
