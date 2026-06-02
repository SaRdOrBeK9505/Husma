from django.urls import path
from .views import (
    # SiteSettingsView,  # TODO: keyinchalik yoqiladi
    UserStatistikaView,
    UserStatistikaAdminView,
    RieltorStatistikaView,
    KontaktView,
    KontaktAdminView,
    SliderListView,
    SliderAdminListCreateView,
    SliderAdminDetailView,
)

urlpatterns = [
    # Sayt sozlamalari
    # path('settings/', SiteSettingsView.as_view(), name='site-settings'),

    # Statistika
    path('statistika/', UserStatistikaView.as_view(), name='user-statistika'),
    path('rieltor/statistika/', RieltorStatistikaView.as_view(), name='rieltor-statistika'),

    # Slider — foydalanuvchi roli bo'yicha (IsAuthenticated)
    path('slider/', SliderListView.as_view(), name='slider-list'),

    # Kontakt
    path('kontakt/', KontaktView.as_view(), name='kontakt'),

    # ===== ADMIN =====
    # path('admin/statistika/', UserStatistikaAdminView.as_view(), name='admin-user-statistika'),
    # path('admin/kontakt/', KontaktAdminView.as_view(), name='admin-kontakt'),
    # path('admin/slider/', SliderAdminListCreateView.as_view(), name='admin-slider-list'),
    # path('admin/slider/<int:pk>/', SliderAdminDetailView.as_view(), name='admin-slider-detail'),
]
