from apps.makler.models import MaklerProfil
from .models import Ariza, ArizaMakler


def arizani_rieltorlarga_yuborish(ariza: Ariza) -> int:
    """
    Ariza yuborilganda shu hududdagi
    verified rieltorlarga avtomatik yuboradi.
    Nechta rieltorga yuborilganini qaytaradi.
    """
    rieltorlar = MaklerProfil.objects.filter(
        hududlar=ariza.hudud,
        verify_holat='verified',
        user__is_active=True,
    )

    yuborildi = 0
    for rieltor in rieltorlar:
        _, created = ArizaMakler.objects.get_or_create(
            ariza=ariza,
            rieltor=rieltor,
        )
        if created:
            yuborildi += 1

    return yuborildi


# Backward compatibility
arizani_maklerlarga_yuborish = arizani_rieltorlarga_yuborish