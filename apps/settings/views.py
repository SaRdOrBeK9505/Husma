from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import status, generics
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.ariza.models import ArizaMakler
from .models import SiteSettings, KontaktMalumot, UserStatistika, SliderKarta
from .serializers import (
    SiteSettingsSerializer,
    KontaktMalumotSerializer,
    KontaktMalumotAdminSerializer,
    UserStatistikaSerializer,
    UserStatistikaAdminSerializer,
    RieltorStatistikaSerializer,
    SliderKartaSerializer,
    SliderKartaAdminSerializer,
)


# ===== PAGINATION =====

class SliderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20


# ===== SLIDER — USER / RIELTOR =====

class SliderListView(generics.ListAPIView):
    """
    Autentifikatsiya qilingan foydalanuvchi roli bo'yicha
    mos slider kartochkalarini qaytaradi.
    - role='makler' → rieltor panel sliderlari
    - boshqalar → user panel sliderlari
    """
    serializer_class = SliderKartaSerializer
    pagination_class = SliderPagination
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Slider kartochkalar (rol bo'yicha)",
        description=(
            "Autentifikatsiya qilingan foydalanuvchi roliga qarab "
            "mos panel sliderlari qaytariladi. "
            "Makler → rieltor sliderlari, user → user sliderlari."
        ),
        responses={200: SliderKartaSerializer(many=True)},
        tags=["Settings"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # drf-spectacular schema generatsiya qilayotganda fake view bo'ladi
        if getattr(self, 'swagger_fake_view', False):
            return SliderKarta.objects.none()

        if self.request.user.role == 'makler':
            panel = SliderKarta.PanelTuri.RIELTOR
        else:
            panel = SliderKarta.PanelTuri.USER
        return SliderKarta.objects.filter(panel_turi=panel, faol=True)


# ===== SLIDER — ADMIN CRUD =====

class SliderAdminListCreateView(generics.ListCreateAPIView):
    """Admin — barcha sliderlarni ko'rish va yangi qo'shish"""
    queryset = SliderKarta.objects.all()
    serializer_class = SliderKartaAdminSerializer
    pagination_class = SliderPagination
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="[Admin] Slider kartochkalar ro'yxati",
        parameters=[
            OpenApiParameter(
                name='panel_turi',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter: 'user' yoki 'rieltor'",
                required=False,
            )
        ],
        responses={200: SliderKartaAdminSerializer(many=True)},
        tags=["Admin – Settings"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="[Admin] Yangi slider qo'shish",
        request=SliderKartaAdminSerializer,
        responses={201: SliderKartaAdminSerializer},
        tags=["Admin – Settings"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        qs = SliderKarta.objects.all()
        panel = self.request.query_params.get('panel_turi')
        if panel in [SliderKarta.PanelTuri.USER, SliderKarta.PanelTuri.RIELTOR]:
            qs = qs.filter(panel_turi=panel)
        return qs


class SliderAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin — bitta sliderni tahrirlash va o'chirish"""
    queryset = SliderKarta.objects.all()
    serializer_class = SliderKartaAdminSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="[Admin] Slider ko'rish",
        responses={200: SliderKartaAdminSerializer},
        tags=["Admin – Settings"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="[Admin] Sliderni to'liq yangilash",
        request=SliderKartaAdminSerializer,
        responses={200: SliderKartaAdminSerializer},
        tags=["Admin – Settings"],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="[Admin] Sliderni qisman yangilash",
        request=SliderKartaAdminSerializer,
        responses={200: SliderKartaAdminSerializer},
        tags=["Admin – Settings"],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="[Admin] Sliderni o'chirish",
        responses={204: None},
        tags=["Admin – Settings"],
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ===== SAYT SOZLAMALARI =====

class SiteSettingsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Sayt sozlamalari",
        description="Frontend uchun barcha matnlar — hero, ustunliklar, qadamlar, tavsiyalar",
        responses={200: SiteSettingsSerializer},
        tags=["Settings"],
    )
    def get(self, request):
        settings = SiteSettings.get()
        serializer = SiteSettingsSerializer(settings)
        return Response(serializer.data)


# ===== USER STATISTIKASI (static) =====

class UserStatistikaView(APIView):
    """User paneli — 500+ Bitimlar, 50+ Rieltor, 2s Javob"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User paneli statistikasi",
        description="Statik statistika: jami bitimlar, rieltorlar soni, javob vaqti",
        responses={200: UserStatistikaSerializer},
        tags=["Settings"],
    )
    def get(self, request):
        stat = UserStatistika.get()
        serializer = UserStatistikaSerializer(stat)
        return Response(serializer.data)


class UserStatistikaAdminView(APIView):
    """Admin — user statistikasini tahrirlash"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="[Admin] User statistikasini ko'rish",
        responses={200: UserStatistikaAdminSerializer},
        tags=["Admin – Settings"],
    )
    def get(self, request):
        stat = UserStatistika.get()
        return Response(UserStatistikaAdminSerializer(stat).data)

    @extend_schema(
        summary="[Admin] User statistikasini tahrirlash",
        request=UserStatistikaAdminSerializer,
        responses={200: UserStatistikaAdminSerializer},
        tags=["Admin – Settings"],
    )
    def patch(self, request):
        stat = UserStatistika.get()
        serializer = UserStatistikaAdminSerializer(stat, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="[Admin] User statistikasini to'liq yangilash",
        request=UserStatistikaAdminSerializer,
        responses={200: UserStatistikaAdminSerializer},
        tags=["Admin – Settings"],
    )
    def put(self, request):
        stat = UserStatistika.get()
        serializer = UserStatistikaAdminSerializer(stat, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===== RIELTOR STATISTIKASI (dynamic) =====

class RieltorStatistikaView(APIView):
    """Rieltor paneli — Faol arizalar va Konversiya (real-time)"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Rieltor paneli statistikasi",
        description=(
            "Rieltorning shaxsiy statistikasi: "
            "faol arizalar soni va konversiya foizi. "
            "Konversiya = yopilgan arizalar / jami arizalar × 100"
        ),
        responses={200: RieltorStatistikaSerializer},
        tags=["Settings"],
    )
    def get(self, request):
        try:
            rieltor = request.user.rieltor_profil
        except Exception:
            return Response(
                {"detail": "Rieltor profil topilmadi."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Ushbu rieltorga tegishli barcha ariza-rieltor yozuvlari
        qs = ArizaMakler.objects.filter(rieltor=rieltor)
        jami = qs.count()

        # Faol = yangi yoki ko'rildi (yopilmagan)
        faol = qs.filter(holat__in=[
            ArizaMakler.Holat.YANGI,
            ArizaMakler.Holat.KORILDI,
            ArizaMakler.Holat.BOGLANDI,
        ]).count()

        # Konversiya = yopilgan / jami × 100
        yopilgan = qs.filter(holat=ArizaMakler.Holat.YOPILDI).count()
        konversiya = round((yopilgan / jami * 100), 1) if jami > 0 else 0.0

        data = {
            "faol_arizalar": faol,
            "konversiya": konversiya,
        }
        return Response(RieltorStatistikaSerializer(data).data)


# ===== KONTAKT =====

class KontaktView(APIView):
    """User va rieltor paneli — faqat o'qish"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Kontakt ma'lumotlari",
        description="'Biz bilan bog'laning' sahifasi uchun — telefon, email, telegram, ofis manzili",
        responses={200: KontaktMalumotSerializer},
        tags=["Settings"],
    )
    def get(self, request):
        kontakt = KontaktMalumot.get()
        serializer = KontaktMalumotSerializer(kontakt)
        return Response(serializer.data)


class KontaktAdminView(APIView):
    """Admin paneli — kontaktni tahrirlash"""
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="[Admin] Kontakt ma'lumotlarini ko'rish",
        responses={200: KontaktMalumotAdminSerializer},
        tags=["Admin – Settings"],
    )
    def get(self, request):
        kontakt = KontaktMalumot.get()
        return Response(KontaktMalumotAdminSerializer(kontakt).data)

    @extend_schema(
        summary="[Admin] Kontakt ma'lumotlarini tahrirlash",
        request=KontaktMalumotAdminSerializer,
        responses={200: KontaktMalumotAdminSerializer},
        tags=["Admin – Settings"],
    )
    def patch(self, request):
        kontakt = KontaktMalumot.get()
        serializer = KontaktMalumotAdminSerializer(kontakt, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="[Admin] Kontakt ma'lumotlarini to'liq yangilash",
        request=KontaktMalumotAdminSerializer,
        responses={200: KontaktMalumotAdminSerializer},
        tags=["Admin – Settings"],
    )
    def put(self, request):
        kontakt = KontaktMalumot.get()
        serializer = KontaktMalumotAdminSerializer(kontakt, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
