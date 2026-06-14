from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Hudud, Viloyat, MulkTuri
from .serializers import HududSerializer, ViloyatSerializer, MulkTuriSerializer


@extend_schema(
    summary="Barcha hududlar (tumanlar) ro'yxati",
    description=(
        "Ariza/registratsiya formasi uchun tumanlar — hammaga ochiq. "
        "`?viloyat=<id>` bilan tanlangan viloyatga tegishli tumanlarni qaytaradi."
    ),
    parameters=[
        OpenApiParameter(
            name="viloyat",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Viloyat ID — shu viloyatga qarashli tumanlarni filtrlaydi",
        ),
    ],
    tags=["Hudud"],
)
class HududListView(ListAPIView):
    serializer_class = HududSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Hudud.objects.filter(is_active=True).select_related('viloyat')
        viloyat_id = self.request.query_params.get('viloyat')
        if viloyat_id:
            qs = qs.filter(viloyat_id=viloyat_id)
        return qs


@extend_schema(
    summary="Shahar/viloyatlar ro'yxati",
    description="Toshkent shahar, Toshkent viloyati, Andijon viloyati... Tumanlar uchun /hududlar/?viloyat=<id> ishlatiladi",
    tags=["Hudud"],
)
class ViloyatListView(ListAPIView):
    queryset = Viloyat.objects.filter(is_active=True)
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
