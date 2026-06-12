from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .models import Hudud, Viloyat, MulkTuri
from .serializers import HududSerializer, ViloyatSerializer, MulkTuriSerializer


@extend_schema(
    summary="Barcha hududlar (tumanlar) ro'yxati",
    description="Ariza formasi uchun tumanlar — hammaga ochiq",
    tags=["Hudud"],
)
class HududListView(ListAPIView):
    queryset = Hudud.objects.filter(is_active=True).select_related('viloyat')
    serializer_class = HududSerializer
    permission_classes = [AllowAny]


@extend_schema(
    summary="Shahar/viloyatlar ro'yxati (tumanlari bilan)",
    description="Toshkent shahar, Toshkent viloyati, Andijon viloyati... va har birining tumanlari",
    tags=["Hudud"],
)
class ViloyatListView(ListAPIView):
    queryset = Viloyat.objects.filter(is_active=True).prefetch_related('hududlar')
    serializer_class = ViloyatSerializer
    permission_classes = [AllowAny]


@extend_schema(
    summary="Mulk turlari ro'yxati",
    description="Kvartira, Hovli, Offis, Dalahovli, Bo'sh yer — hammaga ochiq",
    tags=["Hudud"],
)
class MulkTuriListView(ListAPIView):
    queryset = MulkTuri.objects.filter(is_active=True)
    serializer_class = MulkTuriSerializer
    permission_classes = [AllowAny]
