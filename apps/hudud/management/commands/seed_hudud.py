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
        'Bektemir',
        'Chilonzor',
        "Mirzo Ulug'bek",
        'Mirobod',
        'Olmazar',
        'Sergeli',
        'Shayxontohur',
        'Uchtepa',
        'Yakkasaroy',
        'Yangihayot',
        'Yashnobod',
        'Yunusobod',
    ],
    'Toshkent viloyati': [
        'Nurafshon shahar',
        'Angren shahar',
        'Bekobod shahar',
        'Chirchiq shahar',
        'Olmaliq shahar',
        'Ohangaron shahar',
        "Yangiyo'l shahar",
        'Bekobod tumani',
        "Bo'ka tumani",
        "Bo'stonliq tumani",
        'Zangiota tumani',
        'Qibray tumani',
        'Quyichirchiq tumani',
        "Oqqo'rg'on tumani",
        'Ohangaron tumani',
        'Parkent tumani',
        'Piskent tumani',
        'Toshkent tumani',
        "O'rtachirchiq tumani",
        'Chinoz tumani',
        'Yuqorichirchiq tumani',
        "Yangiyo'l tumani",
    ],
    'Andijon viloyati': [
        'Andijon shahar',
        'Xonabod shahar',
        'Andijon tumani',
        'Asaka tumani',
        'Baliqchi tumani',
        "Bo'z tumani",
        'Buloqboshi tumani',
        'Jalaquduq tumani',
        'Izboskan tumani',
        "Qo'rg'ontepa tumani",
        'Marhamat tumani',
        "Oltinko'l tumani",
        'Paxtaobod tumani',
        "Ulug'nor tumani",
        "Xo'jaobod tumani",
        'Shahrixon tumani',
    ],
    "Farg'ona viloyati": [
        "Farg'ona shahar",
        "Marg'ilon shahar",
        "Qo'qon shahar",
        'Quvasoy shahar',
        'Beshariq tumani',
        "Bog'dod tumani",
        'Buvayda tumani',
        "Dang'ara tumani",
        'Yozyovon tumani',
        'Quva tumani',
        "Qo'shtepa tumani",
        'Oltiariq tumani',
        'Rishton tumani',
        "So'x tumani",
        'Toshloq tumani',
        "O'zbekiston tumani",
        "Uchko'prik tumani",
        "Farg'ona tumani",
        'Furqat tumani',
    ],
    'Namangan viloyati': [
        'Namangan shahar',
        'Kosonsoy tumani',
        'Mingbuloq tumani',
        'Namangan tumani',
        'Norin tumani',
        'Pop tumani',
        "To'raqo'rg'on tumani",
        'Uychi tumani',
        "Uchqo'rg'on tumani",
        'Chortoq tumani',
        'Chust tumani',
        "Yangiqo'rg'on tumani",
    ],
    'Samarqand viloyati': [
        'Samarqand shahar',
        "Kattaqo'rg'on shahar",
        "Bulung'ur tumani",
        'Jomboy tumani',
        'Ishtixon tumani',
        "Kattaqo'rg'on tumani",
        'Narpay tumani',
        'Nurobod tumani',
        'Oqdaryo tumani',
        'Payariq tumani',
        "Pastdarg'om tumani",
        'Paxtachi tumani',
        'Samarqand tumani',
        'Toyloq tumani',
        'Urgut tumani',
        "Qo'shrabot tumani",
    ],
    'Buxoro viloyati': [
        'Buxoro shahar',
        'Kogon shahar',
        'Buxoro tumani',
        'Vobkent tumani',
        'Jondor tumani',
        'Kogon tumani',
        'Olot tumani',
        'Peshku tumani',
        'Romitan tumani',
        'Shofirkon tumani',
        'Qorovulbozor tumani',
        "Qorako'l tumani",
        "G'ijduvon tumani",
    ],
    'Navoiy viloyati': [
        'Navoiy shahar',
        'Zarafshon shahar',
        'Karmana tumani',
        'Konimex tumani',
        'Navbahor tumani',
        'Nurota tumani',
        'Tomdi tumani',
        'Uchquduq tumani',
        'Xatirchi tumani',
        'Qiziltepa tumani',
    ],
    "Qashqadaryo viloyati": [
        'Qarshi shahar',
        'Shahrisabz shahar',
        'Dehqonobod tumani',
        'Kasbi tumani',
        'Kitob tumani',
        'Koson tumani',
        'Mirishkor tumani',
        'Muborak tumani',
        'Nishon tumani',
        'Chiroqchi tumani',
        'Shahrisabz tumani',
        "Yakkabog' tumani",
        'Qamashi tumani',
        'Qarshi tumani',
        "G'uzor tumani",
    ],
    'Surxondaryo viloyati': [
        'Termiz shahar',
        'Angor tumani',
        'Boysun tumani',
        'Denov tumani',
        "Jarqo'rg'on tumani",
        'Muzrobod tumani',
        'Oltinsoy tumani',
        'Sariosiyo tumani',
        'Termiz tumani',
        'Uzun tumani',
        'Sherobod tumani',
        "Sho'rchi tumani",
        'Qiziriq tumani',
        "Qumqo'rg'on tumani",
        'Bandixon tumani',
    ],
    'Jizzax viloyati': [
        'Jizzax shahar',
        'Arnasoy tumani',
        'Baxmal tumani',
        "Do'stlik tumani",
        'Zarbdor tumani',
        'Zafarobod tumani',
        'Zomin tumani',
        "Mirzacho'l tumani",
        'Paxtakor tumani',
        'Forish tumani',
        'Sharof Rashidov tumani',
        "G'allaorol tumani",
        'Yangiobod tumani',
    ],
    'Sirdaryo viloyati': [
        'Guliston shahar',
        'Yangiyer shahar',
        'Shirin shahar',
        'Boyovut tumani',
        'Guliston tumani',
        'Mirzaobod tumani',
        'Oqoltin tumani',
        'Sardoba tumani',
        'Sayxunobod tumani',
        'Sirdaryo tumani',
        'Xovos tumani',
    ],
    'Xorazm viloyati': [
        'Urganch shahar',
        'Xiva shahar',
        "Bog'ot tumani",
        'Gurlan tumani',
        'Urganch tumani',
        'Xiva tumani',
        'Xonqa tumani',
        'Hazorasp tumani',
        'Shovot tumani',
        'Yangiariq tumani',
        'Yangibozor tumani',
        "Qo'shko'pir tumani",
        "Tuproqqal'a tumani",
    ],
    "Qoraqalpog'iston Respublikasi": [
        'Nukus shahar',
        'Amudaryo tumani',
        'Beruniy tumani',
        'Kegeyli tumani',
        "Qonliko'l tumani",
        "Qorao'zak tumani",
        "Qo'ng'irot tumani",
        "Mo'ynoq tumani",
        'Nukus tumani',
        'Taxiatosh tumani',
        "Taxtako'pir tumani",
        "To'rtko'l tumani",
        "Xo'jayli tumani",
        'Chimboy tumani',
        "Sho'manoy tumani",
        "Ellikqal'a tumani",
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
                # Dublikatlarga chidamli: avval shu nomli tumanlarni topamiz.
                mavjud = Hudud.objects.filter(nomi=tuman, viloyat=viloyat)
                if mavjud.count() > 1:
                    # Bir nechta dublikat bo'lsa — bittasini qoldirib, qolganini o'chiramiz.
                    birinchi = mavjud.first()
                    mavjud.exclude(pk=birinchi.pk).delete()
                    birinchi.shahar = viloyat_nomi
                    birinchi.is_active = True
                    birinchi.save(update_fields=['shahar', 'is_active'])
                    self.stdout.write(
                        self.style.WARNING(f"~ dublikat tozalandi: {tuman} ({viloyat_nomi})")
                    )
                elif mavjud.count() == 1:
                    obj = mavjud.first()
                    obj.shahar = viloyat_nomi
                    obj.is_active = True
                    obj.save(update_fields=['shahar', 'is_active'])
                else:
                    Hudud.objects.create(
                        nomi=tuman,
                        viloyat=viloyat,
                        shahar=viloyat_nomi,
                        is_active=True,
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
