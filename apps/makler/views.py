from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from core.permissions import IsRieltor, IsAdmin
from .models import MaklerProfil, CustomUser
from .serializers import (
    RieltorProfilSerializer,
    RieltorProfilUpdateSerializer,
    RieltorLoginSerializer,
    RieltorLoginResponseSerializer,
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
        summary="Rieltor profilini yangilash (bio, hududlar, mulk turlari)",
        request=RieltorProfilUpdateSerializer,
        responses={200: RieltorProfilSerializer},
        tags=["Rieltor"],
    )
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class RieltorLoginView(APIView):
    """
    Telegram auth orqali olingan token bilan rieltor profilini tasdiqlash.
    Yangi token CHIQARILMAYDI — joriy token davom etadi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Rieltor sifatida kirish (token yangilanmaydi)",
        description=(
            "Telegram auth orqali olingan Bearer token bilan so'rov yuboring. "
            "Bu endpoint username/parolni tekshirib, rieltor profilini qaytaradi. "
            "Yangi token **chiqarilmaydi** — mavjud token bilan ishlashda davom etiladi."
        ),
        request=RieltorLoginSerializer,
        responses={
            200: RieltorLoginResponseSerializer,
            400: OpenApiResponse(description="Username/parol noto'g'ri yoki bo'sh"),
            403: OpenApiResponse(description="Profil admin tomonidan bloklangan"),
            404: OpenApiResponse(description="Rieltor profili topilmadi"),
        },
        tags=["Rieltor"],
        examples=[
            OpenApiExample(
                name="Muvaffaqiyatli tasdiqlash",
                value={
                    "message": "Rieltor sifatida tasdiqlandi",
                    "rieltor": {
                        "id": 1,
                        "bio": "Professional rieltor",
                        "verify_holat": "verified",
                        "faol": True,
                    }
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request):
        serializer = RieltorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # username/parol joriy (telegram orqali aniqlangan) userga tegishli ekanini tekshiramiz
        if request.user.username != username or not request.user.check_password(password):
            return Response(
                {'error': "Username yoki parol noto'g'ri"},
                status=status.HTTP_400_BAD_REQUEST
            )

        rieltor_profil = getattr(request.user, 'rieltor_profil', None)
        if rieltor_profil is None:
            return Response(
                {'error': "Bu hisobda rieltor profili topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )

        if rieltor_profil.bloklangan:
            return Response(
                {'error': "Profilingiz admin tomonidan bloklangan"},
                status=status.HTTP_403_FORBIDDEN
            )

        # MUHIM: yangi token chiqarilmaydi — joriy (telegram auth'dan kelgan) token davom etadi
        return Response({
            'message': "Rieltor sifatida tasdiqlandi",
            'rieltor': {
                'id': rieltor_profil.id,
                'bio': rieltor_profil.bio,
                'verify_holat': rieltor_profil.verify_holat,
                'faol': rieltor_profil.faol,
            }
        }, status=status.HTTP_200_OK)


class AdminRieltorListView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = RieltorProfilSerializer

    def get_queryset(self):
        from django.db.models import Q
        from datetime import timedelta
        
        qs = MaklerProfil.objects.select_related('user').prefetch_related('hududlar')
        
        # Filter by verify_holat
        verify_holat = self.request.query_params.get('verify_holat')
        if verify_holat in ['verified', 'pending', 'rejected']:
            qs = qs.filter(verify_holat=verify_holat)
        
        # Filter by faol status
        faol = self.request.query_params.get('faol')
        if faol == 'true':
            # Filter for active rieltors (not blocked and has active subscription or trial)
            now = timezone.now()
            qs = qs.filter(verify_holat='verified').filter(
                Q(bepul_muddat_tugash__gte=now) | Q(obunalar__tugash_vaqti__gte=now, obunalar__holat='active')
            ).distinct()
        elif faol == 'false':
            # Filter for inactive rieltors
            now = timezone.now()
            qs = qs.filter(
                Q(verify_holat='rejected') |
                Q(bepul_muddat_tugash__lt=now)
            ).distinct()
        
        return qs

    @extend_schema(
        summary="Barcha rieltorlar ro'yxati (Admin)",
        parameters=[
            OpenApiParameter(
                name='verify_holat',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Verify holat bo'yicha filter: verified | pending | rejected",
                required=False,
                enum=['verified', 'pending', 'rejected'],
            ),
            OpenApiParameter(
                name='faol',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Faollik holati bo'yicha filter: true | false",
                required=False,
            ),
        ],
        responses={200: RieltorProfilSerializer(many=True)},
        tags=["Admin"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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