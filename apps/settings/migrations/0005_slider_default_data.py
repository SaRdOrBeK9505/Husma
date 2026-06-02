from django.db import migrations


def add_default_sliders(apps, schema_editor):
    SliderKarta = apps.get_model('settings', 'SliderKarta')

    default_sliders = [
        # ===== USER PANEL (3 ta) =====
        {
            'panel_turi': 'user',
            'badge_matn': 'Husma Estate',
            'sarlavha': None,
            'title': "Orzuingizdagi kvartirani topamiz",
            'description': "Professional rieltor sizga ideal variantni tanlashda yordam beradi",
            'tartib': 1,
            'faol': True,
        },
        {
            'panel_turi': 'user',
            'badge_matn': 'Husma Estate',
            'sarlavha': 'Eng yaxshi narxlar',
            'title': "Minimal komissiya — atigi 1%",
            'description': "Shahardagi eng arzon narxlar bilan ish ko'ramiz",
            'tartib': 2,
            'faol': True,
        },
        {
            'panel_turi': 'user',
            'badge_matn': 'Xavfsiz bitim',
            'sarlavha': 'Yuridik kafolat',
            'title': "Barcha hujjatlar tekshirilgan",
            'description': "Bitim oldidan yuridik tozalikni to'liq taMinlaymiz",
            'tartib': 3,
            'faol': True,
        },

        # ===== RIELTOR PANEL (2 ta) =====
        {
            'panel_turi': 'rieltor',
            'badge_matn': 'Rieltor paneli',
            'sarlavha': 'Bugungi holat',
            'title': "Mijozlardan dolzarb arizalar",
            'description': None,
            'tartib': 1,
            'faol': True,
        },
        {
            'panel_turi': 'rieltor',
            'badge_matn': 'Rieltor paneli',
            'sarlavha': 'Yangi imkoniyat',
            'title': "Yangi arizalar sizni kutmoqda",
            'description': "Tezroq javob bering — konversiyangizni oshiring",
            'tartib': 2,
            'faol': True,
        },
    ]

    for data in default_sliders:
        SliderKarta.objects.create(**data)


def remove_default_sliders(apps, schema_editor):
    SliderKarta = apps.get_model('settings', 'SliderKarta')
    SliderKarta.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0004_slider_karta'),
    ]

    operations = [
        migrations.RunPython(add_default_sliders, remove_default_sliders),
    ]
