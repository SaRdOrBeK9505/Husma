from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ariza', '0002_ariza_ism_alter_ariza_xonalar_soni_and_more'),
    ]

    operations = [
        # ArizaMakler modelida makler field → rieltor ga rename
        migrations.RenameField(
            model_name='arizamakler',
            old_name='makler',
            new_name='rieltor',
        ),
        # verbose_name va related_name o'zgarishlari uchun AlterField
        migrations.AlterModelOptions(
            name='arizamakler',
            options={
                'verbose_name': 'Ariza-Rieltor',
                'verbose_name_plural': 'Ariza-Rielторlar',
            },
        ),
        migrations.AlterUniqueTogether(
            name='arizamakler',
            unique_together={('ariza', 'rieltor')},
        ),
    ]
