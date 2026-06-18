from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema

from core.permissions import IsUser
from apps.ariza.models import Ariza
from apps.makler.models import MaklerProfil
from .models import Review
from .serializers import (
    ReviewYaratishSerializer,
    ReviewSerializer,
    RieltorReytigSerializer,
    IjobiyReviewSerializer,
)


class ReviewPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 24


class ReviewYaratishView(CreateAPIView):
    """User rieltorga review yozadi"""
    permission_classes = [IsUser]
    serializer_class = ReviewYaratishSerializer

    @extend_schema(
        summary="Rieltorga review yozish",
        description="User rieltor bilan ishlagan bo'lsa baho qoldiradi",
        responses={201: ReviewSerializer},
        tags=["Review"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save(user=request.user)
        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )


class RieltorReviewlarView(ListAPIView):
    """Rieltorning barcha reviewlari"""
    serializer_class = ReviewSerializer
    queryset = Review.objects.none()

    @extend_schema(
        summary="Rieltor reviewlari",
        description="Berilgan rieltorning barcha resenzilar",
        responses={200: ReviewSerializer(many=True)},
        tags=["Review"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        return Review.objects.filter(
            rieltor_id=self.kwargs['rieltor_id']
        ).select_related('user')


class RieltorReytingView(APIView):
    """Rieltorning reytingi va statistikasi"""

    @extend_schema(
        summary="Rieltor reytingi",
        description="Rieltorning o'rtacha reytingi va barcha reviewlari",
        responses={200: RieltorReytigSerializer},
        tags=["Review"],
    )
    def get(self, request, rieltor_id):
        try:
            rieltor = MaklerProfil.objects.select_related('user').get(pk=rieltor_id)
        except MaklerProfil.DoesNotExist:
            return Response(
                {'error': 'Rieltor topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

        reviews = Review.objects.filter(
            rieltor=rieltor
        ).select_related('user')

        data = {
            'rieltor_id': rieltor.id,
            'rieltor_ismi': str(rieltor.user),
            'ortacha_reyting': rieltor.ortacha_reyting,
            'jami_reviewlar': reviews.count(),
            'reviews': ReviewSerializer(reviews, many=True).data,
        }

        return Response(RieltorReytigSerializer(data).data)


class UserReviewlarView(ListAPIView):
    """User o'zi yozgan reviewlarni ko'radi"""
    permission_classes = [IsUser]
    serializer_class = ReviewSerializer
    queryset = Review.objects.none()

    @extend_schema(
        summary="Mening reviewlarim",
        description="User o'zi yozgan barcha reviewlar",
        responses={200: ReviewSerializer(many=True)},
        tags=["Review"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        return Review.objects.filter(
            user=self.request.user
        ).select_related('rieltor__user')


class IjobiyReviewlarView(ListAPIView):
    """
    User paneli — 'Mijozlar fikrlari' bo'limi.
    Faqat ijobiy reviewlar (yulduz >= 4), AllowAny, pagination bilan.
    """
    permission_classes = [AllowAny]
    serializer_class = IjobiyReviewSerializer
    pagination_class = ReviewPagination

    def get_queryset(self):
        # N+1 oldini olish:
        # 1. select_related('user', 'rieltor__user') — Review uchun FK lar
        # 2. Prefetch('user__arizalar') — har user uchun oxirgi arizani oldindan yuklaymiz.
        #    ordering='-created_at' bo'lgani uchun birinchi element — eng oxirgi ariza.
        #    Serializer da _prefetched_objects_cache dan foydalanadi (DB so'rovsiz).
        user_arizalar_prefetch = Prefetch(
            'user__arizalar',
            queryset=Ariza.objects.select_related('hudud').order_by('-created_at'),
        )
        return Review.objects.filter(yulduz__gte=4).select_related(
            'user', 'rieltor__user'
        ).prefetch_related(
            user_arizalar_prefetch
        ).order_by('-created_at')

    @extend_schema(
        summary="Ijobiy reviewlar — Mijozlar fikrlari",
        description=(
            "User paneli uchun ijobiy reviewlar ro'yxati (yulduz ≥ 4). "
            "Har sahifada 6 ta. Autentifikatsiya talab qilinmaydi."
        ),
        responses={200: IjobiyReviewSerializer(many=True)},
        tags=["Review"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)