from django.urls import path
from .views import HududListView, ViloyatListView, MulkTuriListView

urlpatterns = [
    path('hududlar/', HududListView.as_view(), name='hudud-list'),
    path('viloyatlar/', ViloyatListView.as_view(), name='viloyat-list'),
    path('mulk-turlari/', MulkTuriListView.as_view(), name='mulk-turi-list'),
]
