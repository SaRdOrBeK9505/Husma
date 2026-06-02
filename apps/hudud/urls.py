from django.urls import path
from .views import HududListView

urlpatterns = [
    path('hududlar/', HududListView.as_view(), name='hudud-list'),
]