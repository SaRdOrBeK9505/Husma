"""
Kvartira ro'yxati (public katalog) uchun filtrlar.

Frontend katalogidagi filtrlarni qo'llab-quvvatlaydi:
  - Turlar      → mulk_turi
  - Xonalar     → xonalar_soni
  - Qavatlik    → jami_qavat / qavat (aniq qiymat + diapazon)
  - Narx        → narx (min/max diapazon)
"""
import django_filters as filters

from .models import Kvartira


class KvartiraFilter(filters.FilterSet):
    """
    Kvartira uchun kengaytirilgan filtr to'plami.

    Query parametrlari (barchasi ixtiyoriy):
      - hudud, viloyat, mulk_turi, ariza_turi, xonalar_soni, hammom_soni, valyuta
        → aniq (exact) moslik
      - jami_qavat            → binoning aniq qavatliligi (masalan ?jami_qavat=9)
      - jami_qavat_min / jami_qavat_max → qavatlik diapazoni (masalan ?jami_qavat_max=9)
      - qavat                 → kvartira joylashgan aniq qavat
      - qavat_min / qavat_max → qavat diapazoni
      - narx_min / narx_max   → narx diapazoni
    """

    # Qavatlik (bino jami qavatlari) — aniq va diapazon
    jami_qavat_min = filters.NumberFilter(field_name='jami_qavat', lookup_expr='gte')
    jami_qavat_max = filters.NumberFilter(field_name='jami_qavat', lookup_expr='lte')

    # Kvartira joylashgan qavat — aniq va diapazon
    qavat_min = filters.NumberFilter(field_name='qavat', lookup_expr='gte')
    qavat_max = filters.NumberFilter(field_name='qavat', lookup_expr='lte')

    # Narx diapazoni
    narx_min = filters.NumberFilter(field_name='narx', lookup_expr='gte')
    narx_max = filters.NumberFilter(field_name='narx', lookup_expr='lte')

    class Meta:
        model = Kvartira
        fields = [
            'hudud', 'viloyat', 'mulk_turi', 'ariza_turi',
            'xonalar_soni', 'hammom_soni', 'valyuta',
            'jami_qavat', 'qavat', 'remont_holati', 'mebel',
        ]
