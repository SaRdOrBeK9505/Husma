from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from core.permissions import IsAdminOrMakler
from .models import Kvartira
from .serializers import KvartiraSerializer, KvartiraYaratishSerializer


class KvartiraListView(ListAPIView):
    """Hammaga ochiq — kvartiralar ro'yxati"""
    serializer_class = KvartiraSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['hudud', 'ariza_turi', 'xonalar_soni', 'holat']
    ordering_fields = ['narx', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Kvartira.objects.none()
        return Kvartira.objects.filter(
            holat='active',
            is_verified=True,
        ).select_related('hudud').prefetch_related('rasmlar')

    @extend_schema(
        summary="Kvartiralar ro'yxati",
        description="Tasdiqlangan faol kvartiralar — hammaga ochiq",
        tags=["Kvartira"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class KvartiraDetailView(RetrieveAPIView):
    """Bitta kvartira detail"""
    serializer_class = KvartiraSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Kvartira.objects.none()
        return Kvartira.objects.filter(
            is_verified=True
        ).select_related('hudud').prefetch_related('rasmlar')

    @extend_schema(
        summary="Kvartira detail",
        tags=["Kvartira"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class KvartiraYaratishView(CreateAPIView):
    """Makler yoki Admin kvartira qo'shadi"""
    serializer_class = KvartiraYaratishSerializer
    permission_classes = [IsAdminOrMakler]

    @extend_schema(
        summary="Kvartira qo'shish",
        description="Makler yoki Admin yangi kvartira qo'shadi",
        responses={201: KvartiraSerializer},
        tags=["Kvartira"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kvartira = serializer.save(qoshgan=request.user)
        return Response(
            KvartiraSerializer(kvartira).data,
            status=status.HTTP_201_CREATED
        )