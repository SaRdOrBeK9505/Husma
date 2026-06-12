from django.urls import path
from .views import RieltorProfilView, AdminRieltorListView, AdminStatistikaView

urlpatterns = [
    path('rieltor/profil/', RieltorProfilView.as_view(), name='rieltor-profil'),
    # path('admin/rieltorlar/', AdminRieltorListView.as_view(), name='admin-rieltor-list'),
    # path('admin/statistika/', AdminStatistikaView.as_view(), name='admin-statistika'),
]
