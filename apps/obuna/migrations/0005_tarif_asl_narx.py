# Chegirma (aksiya) narxini qo'llab-quvvatlash uchun asl_narx maydonini qo'shadi
# va birinchi oy tarifini 50% chegirma bilan yangilaydi (99 000 -> 49 500).

from django.db import migrations, models


def apply_birinchi_oy_chegirma(apps, schema_editor):
    """
    Birinchi oy tarifiga chegirma qo'llash:
      - narx      = 49 500  (haqiqatda to'lanadigan summa)
      - asl_narx  = 99 000  (ustidan chiziladigan asl narx)
    """
    Tarif = apps.get_model('obuna', 'Tarif')
    Tarif.objects.filter(kod='birinchi_oy').update(narx=49500, asl_narx=99000)


def revert_birinchi_oy_chegirma(apps, schema_editor):
    """Orqaga qaytarish: chegirmasiz holatga (narx=99 000, asl_narx=None)."""
    Tarif = apps.get_model('obuna', 'Tarif')
    Tarif.objects.filter(kod='birinchi_oy').update(narx=99000, asl_narx=None)


class Migration(migrations.Migration):

    dependencies = [
        ('obuna', '0004_add_birinchi_oy_tarif'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarif',
            name='asl_narx',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text=(
                    "Chegirmagacha bo'lgan asl narx (so'mda). Faqat aksiya/chegirma "
                    "uchun to'ldiriladi. Frontendda ustidan chizib ko'rsatiladi. "
                    "Bo'sh bo'lsa — chegirma yo'q deb hisoblanadi."
                ),
            ),
        ),
        migrations.RunPython(apply_birinchi_oy_chegirma, revert_birinchi_oy_chegirma),
    ]
