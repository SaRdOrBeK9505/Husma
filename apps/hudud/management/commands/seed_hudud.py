from django.core.management.base import BaseCommand
from apps.hudud.models import Viloyat, MulkTuri, Hudud


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

# Viloyat nomi -> tumanlar/shaharlar ro'yxati.
# Ariza tarqatish aynan tuman (Hudud) bo'yicha ishlagani uchun har bir
# viloyat uchun asosiy tumanlar kiritiladi.
HUDUDLAR = {
    'Toshkent shahar': [
        'Bektemir', 'Chilonzor', "Mirzo Ulug'bek", 'Olmazar', 'Sergeli',
        'Shayxontohur', 'Uchtepa', 'Yakkasaroy', 'Yashnobod', 'Yunusobod',
        'Mirobod', 'Yangihayot',
    ],
    'Toshkent viloyati': [
        'Nurafshon', 'Angren', 'Bekobod', 'Chirchiq', 'Olmaliq',
        'Ohangaron', 'Yangiyo\'l', 'Parkent', 'Piskent', 'Zangiota',
    ],
    'Andijon viloyati': [
        'Andijon shahar', 'Asaka', 'Xonobod', 'Shahrixon', 'Marhamat', 'Qorasuv',
    ],
    "Farg'ona viloyati": [
        "Farg'ona shahar", "Marg'ilon", "Qo'qon", 'Quvasoy', 'Rishton', 'Beshariq',
    ],
    'Namangan viloyati': [
        'Namangan shahar', 'Chust', 'Pop', "To'raqo'rg'on", 'Uchqo\'rg\'on', 'Kosonsoy',
    ],
    'Samarqand viloyati': [
        'Samarqand shahar', 'Kattaqo\'rg\'on', 'Urgut', 'Bulung\'ur', 'Jomboy', 'Ishtixon',
    ],
    'Buxoro viloyati': [
        'Buxoro shahar', "G'ijduvon", 'Kogon', 'Vobkent', 'Romitan', 'Shofirkon',
    ],
    'Navoiy viloyati': [
        'Navoiy shahar', 'Zarafshon', 'Nurota', 'Konimex', 'Qiziltepa',
    ],
    "Qashqadaryo viloyati": [
        'Qarshi', 'Shahrisabz', "G'uzor", 'Kitob', 'Koson', 'Muborak',
    ],
    'Surxondaryo viloyati': [
        'Termiz', 'Denov', 'Sho\'rchi', 'Boysun', 'Jarqo\'rg\'on',
    ],
    'Jizzax viloyati': [
        'Jizzax shahar', 'Gagarin', 'Do\'stlik', 'Zomin', 'Forish',
    ],
    'Sirdaryo viloyati': [
        'Guliston', 'Yangiyer', 'Shirin', 'Sirdaryo', 'Boyovut',
    ],
    'Xorazm viloyati': [
        'Urganch', 'Xiva', 'Hazorasp', 'Shovot', 'Gurlan', 'Yangibozor',
    ],
    "Qoraqalpog'iston Respublikasi": [
        'Nukus', "Beruniy", 'Xo\'jayli', 'Chimboy', 'To\'rtko\'l', 'Mo\'ynoq',
    ],
}


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

        # Tumanlarni (Hudud) viloyatga bog'lab yaratamiz.
        # Ariza tarqatish aynan tuman bo'yicha ishlaydi, shuning uchun
        # mavjud bog'lanmagan tumanlar ham to'g'ri viloyatga ulanadi.
        jami_tuman = 0
        for viloyat_nomi, tumanlar in HUDUDLAR.items():
            viloyat = Viloyat.objects.get(nomi=viloyat_nomi)
            for tuman in tumanlar:
                Hudud.objects.update_or_create(
                    nomi=tuman,
                    viloyat=viloyat,
                    defaults={'shahar': viloyat_nomi, 'is_active': True},
                )
                jami_tuman += 1

        # Eski, viloyatga bog'lanmagan Toshkent tumanlarini bog'laymiz
        try:
            toshkent = Viloyat.objects.get(nomi='Toshkent shahar')
            yangilangan = Hudud.objects.filter(viloyat__isnull=True).update(
                viloyat=toshkent, shahar='Toshkent shahar'
            )
            if yangilangan:
                self.stdout.write(
                    self.style.WARNING(f"~ {yangilangan} ta bog'lanmagan tuman Toshkent shaharga ulandi")
                )
        except Viloyat.DoesNotExist:
            pass

        self.stdout.write(
            self.style.SUCCESS(f"+ {jami_tuman} ta tuman (Hudud) yuklandi")
        )
        self.stdout.write(self.style.SUCCESS("Tayyor! Mulk turlari, viloyatlar va tumanlar yuklandi."))
