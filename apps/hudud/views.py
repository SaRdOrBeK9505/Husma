from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .models import Hudud
from .serializers import HududSerializer


@extend_schema(
    summary="Barcha hududlar ro'yxati",
    description="Ariza formasi uchun hududlar — hammaga ochiq",
    tags=["Hudud"],
)
class HududListView(ListAPIView):
    queryset = Hudud.objects.filter(is_active=True)
    serializer_class = HududSerializer
    permission_classes = [AllowAny]