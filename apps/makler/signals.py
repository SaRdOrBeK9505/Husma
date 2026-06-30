"""
Makler app signals — rieltor yaratilganda kanalga xabar yuborish.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MaklerProfil

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MaklerProfil)
def rieltor_yaratilganda_kanalga_xabar(sender, instance, created, **kwargs):
    """
    Yangi rieltor profil yaratilganda Telegram kanalga xabar yuborish taskini ishga tushiradi.
    
    MUHIM:
    - Faqat created=True bo'lganda ishlaydi (idempotentlik)
    - Xato bo'lsa asosiy oqimni to'xtatmaydi (try/except)
    - Background task ishlatadi (Celery)
    """
    if not created:
        return
    
    try:
        from .tasks import kanalga_yangi_rieltor_xabari_yubor
        
        # Celery task'ni background'da ishga tushirish
        # .delay() asinxron ishlatadi — HTTP request blokirovka qilmaydi
        kanalga_yangi_rieltor_xabari_yubor.delay(instance.id)
        
        logger.info(
            f"[Rieltor Signal] Yangi rieltor {instance.id} uchun kanal notification task ishga tushdi"
        )
    except Exception as e:
        # Signal ichida xato bo'lsa asosiy oqimni to'xtatmaymiz
        logger.error(
            f"[Rieltor Signal] Kanal notification task ishga tushmadi: {e}",
            exc_info=True
        )
