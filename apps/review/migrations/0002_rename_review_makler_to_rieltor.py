from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0001_initial'),
        ('makler', '0002_rename_makler_to_rieltor'),
    ]

    operations = [
        # Review modelida makler field → rieltor ga rename
        migrations.RenameField(
            model_name='review',
            old_name='makler',
            new_name='rieltor',
        ),
        migrations.AlterUniqueTogether(
            name='review',
            unique_together={('user', 'rieltor')},
        ),
    ]
