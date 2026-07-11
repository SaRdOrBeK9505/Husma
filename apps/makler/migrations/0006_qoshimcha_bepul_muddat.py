# Generated for 14-kunlik qo'shimcha bepul muddat aksiyasi

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('makler', '0005_remove_maklerprofil_obuna_faol_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='maklerprofil',
            name='qoshimcha_bepul_muddat_berildi',
            field=models.BooleanField(
                default=False,
                help_text="14 kunlik qo'shimcha bepul sinov muddati aksiyasi berilganmi",
            ),
        ),
        migrations.AddField(
            model_name='maklerprofil',
            name='qoshimcha_bepul_muddat_vaqti',
            field=models.DateTimeField(
                blank=True, null=True,
                help_text="14 kunlik aksiya qachon berilgani (audit uchun)",
            ),
        ),
    ]
