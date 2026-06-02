from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse

from core.permissions import IsRieltor, IsAdmin
from .models import MaklerProfil, CustomUser
from .serializers import (
    RieltorProfilSerializer,
    RieltorProfilUpdateSerializer,
    RieltorVerifySerializer,
)


class RieltorProfilView(RetrieveUpdateAPIView):
    permission_classes = [IsRieltor]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RieltorProfilUpdateSerializer
        return RieltorProfilSerializer

    def get_object(self):
        return self.request.user.rieltor_profil

    @extend_schema(
        summary="Rieltor o'z profilini ko'rish",
        responses={200: RieltorProfilSerializer},
        tags=["Rieltor"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Rieltor profilini yangilash (bio, hududlar)",
        request=RieltorProfilUpdateSerializer,
        responses={200: RieltorProfilSerializer},
        tags=["Rieltor"],
    )
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class AdminRieltorListView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = RieltorProfilSerializer

    def get_queryset(self):
        return MaklerProfil.objects.select_related('user').prefetch_related('hududlar')

    @extend_schema(
        summary="Barcha rieltorlar ro'yxati (Admin)",
        responses={200: RieltorProfilSerializer(many=True)},
        tags=["Admin"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminRieltorVerifyView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Rieltorni verify qilish (Admin)",
        request=RieltorVerifySerializer,
        responses={200: RieltorProfilSerializer},
        tags=["Admin"],
    )
    def post(self, request, pk):
        try:
            rieltor = MaklerProfil.objects.get(pk=pk)
        except MaklerProfil.DoesNotExist:
            return Response(
                {'error': 'Rieltor topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RieltorVerifySerializer(rieltor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if request.data.get('verify_holat') == 'verified':
            rieltor.verify_qilingan_vaqt = timezone.now()

        serializer.save()
        return Response(RieltorProfilSerializer(rieltor).data)


class AdminStatistikaView(APIView):
    """Admin dashboard uchun to'liq statistika"""
    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin statistikasi",
        description="Admin dashboard uchun to'liq statistika",
        responses={
            200: OpenApiResponse(description="Admin statistikasi")
        },
        tags=["Admin"],
    )
    def get(self, request):
        from apps.ariza.models import Ariza
        from apps.review.models import Review

        data = {
            "foydalanuvchilar": {
                "jami": CustomUser.objects.filter(role='user').count(),
                "bugun": CustomUser.objects.filter(
                    role='user',
                    created_at__date=timezone.now().date()
                ).count(),
            },
            "rieltorlar": {
                "jami": MaklerProfil.objects.count(),
                "verified": MaklerProfil.objects.filter(verify_holat='verified').count(),
                "pending": MaklerProfil.objects.filter(verify_holat='pending').count(),
                "rejected": MaklerProfil.objects.filter(verify_holat='rejected').count(),
            },
            "arizalar": {
                "jami": Ariza.objects.count(),
                "yangi": Ariza.objects.filter(holat='yangi').count(),
                "korilmoqda": Ariza.objects.filter(holat='korilmoqda').count(),
                "yopilgan": Ariza.objects.filter(holat='yopilgan').count(),
                "bugun": Ariza.objects.filter(
                    created_at__date=timezone.now().date()
                ).count(),
            },
            "reviewlar": {
                "jami": Review.objects.count(),
            },
        }
        return Response(data)