from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from drf_spectacular.utils import extend_schema

from rest_framework.pagination import PageNumberPagination

from core.permissions import IsAdminOrActiveRieltor, bepul_kvartira_limiti_tekshir
from .models import Kvartira, KvartiraRasm, KvartiraPlanirovka
from .filters import KvartiraFilter
from .mixins import LogRequestMixin


class KvartiraPagination(PageNumberPagination):
    """Public kvartira ro'yxati uchun sahifalash.

    So'rov: ?page=2&page_size=24
    Javob: count, next, previous, results.
    """
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 60
from .serializers import (
    KvartiraSerializer,
    KvartiraYaratishSerializer,
    KvartiraStatusSerializer,
    KvartiraRasmYuklashSerializer,
    KvartiraRasmSerializer,
    KvartiraPlanirovkaSerializer,
)


# ============================================================
# PUBLIC — hammaga ochiq
# ============================================================
class KvartiraListView(ListAPIView):
    """Tasdiqlangan faol kvartiralar ro'yxati — hammaga ochiq."""
    serializer_class = KvartiraSerializer
    permission_classes = [AllowAny]
    pagination_class = KvartiraPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = KvartiraFilter
    search_fields = ['sarlavha', 'tavsif', 'manzil']
    ordering_fields = ['narx', 'created_at']
    ordering = ['-featured', '-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Kvartira.objects.none()
        return Kvartira.objects.filter(
            holat=Kvartira.Holat.ACTIVE,
            is_verified=True,
        ).select_related('hudud', 'viloyat', 'mulk_turi', 'qoshgan') \
         .prefetch_related('rasmlar', 'planirovkalar')

    @extend_schema(summary="Kvartiralar ro'yxati (public)", tags=["Kvartira"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class KvartiraDetailView(RetrieveAPIView):
    """Bitta kvartira detail — hammaga ochiq."""
    serializer_class = KvartiraSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Kvartira.objects.none()
        return Kvartira.objects.filter(is_verified=True) \
            .select_related('hudud', 'viloyat', 'mulk_turi', 'qoshgan') \
            .prefetch_related('rasmlar', 'planirovkalar')

    @extend_schema(summary="Kvartira detail (public)", tags=["Kvartira"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ============================================================
# RIELTOR — o'z kvartiralarini boshqarish
# ============================================================
class RieltorKvartiraListCreateView(LogRequestMixin, ListCreateAPIView):
    """Rieltor o'z kvartiralarini ko'radi va yangi qo'shadi."""
    log_action_name = 'RIELTOR KVARTIRA LIST/CREATE'
    permission_classes = [IsAdminOrActiveRieltor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = KvartiraPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['holat', 'ariza_turi', 'is_verified']
    ordering_fields = ['narx', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return KvartiraYaratishSerializer
        return KvartiraSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Kvartira.objects.none()
        return Kvartira.objects.filter(qoshgan=self.request.user) \
            .select_related('hudud', 'viloyat', 'mulk_turi') \
            .prefetch_related('rasmlar', 'planirovkalar')

    def _telegram_malumot(self, user):
        """Rieltorning telegram username/id sini background sifatida oladi."""
        data = {}
        username = getattr(user, 'telegram_username', None)
        if username and not str(username).startswith('@'):
            username = f"@{username}"
        data['telegram_username'] = username
        data['telegram_id'] = getattr(user, 'telegram_id', None)
        return data

    @extend_schema(summary="Rieltor: mening kvartiralarim", tags=["Kvartira - Rieltor"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Rieltor: yangi kvartira qo'shish",
        request=KvartiraYaratishSerializer,
        responses={201: KvartiraSerializer},
        tags=["Kvartira - Rieltor"],
    )
    def post(self, request, *args, **kwargs):
        # Admin uchun limit tekshiruvi o'tkazib yuboriladi
        if request.user.role != 'admin':
            profil = getattr(request.user, 'rieltor_profil', None)
            if profil is not None:
                limit_natija = bepul_kvartira_limiti_tekshir(profil)
                if not limit_natija['ruxsat']:
                    return Response(
                        {
                            'error': limit_natija['xabar'],
                            'jami_kvartiralar': limit_natija['jami'],
                            'limit': limit_natija['limit'],
                            'obuna_kerak': True,
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Telegram username/id ni rieltor profilidan avtomatik olamiz (background)
        tg = self._telegram_malumot(request.user)
        # Foydalanuvchi o'zi telegram_username yubormagan bo'lsa — profildan olamiz
        save_kwargs = {'qoshgan': request.user, 'telegram_id': tg['telegram_id']}
        if not serializer.validated_data.get('telegram_username') and tg['telegram_username']:
            save_kwargs['telegram_username'] = tg['telegram_username']

        # --- VAQTINCHALIK: admin moderatsiyasi o'chirilgan ---
        # Hozircha rieltor qo'shgan kvartira darhol tasdiqlangan (is_verified=True)
        # holatda yaratiladi va userlarga to'g'ridan-to'g'ri ko'rinadi.
        # KEYINCHALIK moderatsiya qaytarilganda — shu qatorni o'chirish kifoya
        # (default is_verified=False bo'lgani uchun admin qo'lda tasdiqlaydi).
        save_kwargs['is_verified'] = True

        kvartira = serializer.save(**save_kwargs)
        return Response(
            KvartiraSerializer(kvartira).data,
            status=status.HTTP_201_CREATED
        )


class RieltorKvartiraDetailView(LogRequestMixin, RetrieveUpdateDestroyAPIView):
    """Rieltor o'z kvartirasini ko'radi / tahrirlaydi / o'chiradi."""
    log_action_name = 'RIELTOR KVARTIRA DETAIL'
    permission_classes = [IsAdminOrActiveRieltor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return KvartiraYaratishSerializer
        return KvartiraSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Kvartira.objects.none()
        return Kvartira.objects.filter(qoshgan=self.request.user) \
            .select_related('hudud', 'viloyat', 'mulk_turi') \
            .prefetch_related('rasmlar', 'planirovkalar')

    @extend_schema(summary="Rieltor: kvartira detail", tags=["Kvartira - Rieltor"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Rieltor: kvartirani tahrirlash",
        request=KvartiraYaratishSerializer,
        responses={200: KvartiraSerializer},
        tags=["Kvartira - Rieltor"],
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        kvartira = serializer.save()
        return Response(KvartiraSerializer(kvartira).data)

    @extend_schema(summary="Rieltor: kvartirani o'chirish", tags=["Kvartira - Rieltor"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class RieltorKvartiraStatusView(LogRequestMixin, APIView):
    """Rieltor kvartira statusini o'zgartiradi (faol / sotilgan / arxiv)."""
    log_action_name = 'RIELTOR KVARTIRA STATUS'
    permission_classes = [IsAdminOrActiveRieltor]

    def get_object(self, request, pk):
        return get_object_or_404(Kvartira, pk=pk, qoshgan=request.user)

    @extend_schema(
        summary="Rieltor: kvartira statusini o'zgartirish",
        request=KvartiraStatusSerializer,
        responses={200: KvartiraSerializer},
        tags=["Kvartira - Rieltor"],
    )
    def patch(self, request, pk):
        kvartira = self.get_object(request, pk)
        serializer = KvartiraStatusSerializer(kvartira, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(KvartiraSerializer(kvartira).data)


# ============================================================
# RIELTOR — rasm boshqaruvi
# ============================================================
class RieltorKvartiraRasmView(LogRequestMixin, APIView):
    """Mavjud kvartiraga yangi rasm(lar) qo'shish."""
    log_action_name = 'RIELTOR KVARTIRA RASM QO\'SHISH'
    permission_classes = [IsAdminOrActiveRieltor]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, request, pk):
        return get_object_or_404(Kvartira, pk=pk, qoshgan=request.user)

    @extend_schema(
        summary="Rieltor: kvartiraga yangi rasm qo'shish",
        request=KvartiraRasmYuklashSerializer,
        responses={201: KvartiraRasmSerializer(many=True)},
        tags=["Kvartira - Rieltor"],
    )
    def post(self, request, pk):
        from .serializers import MAX_RASM_SONI, heic_ni_jpegga_aylantir
        kvartira = self.get_object(request, pk)
        serializer = KvartiraRasmYuklashSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        yangi_rasmlar = serializer.validated_data['rasmlar']

        mavjud = kvartira.rasmlar.count()
        if mavjud + len(yangi_rasmlar) > MAX_RASM_SONI:
            return Response(
                {'rasmlar': f"Jami rasmlar {MAX_RASM_SONI} tadan oshmasligi kerak. "
                            f"Hozir {mavjud} ta bor."},
                status=status.HTTP_400_BAD_REQUEST
            )

        bosh_rasm_bormi = kvartira.rasmlar.filter(asosiy=True).exists()
        yaratilgan = []
        # transaction.atomic() — bir nechta rasm saqlashda xato bo'lsa,
        # chala yuklangan rasmlar DB'da qolmaydi
        with transaction.atomic():
            for i, rasm in enumerate(yangi_rasmlar):
                obj = KvartiraRasm.objects.create(
                    kvartira=kvartira, rasm=heic_ni_jpegga_aylantir(rasm),
                    asosiy=(not bosh_rasm_bormi and i == 0),
                    tartib=mavjud + i
                )
                yaratilgan.append(obj)
        return Response(
            KvartiraRasmSerializer(yaratilgan, many=True).data,
            status=status.HTTP_201_CREATED
        )


class RieltorKvartiraRasmDeleteView(LogRequestMixin, APIView):
    """Kvartira rasmini o'chirish."""
    log_action_name = 'RIELTOR KVARTIRA RASM O\'CHIRISH'
    permission_classes = [IsAdminOrActiveRieltor]

    @extend_schema(summary="Rieltor: kvartira rasmini o'chirish", responses={204: None}, tags=["Kvartira - Rieltor"])
    def delete(self, request, pk, rasm_id):
        rasm = get_object_or_404(
            KvartiraRasm, pk=rasm_id, kvartira__pk=pk,
            kvartira__qoshgan=request.user
        )
        rasm.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RieltorKvartiraRasmAsosiyView(LogRequestMixin, APIView):
    """Rasmni bosh (asosiy) rasm qilib belgilash."""
    log_action_name = 'RIELTOR KVARTIRA RASM ASOSIY'
    permission_classes = [IsAdminOrActiveRieltor]

    @extend_schema(summary="Rieltor: bosh rasmni belgilash", request=None, responses={200: KvartiraRasmSerializer}, tags=["Kvartira - Rieltor"])
    def patch(self, request, pk, rasm_id):
        rasm = get_object_or_404(
            KvartiraRasm, pk=rasm_id, kvartira__pk=pk,
            kvartira__qoshgan=request.user
        )
        KvartiraRasm.objects.filter(kvartira=rasm.kvartira).update(asosiy=False)
        rasm.asosiy = True
        rasm.save(update_fields=['asosiy'])
        return Response(KvartiraRasmSerializer(rasm).data)


class RieltorKvartiraPlanirovkaDeleteView(LogRequestMixin, APIView):
    """Planirovka rasmini o'chirish."""
    log_action_name = 'RIELTOR KVARTIRA PLANIROVKA O\'CHIRISH'
    permission_classes = [IsAdminOrActiveRieltor]

    @extend_schema(summary="Rieltor: planirovkani o'chirish", responses={204: None}, tags=["Kvartira - Rieltor"])
    def delete(self, request, pk, planirovka_id):
        planirovka = get_object_or_404(
            KvartiraPlanirovka, pk=planirovka_id, kvartira__pk=pk,
            kvartira__qoshgan=request.user
        )
        planirovka.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
