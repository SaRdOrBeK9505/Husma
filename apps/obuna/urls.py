from django.urls import path
from .views import (
    # Public / Rieltor
    TarifListView,
    MeningObunamView,
    ObunaTarixView,
    ObunaSotibOlishView,
    ObunaBekorView,
    # Admin
    AdminTarifListCreateView,
    AdminTarifDetailView,
    AdminObunaListView,
    AdminObunaDetailView,
    AdminObunaBerishView,
    AdminTolovListView,
    AdminTolovTasdiqlashView,
)
from .payme.views import PaymeWebhookView

urlpatterns = [
    # ===== PUBLIC / RIELTOR =====
    path('obuna/tariflar/', TarifListView.as_view(), name='obuna-tariflar'),
    path('obuna/mening/', MeningObunamView.as_view(), name='obuna-mening'),
    path('obuna/tarix/', ObunaTarixView.as_view(), name='obuna-tarix'),
    path('obuna/sotib-olish/', ObunaSotibOlishView.as_view(), name='obuna-sotib-olish'),
    path('obuna/<int:pk>/bekor/', ObunaBekorView.as_view(), name='obuna-bekor'),

    # ===== PAYME WEBHOOK (Payme kabinetga shu URL kiritiladi) =====
    path('obuna/payme/webhook/', PaymeWebhookView.as_view(), name='payme-webhook'),

    # ===== ADMIN: TARIF CRUD =====
    # path('admin/obuna/tariflar/', AdminTarifListCreateView.as_view(), name='admin-tarif-list'),
    # path('admin/obuna/tariflar/<int:pk>/', AdminTarifDetailView.as_view(), name='admin-tarif-detail'),
    #
    # # ===== ADMIN: OBUNA BOSHQARUVI =====
    # path('admin/obuna/obunalar/', AdminObunaListView.as_view(), name='admin-obuna-list'),
    # path('admin/obuna/obunalar/<int:pk>/', AdminObunaDetailView.as_view(), name='admin-obuna-detail'),
    # path('admin/obuna/berish/', AdminObunaBerishView.as_view(), name='admin-obuna-berish'),
    #
    # # ===== ADMIN: TO'LOVLAR =====
    # path('admin/obuna/tolovlar/', AdminTolovListView.as_view(), name='admin-tolov-list'),
    # path('admin/obuna/tolovlar/<int:pk>/tasdiqlash/', AdminTolovTasdiqlashView.as_view(), name='admin-tolov-tasdiqlash'),
]
