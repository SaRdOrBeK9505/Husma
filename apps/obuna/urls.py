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
from .multicard.views import MulticardReturnView, MulticardCallbackView, MulticardCreateInvoiceView

urlpatterns = [
    # ===== PUBLIC / RIELTOR =====
    path('obuna/tariflar/', TarifListView.as_view(), name='obuna-tariflar'),
    path('obuna/mening/', MeningObunamView.as_view(), name='obuna-mening'),
    path('obuna/tarix/', ObunaTarixView.as_view(), name='obuna-tarix'),
    path('obuna/sotib-olish/', ObunaSotibOlishView.as_view(), name='obuna-sotib-olish'),
    path('obuna/<int:pk>/bekor/', ObunaBekorView.as_view(), name='obuna-bekor'),

    # ===== PAYME WEBHOOK =====
    path('obuna/payme/webhook/', PaymeWebhookView.as_view(), name='payme-webhook'),

    # ===== MULTICARD =====
    # Frontend "To'lash" tugmasi bosilganda chaqiriladi — checkout_url qaytaradi
    path("multicard/create/", MulticardCreateInvoiceView.as_view(), name="multicard-create",),
    # Webhook: Multicard server → sizning server (server-to-server POST)
    path('obuna/multicard/return/', MulticardReturnView.as_view(), name='multicard-return'),
    # Callback: Foydalanuvchi to'lovdan keyin redirect bo'ladigan URL (GET)
    path('obuna/multicard/callback/', MulticardCallbackView.as_view(), name='multicard-callback'),

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
