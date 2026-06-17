from django.urls import path
from .views import RieltorProfilView, RieltorLoginView, AdminRieltorListView, AdminStatistikaView

urlpatterns = [
    path('rieltor/profil/', RieltorProfilView.as_view(), name='rieltor-profil'),
    path('auth/rieltor/login/', RieltorLoginView.as_view(), name='rieltor-login'),
    # path('admin/rieltorlar/', AdminRieltorListView.as_view(), name='admin-rieltor-list'),
    # path('admin/statistika/', AdminStatistikaView.as_view(), name='admin-statistika'),
]
