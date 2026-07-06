from django.urls import path
from .views import (
    RieltorProfilView,
    RieltorLoginView,
    AdminRieltorListView,
    AdminStatistikaView,
    RieltorObunaHolatiView,
)

urlpatterns = [
    path('rieltor/profil/', RieltorProfilView.as_view(), name='rieltor-profil'),
    path('rieltor/obuna-holati/', RieltorObunaHolatiView.as_view(), name='rieltor-obuna-holati'),
    # path('auth/rieltor/login/', RieltorLoginView.as_view(), name='rieltor-login'),
    path('admin/rieltorlar/', AdminRieltorListView.as_view(), name='admin-rieltor-list'),
    path('admin/rieltor-statistika/', AdminStatistikaView.as_view(), name='admin-rieltor-statistika'),  # O'zgartirildi
]
