from django.urls import path
from .views import KvartiraListView, KvartiraDetailView, KvartiraYaratishView

urlpatterns = [
    # Hozircha kvartira funksionallik ishlatilmaydi
    # path('kvartiralar/', KvartiraListView.as_view(), name='kvartira-list'),
    # path('kvartiralar/<int:pk>/', KvartiraDetailView.as_view(), name='kvartira-detail'),
    # path('kvartiralar/yangi/', KvartiraYaratishView.as_view(), name='kvartira-yaratish'),
]