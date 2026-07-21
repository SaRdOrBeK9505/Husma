from django.urls import path
from .views import (
    # Public
    KvartiraListView,
    KvartiraDetailView,
    # Rieltor
    RieltorKvartiraListCreateView,
    RieltorKvartiraDetailView,
    RieltorKvartiraStatusView,
    RieltorKvartiraRasmView,
    RieltorKvartiraRasmDeleteView,
    RieltorKvartiraRasmAsosiyView,
    RieltorKvartiraPlanirovkaDeleteView,
)

urlpatterns = [
    # --- Public (hammaga ochiq) ---
    path('kvartiralar/', KvartiraListView.as_view(), name='kvartira-list'),
    path('kvartiralar/<int:pk>/', KvartiraDetailView.as_view(), name='kvartira-detail'),

    # --- Rieltor: o'z kvartiralari CRUD ---
    path('rieltor/kvartiralar/', RieltorKvartiraListCreateView.as_view(), name='rieltor-kvartira-list'),
    path('rieltor/kvartiralar/<int:pk>/', RieltorKvartiraDetailView.as_view(), name='rieltor-kvartira-detail'),
    path('rieltor/kvartiralar/<int:pk>/status/', RieltorKvartiraStatusView.as_view(), name='rieltor-kvartira-status'),

    # --- Rieltor: rasm boshqaruvi ---
    path('rieltor/kvartiralar/<int:pk>/rasmlar/', RieltorKvartiraRasmView.as_view(), name='rieltor-kvartira-rasm-qoshish'),
    path('rieltor/kvartiralar/<int:pk>/rasmlar/<int:rasm_id>/', RieltorKvartiraRasmDeleteView.as_view(), name='rieltor-kvartira-rasm-ochirish'),
    path('rieltor/kvartiralar/<int:pk>/rasmlar/<int:rasm_id>/asosiy/', RieltorKvartiraRasmAsosiyView.as_view(), name='rieltor-kvartira-rasm-asosiy'),

    # --- Rieltor: planirovka boshqaruvi ---
    path('rieltor/kvartiralar/<int:pk>/planirovkalar/<int:planirovka_id>/', RieltorKvartiraPlanirovkaDeleteView.as_view(), name='rieltor-kvartira-planirovka-ochirish'),
]
