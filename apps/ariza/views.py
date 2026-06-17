from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView, RetrieveUpdateDestroyAPIView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as drf_serializers

from core.permissions import IsUser, IsVerifiedRieltor, IsAdmin, IsUserOrRieltor
from .models import Ariza, ArizaMakler
from .serializers import ArizaYaratishSerializer, ArizaSerializer, MaklerArizaSerializer
from .services import arizani_maklerlarga_yuborish


class ArizaYaratishView(CreateAPIView):
    permission_classes = [IsUserOrRieltor]
    serializer_class = ArizaYaratishSerializer

    @extend_schema(
        summary="Yangi ariza yuborish",
        responses={201: ArizaSerializer},
        tags=["Ariza"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ariza = serializer.save(user=request.user)
        yuborildi = arizani_maklerlarga_yuborish(ariza)
        return Response({
            'ariza': ArizaSerializer(ariza).data,
            'rieltorlarga_yuborildi': yuborildi,
        }, status=status.HTTP_201_CREATED)


class UserArizalarView(ListAPIView):
    permission_classes = [IsUserOrRieltor]
    serializer_class = ArizaSerializer
    queryset = Ariza.objects.none()

    @extend_schema(
        summary="O'z arizalarim ro'yxati",
        parameters=[
            OpenApiParameter(
                name='holat',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Holat bo'yicha filter: yangi | korilmoqda | yopilgan",
                required=False,
                enum=['yangi', 'korilmoqda', 'yopilgan'],
            )
        ],
        responses={200: ArizaSerializer(many=True)},
        tags=["Ariza"],
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'jami_soni': queryset.count(),
            'arizalar': serializer.data,
        })

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Ariza.objects.none()

        qs = Ariza.objects.filter(
            user=self.request.user
        ).select_related('hudud')

        holat = self.request.query_params.get('holat')
        if holat in ['yangi', 'korilmoqda', 'yopilgan']:
            qs = qs.filter(holat=holat)

        return qs


class UserArizaDetailView(RetrieveUpdateDestroyAPIView):
    """User bitta arizasini ko'rish, tahrirlash, o'chirish"""
    permission_classes = [IsUserOrRieltor]
    queryset = Ariza.objects.none()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ArizaYaratishSerializer
        return ArizaSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Ariza.objects.none()
        # Faqat o'zining arizalarini
        return Ariza.objects.filter(
            user=self.request.user
        ).select_related('hudud')

    @extend_schema(
        summary="Arizani ko'rish",
        responses={200: ArizaSerializer},
        tags=["Ariza"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Arizani tahrirlash",
        request=ArizaYaratishSerializer,
        responses={200: ArizaSerializer},
        tags=["Ariza"],
    )
    def patch(self, request, *args, **kwargs):
        # Faqat yangi holatdagi arizani tahrirlash mumkin
        ariza = self.get_object()
        if ariza.holat != 'yangi':
            return Response(
                {'error': 'Faqat yangi holatdagi arizani tahrirlash mumkin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Arizani to'liq yangilash",
        request=ArizaYaratishSerializer,
        responses={200: ArizaSerializer},
        tags=["Ariza"],
    )
    def put(self, request, *args, **kwargs):
        ariza = self.get_object()
        if ariza.holat != 'yangi':
            return Response(
                {'error': 'Faqat yangi holatdagi arizani tahrirlash mumkin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Arizani o'chirish",
        responses={204: None},
        tags=["Ariza"],
    )
    def delete(self, request, *args, **kwargs):
        ariza = self.get_object()
        if ariza.holat == 'korilmoqda':
            return Response(
                {'error': 'Ko\'rilmoqda holatdagi arizani o\'chirib bo\'lmaydi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class RieltorArizalarView(ListAPIView):
    permission_classes = [IsVerifiedRieltor]
    serializer_class = MaklerArizaSerializer
    queryset = Ariza.objects.none()

    @extend_schema(
        summary="Rieltor uchun arizalar",
        parameters=[
            OpenApiParameter(
                name='holat',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Holat bo'yicha filter: yangi | korilmoqda | yopilgan",
                required=False,
                enum=['yangi', 'korilmoqda', 'yopilgan'],
            )
        ],
        responses={200: MaklerArizaSerializer(many=True)},
        tags=["Rieltor"],
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'jami_soni': queryset.count(),
            'arizalar': serializer.data,
        })

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Ariza.objects.none()
        rieltor = self.request.user.rieltor_profil
        ariza_ids = ArizaMakler.objects.filter(
            rieltor=rieltor
        ).values_list('ariza_id', flat=True)

        qs = Ariza.objects.filter(
            id__in=ariza_ids,
        ).select_related('hudud', 'user')

        holat = self.request.query_params.get('holat')
        if holat in ['yangi', 'korilmoqda', 'yopilgan']:
            qs = qs.filter(holat=holat)

        return qs


# Backward compatibility
MaklerArizalarView = RieltorArizalarView


class RieltorArizaDetailView(RetrieveAPIView):
    permission_classes = [IsVerifiedRieltor]
    serializer_class = MaklerArizaSerializer
    queryset = Ariza.objects.none()

    @extend_schema(
        summary="Ariza detail (Rieltor)",
        responses={200: MaklerArizaSerializer},
        tags=["Rieltor"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Ariza.objects.none()
        rieltor = self.request.user.rieltor_profil
        ariza_ids = ArizaMakler.objects.filter(
            rieltor=rieltor
        ).values_list('ariza_id', flat=True)
        return Ariza.objects.filter(id__in=ariza_ids)


# Backward compatibility
MaklerArizaDetailView = RieltorArizaDetailView


class RieltorArizaQabulView(APIView):
    """
    Rieltor arizani qabul qiladi — mijoz bilan bog'lanishga tayyor.

    ArizaMakler.holat: yangi → boglandi
    Ariza.holat: yangi → korilmoqda
    """
    permission_classes = [IsVerifiedRieltor]

    @extend_schema(
        summary="Arizani qabul qilish (Rieltor)",
        description=(
            "Rieltor arizani qabul qilib, mijoz bilan bog'lanishga tayyor ekanini bildiradi.\n\n"
            "**Natija:**\n"
            "- `ArizaMakler.holat` → `boglandi`\n"
            "- `Ariza.holat` → `korilmoqda`\n\n"
            "**Cheklov:** Ariza allaqachon `korilmoqda` yoki `yopilgan` bo'lsa, qabul qilib bo'lmaydi."
        ),
        request=None,
        responses={
            200: inline_serializer(
                name='ArizaQabulResponse',
                fields={
                    'message': drf_serializers.CharField(),
                    'ariza': MaklerArizaSerializer(),
                }
            ),
            400: inline_serializer(
                name='ArizaQabulErrorResponse',
                fields={'error': drf_serializers.CharField()}
            ),
            404: inline_serializer(
                name='ArizaQabulNotFoundResponse',
                fields={'error': drf_serializers.CharField()}
            ),
        },
        tags=["Rieltor"],
    )
    def post(self, request, pk):
        rieltor = request.user.rieltor_profil

        try:
            ariza_makler = ArizaMakler.objects.select_related('ariza').get(
                ariza_id=pk,
                rieltor=rieltor,
            )
        except ArizaMakler.DoesNotExist:
            return Response(
                {'error': 'Ariza topilmadi yoki sizga tegishli emas'},
                status=status.HTTP_404_NOT_FOUND,
            )

        ariza = ariza_makler.ariza

        if ariza.holat != Ariza.Holat.YANGI:
            return Response(
                {'error': f"Ariza '{ariza.get_holat_display()}' holatida, qabul qilib bo'lmaydi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ariza_makler.holat == ArizaMakler.Holat.BOGLANDI:
            return Response(
                {'error': 'Siz bu arizani allaqachon qabul qilgansiz'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ariza_makler.holat = ArizaMakler.Holat.BOGLANDI
        ariza_makler.korilgan_vaqt = timezone.now()
        ariza_makler.save(update_fields=['holat', 'korilgan_vaqt'])

        ariza.holat = Ariza.Holat.KORILMOQDA
        ariza.save(update_fields=['holat'])

        return Response(
            {
                'message': 'Ariza qabul qilindi. Mijoz bilan bog\'laning.',
                'ariza': MaklerArizaSerializer(ariza).data,
            },
            status=status.HTTP_200_OK,
        )


# Backward compatibility
MaklerArizaQabulView = RieltorArizaQabulView


class RieltorArizaYopishView(APIView):
    """
    Rieltor arizani yopadi — ish yakunlandi.

    ArizaMakler.holat: boglandi → yopildi
    Ariza.holat: korilmoqda → yopilgan
    """
    permission_classes = [IsVerifiedRieltor]

    @extend_schema(
        summary="Arizani yopish (Rieltor)",
        description=(
            "Rieltor mijoz bilan ish yakunlanganini bildiradi.\n\n"
            "**Natija:**\n"
            "- `ArizaMakler.holat` → `yopildi`\n"
            "- `Ariza.holat` → `yopilgan`\n\n"
            "**Cheklov:** Faqat `boglandi` holatidagi arizani yopish mumkin.\n\n"
            "**Keyingi qadam:** User endi bu rieltorga review yoza oladi."
        ),
        request=None,
        responses={
            200: inline_serializer(
                name='ArizaYopishResponse',
                fields={
                    'message': drf_serializers.CharField(),
                    'ariza': MaklerArizaSerializer(),
                }
            ),
            400: inline_serializer(
                name='ArizaYopishErrorResponse',
                fields={'error': drf_serializers.CharField()}
            ),
            404: inline_serializer(
                name='ArizaYopishNotFoundResponse',
                fields={'error': drf_serializers.CharField()}
            ),
        },
        tags=["Rieltor"],
    )
    def post(self, request, pk):
        rieltor = request.user.rieltor_profil

        try:
            ariza_makler = ArizaMakler.objects.select_related('ariza').get(
                ariza_id=pk,
                rieltor=rieltor,
            )
        except ArizaMakler.DoesNotExist:
            return Response(
                {'error': 'Ariza topilmadi yoki sizga tegishli emas'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ariza_makler.holat != ArizaMakler.Holat.BOGLANDI:
            return Response(
                {'error': "Faqat 'boglandi' holatidagi arizani yopish mumkin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ariza = ariza_makler.ariza

        ariza_makler.holat = ArizaMakler.Holat.YOPILDI
        ariza_makler.save(update_fields=['holat'])

        ariza.holat = Ariza.Holat.YOPILGAN
        ariza.save(update_fields=['holat'])

        return Response(
            {
                'message': 'Ariza yopildi. Mijoz endi sizga baho qoldira oladi.',
                'ariza': MaklerArizaSerializer(ariza).data,
            },
            status=status.HTTP_200_OK,
        )


# Backward compatibility
MaklerArizaYopishView = RieltorArizaYopishView


class AdminArizalarView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = ArizaSerializer
    queryset = Ariza.objects.none()

    @extend_schema(
        summary="Barcha arizalar (Admin)",
        responses={200: ArizaSerializer(many=True)},
        tags=["Admin"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Ariza.objects.none()
        return Ariza.objects.select_related(
            'hudud', 'user'
        ).prefetch_related('ariza_rieltorlar')