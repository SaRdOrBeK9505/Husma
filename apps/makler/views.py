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
    RieltorObunaHolatiSerializer,
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


class RieltorObunaHolatiView(APIView):
    """
    Rieltor obuna holati — Telegram Mini App modal window uchun.
    
    Frontend har safar ochilganda yoki asosiy ekranga qaytganda shu endpoint'ga
    so'rov yuborib obuna holatini tekshiradi va kerak bo'lsa modal oyna ko'rsatadi.
    """
    permission_classes = [IsRieltor]

    @extend_schema(
        summary="Rieltor obuna holati (Telegram Mini App modal uchun)",
        description=(
            "Rieltor obuna holati to'g'risida batafsil ma'lumot qaytaradi.\n\n"
            "Frontend shu endpoint'dan foydalanib:\n"
            "- Rieltorning faol/nofaol ekanini biladi\n"
            "- Qachon obuna tugashini ko'rsatadi\n"
            "- Kerak bo'lganda modal window ko'rsatadi (masalan: obuna tugagan)\n\n"
            "**Modal strategiyasi:**\n"
            "- `modal_korinsin: true` bo'lsa frontend modal window ko'rsatadi\n"
            "- `modal_turi` modal dizayni va rangini belgilaydi\n"
            "- `modal_xabar` modal'da ko'rsatiladigan matn\n\n"
            "**Chaqirish taktikasi:**\n"
            "- Har safar app ochilganda\n"
            "- Asosiy ekranga qaytganda\n"
            "- Ariza ko'rishga urinib ko'rganda (access control)\n"
        ),
        responses={
            200: RieltorObunaHolatiSerializer,
            403: OpenApiResponse(description="Rieltor profili topilmadi"),
        },
        tags=["Rieltor"],
        examples=[
            OpenApiExample(
                name="Faol obuna bor",
                value={
                    "faol": True,
                    "bloklangan": False,
                    "bepul_muddat_tugash": None,
                    "bepul_muddat_qolgan_kunlar": None,
                    "obuna_faol": True,
                    "obuna_tugash": "2026-08-06T10:00:00Z",
                    "obuna_qolgan_kunlar": 31,
                    "obuna_tarif_nomi": "Oylik obuna",
                    "modal_korinsin": False,
                    "modal_xabar": None,
                    "modal_turi": "yoq"
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Obuna tugagan",
                value={
                    "faol": False,
                    "bloklangan": False,
                    "bepul_muddat_tugash": None,
                    "bepul_muddat_qolgan_kunlar": None,
                    "obuna_faol": False,
                    "obuna_tugash": None,
                    "obuna_qolgan_kunlar": None,
                    "obuna_tarif_nomi": None,
                    "modal_korinsin": True,
                    "modal_xabar": "Obunangiz muddati tugadi. Xizmatdan foydalanishni davom ettirish uchun obuna sotib oling.",
                    "modal_turi": "obuna_tugadi"
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Bepul muddat tugashiga yaqin (2 kun qolgan)",
                value={
                    "faol": True,
                    "bloklangan": False,
                    "bepul_muddat_tugash": "2026-07-08T10:00:00Z",
                    "bepul_muddat_qolgan_kunlar": 2,
                    "obuna_faol": False,
                    "obuna_tugash": None,
                    "obuna_qolgan_kunlar": None,
                    "obuna_tarif_nomi": None,
                    "modal_korinsin": True,
                    "modal_xabar": "Bepul sinov muddatingiz tugashiga 2 kun qoldi. Uzluksiz xizmatdan foydalanish uchun obuna sotib oling.",
                    "modal_turi": "eslatma"
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def get(self, request):
        from datetime import timedelta
        
        rieltor = getattr(request.user, 'rieltor_profil', None)
        if not rieltor:
            return Response(
                {"error": "Rieltor profili topilmadi"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        now = timezone.now()
        
        # Bepul muddat
        bepul_muddat_tugash = rieltor.bepul_muddat_tugash
        bepul_qolgan_kunlar = None
        if bepul_muddat_tugash and bepul_muddat_tugash > now:
            bepul_qolgan_kunlar = (bepul_muddat_tugash - now).days
        
        # Obuna
        joriy_obuna = rieltor.obunalar.faol().order_by('-tugash_vaqti').first()
        obuna_faol = joriy_obuna is not None
        obuna_tugash = joriy_obuna.tugash_vaqti if joriy_obuna else None
        obuna_qolgan_kunlar = None
        obuna_tarif_nomi = None
        
        if joriy_obuna:
            obuna_qolgan_kunlar = (joriy_obuna.tugash_vaqti - now).days
            obuna_tarif_nomi = joriy_obuna.tarif.nomi
        
        # Modal strategiyasi
        modal_korinsin = False
        modal_xabar = None
        modal_turi = "yoq"
        
        # 1. Admin bloklagan
        if rieltor.bloklangan:
            modal_korinsin = True
            modal_turi = "bloklangan"
            modal_xabar = (
                "Profilingiz admin tomonidan bloklangan. "
                "Qo'shimcha ma'lumot uchun qo'llab-quvvatlash xizmatiga murojaat qiling."
            )
        
        # 2. Obuna va bepul muddat tugagan
        elif not rieltor.faol:
            modal_korinsin = True
            modal_turi = "obuna_tugadi"
            modal_xabar = (
                "Obunangiz muddati tugadi. "
                "Xizmatdan foydalanishni davom ettirish uchun obuna sotib oling."
            )
        
        # 3. Bepul muddat tugashiga yaqin (3 kun yoki kamroq qolgan)
        elif bepul_qolgan_kunlar is not None and bepul_qolgan_kunlar <= 3 and not obuna_faol:
            modal_korinsin = True
            modal_turi = "eslatma"
            modal_xabar = (
                f"Bepul sinov muddatingiz tugashiga {bepul_qolgan_kunlar} kun qoldi. "
                f"Uzluksiz xizmatdan foydalanish uchun obuna sotib oling."
            )
        
        # 4. Obuna tugashiga yaqin (3 kun yoki kamroq qolgan)
        elif obuna_qolgan_kunlar is not None and obuna_qolgan_kunlar <= 3:
            modal_korinsin = True
            modal_turi = "eslatma"
            modal_xabar = (
                f"Obunangiz tugashiga {obuna_qolgan_kunlar} kun qoldi. "
                f"Uzluksiz xizmatdan foydalanish uchun obunani yangilang."
            )
        
        data = {
            "faol": rieltor.faol,
            "bloklangan": rieltor.bloklangan,
            "bepul_muddat_tugash": bepul_muddat_tugash,
            "bepul_muddat_qolgan_kunlar": bepul_qolgan_kunlar,
            "obuna_faol": obuna_faol,
            "obuna_tugash": obuna_tugash,
            "obuna_qolgan_kunlar": obuna_qolgan_kunlar,
            "obuna_tarif_nomi": obuna_tarif_nomi,
            "modal_korinsin": modal_korinsin,
            "modal_xabar": modal_xabar,
            "modal_turi": modal_turi,
        }
        
        serializer = RieltorObunaHolatiSerializer(data)
        return Response(serializer.data)