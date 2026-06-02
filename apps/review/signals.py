from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Review


def rieltor_reyting_yangilash(rieltor):
    """Rieltorning o'rtacha reytingini qayta hisoblab saqlaydi"""
    ortacha = Review.objects.filter(
        rieltor=rieltor
    ).aggregate(Avg('yulduz'))['yulduz__avg']

    rieltor.ortacha_reyting = round(ortacha, 2) if ortacha else 0.00
    rieltor.save(update_fields=['ortacha_reyting'])


@receiver(post_save, sender=Review)
def review_saqlanganda(sender, instance, **kwargs):
    rieltor_reyting_yangilash(instance.rieltor)


@receiver(post_delete, sender=Review)
def review_o_chirilganda(sender, instance, **kwargs):
    rieltor_reyting_yangilash(instance.rieltor)
