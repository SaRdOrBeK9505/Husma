# Generated migration for adding first-month tariff

from django.db import migrations


def add_tariflar(apps, schema_editor):
    Tarif = apps.get_model('obuna', 'Tarif')
    
    # Birinchi oy tarifi
    Tarif.objects.create(
        nomi="Birinchi oy (aktsiya)",
        kod="birinchi_oy",
        narx=99000,
        davomiylik_kun=30,
        izoh="Yangi rieltorlar uchun birinchi oy aktsiya narxi",
        tartib=1,
        is_active=True
    )
    
    # Keyingi oylar tarifi
    Tarif.objects.create(
        nomi="Oylik obuna",
        kod="oylik",
        narx=199000,
        davomiylik_kun=30,
        izoh="Davomiy oylik obuna narxi",
        tartib=2,
        is_active=True
    )


class Migration(migrations.Migration):
    dependencies = [
        ('obuna', '0003_add_multicard_provayder'),
    ]

    operations = [
        migrations.RunPython(add_tariflar, migrations.RunPython.noop),
    ]
