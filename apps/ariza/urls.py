from django.urls import path
from .views import (
    ArizaYaratishView,
    UserArizalarView,
    RieltorArizalarView,
    RieltorArizaDetailView,
    RieltorArizaQabulView,
    RieltorArizaYopishView,
    AdminArizalarView,
    UserArizaDetailView,
)

urlpatterns = [
    # User
    path('arizalar/', ArizaYaratishView.as_view(), name='ariza-yaratish'),
    path('arizalar/mening/', UserArizalarView.as_view(), name='user-arizalar'),
    path('arizalar/<int:pk>/', UserArizaDetailView.as_view(), name='ariza-detail'),

    # Rieltor
    path('rieltor/arizalar/', RieltorArizalarView.as_view(), name='rieltor-arizalar'),
    path('rieltor/arizalar/<int:pk>/', RieltorArizaDetailView.as_view(), name='rieltor-ariza-detail'),
    path('rieltor/arizalar/<int:pk>/qabul/', RieltorArizaQabulView.as_view(), name='rieltor-ariza-qabul'),
    path('rieltor/arizalar/<int:pk>/yopish/', RieltorArizaYopishView.as_view(), name='rieltor-ariza-yopish'),

    # Admin
    path('admin/arizalar/', AdminArizalarView.as_view(), name='admin-arizalar'),
]