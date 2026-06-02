# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ariza', '0001_initial'),
    ]

    operations = [
        # 1. Ariza modeliga ism maydoni qo'shish
        migrations.AddField(
            model_name='ariza',
            name='ism',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        # 2. xonalar_soni choices ni yangilash: '4' -> '4+', '5+' olib tashlash
        migrations.AlterField(
            model_name='ariza',
            name='xonalar_soni',
            field=models.CharField(
                choices=[
                    ('1', '1 xonali'),
                    ('2', '2 xonali'),
                    ('3', '3 xonali'),
                    ('4+', '4+ xonali'),
                ],
                max_length=5,
            ),
        ),
        # 3. ArizaMakler.holat choices ni yangilash: 'yuborildi' -> 'yangi'
        migrations.AlterField(
            model_name='arizamakler',
            name='holat',
            field=models.CharField(
                choices=[
                    ('yangi', 'Yangi'),
                    ('korildi', "Ko'rildi"),
                    ('boglandi', "Bog'landi"),
                    ('yopildi', 'Yopildi'),
                ],
                default='yangi',
                max_length=15,
            ),
        ),
    ]
