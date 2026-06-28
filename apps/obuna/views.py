from rest_framework.generics import (
    ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    extend_schema, OpenApiResponse, OpenApiParameter, inline_serializer,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as drf_serializers

from core.permissions import IsRieltor, IsAdmin
from apps.makler.models import MaklerProfil
from .models import Tarif, Obuna, Tolov
from .serializers import (
    TarifSerializer,
    TarifRieltorSerializer,
    TarifAdminSerializer,
    ObunaSerializer,
    ObunaAdminSerializer,
    ObunaYaratishSerializer,
    AdminObunaBerishSerializer,
    TolovAdminSerializer,
)
from .payme.checkout import payme_checkout_url
from .multicard.client import MulticardClient, MulticardError

import logging
_log = logging.getLogger('multicard')


# ============================================================
#  PUBLIC / RIELTOR — Tariflar va obuna sotib olish
# ============================================================

class TarifListView(ListAPIView):
    """
    Mavjud obuna tariflari ro'yxati — hammaga ochiq.
    Agar rieltor login qilgan bo'lsa, unga mos tarifni qaytaradi
    (birinchi obuna bo'lsa - aktsiya narxi, aks holda - oddiy narxi).
    """
    serializer_class = TarifSerializer
    permission_classes = [IsRieltor]
    pagination_class = None

    @extend_schema(
        summary="Obuna tariflari ro'yxati (public)",
        responses={200: TarifSerializer(many=True)},
        tags=["Obuna"],
    )
    def get(self, request, *args, **kwargs):
        # Agar rieltor login qilgan bo'lsa, unga mos tarifni qaytaramiz
        if request.user.is_authenticated and hasattr(request.user, 'rieltor_profil'):
            rieltor = request.user.rieltor_profil
            
            # Rieltorning muvaffaqiyatli obunasi bormi? (FAOL yoki TUGAGAN)
            # BEKOR va KUTILMOQDA holatlari hisobga olinmaydi - ular muvaffaqiyatsiz
            muvaffaqiyatli_obunalar = rieltor.obunalar.filter(
                holat__in=[Obuna.Holat.FAOL, Obuna.Holat.TUGAGAN]
            )
            muvaffaqiyatli_obuna_bormi = muvaffaqiyatli_obunalar.exists()
            
            # Debug log
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Rieltor: {rieltor.user.telegram_id}, Obunalar soni: {rieltor.obunalar.count()}, Muvaffaqiyatli: {muvaffaqiyatli_obuna_bormi}")
            for obuna in rieltor.obunalar.all():
                logger.info(f"Obuna: id={obuna.id}, holat={obuna.holat}, narx={obuna.narx}")
            
            # Agar muvaffaqiyatli obuna bo'lmagan bo'lsa - birinchi oy tarifini taklif qilamiz
            if not muvaffaqiyatli_obuna_bormi:
                tarif = Tarif.objects.filter(
                    kod='birinchi_oy',
                    is_active=True
                ).first()
                if tarif:
                    serializer = TarifRieltorSerializer(tarif)
                    data = serializer.data
                    data['birinchi_oy_bormi'] = True
                    return Response([data])
            
            # Aks holda (kamida bitta muvaffaqiyatli obuna sotib olgan) - oddiy oylik tarifini taklif qilamiz
            tarif = Tarif.objects.filter(
                kod='oylik',
                is_active=True
            ).first()
            if tarif:
                serializer = TarifRieltorSerializer(tarif)
                data = serializer.data
                data['birinchi_oy_bormi'] = False
                return Response([data])
        
        # Login qilmagan yoki rieltor bo'lmagan bo'lsa - barcha tariflarni qaytaramiz
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Tarif.objects.filter(is_active=True)


class MeningObunamView(APIView):
    """Rieltor o'z obuna holatini va tarixini ko'radi."""
    permission_classes = [IsRieltor]

    @extend_schema(
        summary="Mening obunam (holat + tarix)",
        responses={
            200: inline_serializer(
                name='MeningObunamResponse',
                fields={
                    'faol': drf_serializers.BooleanField(),
                    'obuna_faol': drf_serializers.BooleanField(),
                    'bepul_muddat_tugash': drf_serializers.DateTimeField(allow_null=True),
                    'joriy_obuna': ObunaSerializer(allow_null=True),
                    'tarix': ObunaSerializer(many=True),
                }
            )
        },
        tags=["Obuna"],
    )
    def get(self, request):
        rieltor = request.user.rieltor_profil

        # Ikki marta so'rov o'rniga bir marta barcha obunalarni yuklaymiz,
        # keyin Python da faolini topamiz (DB ga qo'shimcha so'rov ketmaydi).
        tarix = list(
            rieltor.obunalar.all()
            .select_related('tarif')
            .prefetch_related('tolovlar')
        )
        from django.utils import timezone as tz
        joriy = next(
            (
                o for o in tarix
                if o.holat == 'faol' and o.tugash_vaqti and tz.now() < o.tugash_vaqti
            ),
            None
        )

        return Response({
            "faol": rieltor.faol,
            "obuna_faol": rieltor.obuna_faol,
            "bepul_muddat_tugash": rieltor.bepul_muddat_tugash,
            "joriy_obuna": ObunaSerializer(joriy).data if joriy else None,
            "tarix": ObunaSerializer(tarix, many=True).data,
        })


class ObunaTarixView(ListAPIView):
    """Rieltor o'z obunalari ro'yxatini (paginatsiya bilan) ko'radi."""
    permission_classes = [IsRieltor]
    serializer_class = ObunaSerializer
    queryset = Obuna.objects.none()

    @extend_schema(
        summary="Mening obunalarim tarixi (ro'yxat)",
        responses={200: ObunaSerializer(many=True)},
        tags=["Obuna"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Obuna.objects.none()
        return self.request.user.rieltor_profil.obunalar.all().select_related(
            'tarif'
        ).prefetch_related('tolovlar')


class ObunaSotibOlishView(APIView):
    """
    Rieltor obuna sotib olishni boshlaydi.

    Obuna (kutilmoqda) + Tolov (kutilmoqda) yaratiladi.
    Payme tanlansa to'lov havolasi (tolov_url) qaytariladi.
    
    MUHIM: Agar tarif_id ko'rsatilmagan bo'lsa, avtomatik mos tarifni tanlaydi:
    - Birinchi obuna bo'lsa - birinchi_oy (99,000 so'm)
    - Aks holda - oylik (199,000 so'm)
    """
    permission_classes = [IsRieltor]

    @extend_schema(
        summary="Obuna sotib olish (to'lovni boshlash)",
        request=ObunaYaratishSerializer,
        responses={
            201: inline_serializer(
                name='ObunaSotibOlishResponse',
                fields={
                    'message': drf_serializers.CharField(),
                    'obuna_id': drf_serializers.IntegerField(),
                    'tolov_id': drf_serializers.IntegerField(),
                    'summa': drf_serializers.IntegerField(),
                    'provayder': drf_serializers.CharField(),
                    'tolov_url': drf_serializers.CharField(required=False),
                    'birinchi_oy_bormi': drf_serializers.BooleanField(),
                }
            ),
            400: OpenApiResponse(description="Validatsiya xatosi"),
        },
        tags=["Obuna"],
    )
    def post(self, request):
        serializer = ObunaYaratishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tarif    = serializer.context.get('tarif')
        provayder = serializer.validated_data['provayder']
        rieltor  = request.user.rieltor_profil
        
        # Agar tarif ko'rsatilmagan bo'lsa, avtomatik mos tarifni tanlaymiz
        if not tarif:
            # Rieltorning muvaffaqiyatli obunasi bormi? (FAOL yoki TUGAGAN)
            # BEKOR va KUTILMOQDA holatlari hisobga olinmaydi - ular muvaffaqiyatsiz
            muvaffaqiyatli_obuna_bormi = rieltor.obunalar.filter(
                holat__in=[Obuna.Holat.FAOL, Obuna.Holat.TUGAGAN]
            ).exists()
            
            # Agar muvaffaqiyatli obuna bo'lmagan bo'lsa - birinchi oy tarifini
            if not muvaffaqiyatli_obuna_bormi:
                tarif = Tarif.objects.filter(
                    kod='birinchi_oy',
                    is_active=True
                ).first()
            else:
                # Aks holda (kamida bitta muvaffaqiyatli obuna sotib olgan) - oddiy oylik tarifini
                tarif = Tarif.objects.filter(
                    kod='oylik',
                    is_active=True
                ).first()
            
            if not tarif:
                return Response(
                    {"error": "Mos tarif topilmadi"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        with transaction.atomic():
            obuna = Obuna.objects.create(
                rieltor=rieltor,
                tarif=tarif,
                narx=tarif.narx,
                holat=Obuna.Holat.KUTILMOQDA,
            )
            tolov = Tolov.objects.create(
                obuna=obuna,
                provayder=provayder,
                summa=tarif.narx,
                holat=Tolov.Holat.KUTILMOQDA,
            )

        birinchi_oy_bormi = (tarif.kod == 'birinchi_oy')
        
        javob = {
            "message": "Obuna yaratildi. To'lovni amalga oshiring.",
            "obuna_id": obuna.id,
            "tolov_id": tolov.id,
            "summa": tolov.summa,
            "provayder": provayder,
            "birinchi_oy_bormi": birinchi_oy_bormi,
        }

        # ----- PAYME -----
        if provayder == Tolov.Provayder.PAYME:
            javob["tolov_url"] = payme_checkout_url(
                obuna_id=obuna.id,
                amount_som=tarif.narx,
            )

        # ----- MULTICARD -----
        elif provayder == Tolov.Provayder.MULTICARD:
            try:
                client = MulticardClient()
                result = client.create_invoice(
                    obuna_id=obuna.id,
                    amount_som=tarif.narx,
                )
                # Invoice uuid ni Tolov ga saqlaymiz (callback da shu bo'yicha qidiramiz)
                tolov.tashqi_id = result["uuid"]
                tolov.metadata = result
                tolov.save(update_fields=["tashqi_id", "metadata", "updated_at"])
                javob["tolov_url"] = result["checkout_url"]

            except MulticardError as exc:
                _log.error(
                    "[Multicard] Invoice yaratishda xato: obuna_id=%s err=%s",
                    obuna.id, exc,
                )
                # Yaratilgan Obuna va Tolov ni tozalaymiz
                with transaction.atomic():
                    tolov.delete()
                    obuna.delete()
                return Response(
                    {
                        "error": "Multicard bilan bog'lanishda xato. "
                                 "Keyinroq qayta urinib ko'ring.",
                        "detail": str(exc),
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return Response(javob, status=status.HTTP_201_CREATED)


class ObunaBekorView(APIView):
    """Rieltor hali to'lanmagan (kutilmoqda) obunani bekor qiladi."""
    permission_classes = [IsRieltor]

    @extend_schema(
        summary="Obunani bekor qilish (faqat to'lanmagan)",
        request=None,
        responses={
            200: OpenApiResponse(description="Bekor qilindi"),
            400: OpenApiResponse(description="Bu obunani bekor qilib bo'lmaydi"),
            404: OpenApiResponse(description="Obuna topilmadi"),
        },
        tags=["Obuna"],
    )
    def post(self, request, pk):
        rieltor = request.user.rieltor_profil
        obuna = get_object_or_404(Obuna, pk=pk, rieltor=rieltor)

        if obuna.holat != Obuna.Holat.KUTILMOQDA:
            return Response(
                {'error': "Faqat to'lov kutilayotgan obunani bekor qilish mumkin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obuna.holat = Obuna.Holat.BEKOR
        obuna.save(update_fields=['holat', 'updated_at'])
        obuna.tolovlar.filter(holat=Tolov.Holat.KUTILMOQDA).update(
            holat=Tolov.Holat.BEKOR
        )
        return Response({"message": "Obuna bekor qilindi"})


# ============================================================
#  ADMIN — Tarif CRUD, obuna boshqaruvi, to'lovlar
# ============================================================

class AdminTarifListCreateView(ListCreateAPIView):
    """Admin: tariflar ro'yxati + yangi tarif yaratish."""
    permission_classes = [IsAdmin]
    serializer_class = TarifAdminSerializer
    queryset = Tarif.objects.all()
    pagination_class = None

    @extend_schema(summary="Tariflar ro'yxati (Admin)", tags=["Admin: Obuna"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Yangi tarif yaratish (Admin)", tags=["Admin: Obuna"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminTarifDetailView(RetrieveUpdateDestroyAPIView):
    """Admin: bitta tarifni ko'rish / tahrirlash / o'chirish."""
    permission_classes = [IsAdmin]
    serializer_class = TarifAdminSerializer
    queryset = Tarif.objects.all()

    @extend_schema(summary="Tarifni ko'rish (Admin)", tags=["Admin: Obuna"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Tarifni to'liq yangilash (Admin)", tags=["Admin: Obuna"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(summary="Tarifni qisman yangilash (Admin)", tags=["Admin: Obuna"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(summary="Tarifni o'chirish (Admin)", tags=["Admin: Obuna"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AdminObunaListView(ListAPIView):
    """Admin: barcha obunalar ro'yxati (holat bo'yicha filter)."""
    permission_classes = [IsAdmin]
    serializer_class = ObunaAdminSerializer
    queryset = Obuna.objects.none()

    @extend_schema(
        summary="Barcha obunalar (Admin)",
        parameters=[
            OpenApiParameter(
                name='holat', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter: kutilmoqda | faol | tugagan | bekor",
                required=False,
                enum=['kutilmoqda', 'faol', 'tugagan', 'bekor'],
            )
        ],
        responses={200: ObunaAdminSerializer(many=True)},
        tags=["Admin: Obuna"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Obuna.objects.none()
        qs = Obuna.objects.select_related(
            'tarif', 'rieltor__user'
        ).prefetch_related('tolovlar')
        holat = self.request.query_params.get('holat')
        if holat in ['kutilmoqda', 'faol', 'tugagan', 'bekor']:
            qs = qs.filter(holat=holat)
        return qs


class AdminObunaDetailView(RetrieveUpdateDestroyAPIView):
    """Admin: bitta obunani ko'rish / tahrirlash / o'chirish."""
    permission_classes = [IsAdmin]
    serializer_class = ObunaAdminSerializer
    queryset = Obuna.objects.select_related('tarif', 'rieltor__user').prefetch_related('tolovlar')

    @extend_schema(summary="Obunani ko'rish (Admin)", tags=["Admin: Obuna"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Obunani qisman yangilash (Admin)", tags=["Admin: Obuna"])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(summary="Obunani to'liq yangilash (Admin)", tags=["Admin: Obuna"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(summary="Obunani o'chirish (Admin)", tags=["Admin: Obuna"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AdminObunaBerishView(APIView):
    """
    Admin rieltorga qo'lda obuna beradi (to'lovsiz — bonus/aksiya).
    Obuna darhol faollashtiriladi (qo'lda manual to'lov bilan).
    """
    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Rieltorga qo'lda obuna berish (Admin)",
        request=AdminObunaBerishSerializer,
        responses={201: ObunaAdminSerializer},
        tags=["Admin: Obuna"],
    )
    def post(self, request):
        serializer = AdminObunaBerishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rieltor = serializer.context['rieltor']
        tarif = serializer.context['tarif']

        with transaction.atomic():
            obuna = Obuna.objects.create(
                rieltor=rieltor,
                tarif=tarif,
                narx=tarif.narx,
                holat=Obuna.Holat.KUTILMOQDA,
            )
            tolov = Tolov.objects.create(
                obuna=obuna,
                provayder=Tolov.Provayder.MANUAL,
                summa=tarif.narx,
                holat=Tolov.Holat.KUTILMOQDA,
            )
            # To'lovni tasdiqlash → obuna avtomatik faollashadi
            tolov.muvaffaqiyatli_deb_belgilash()

        obuna.refresh_from_db()
        return Response(
            ObunaAdminSerializer(obuna).data,
            status=status.HTTP_201_CREATED,
        )


class AdminTolovListView(ListAPIView):
    """Admin: barcha to'lovlar ro'yxati (provayder/holat bo'yicha filter)."""
    permission_classes = [IsAdmin]
    serializer_class = TolovAdminSerializer
    queryset = Tolov.objects.none()

    @extend_schema(
        summary="Barcha to'lovlar (Admin)",
        parameters=[
            OpenApiParameter(
                name='provayder', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter: payme | click | manual", required=False,
                enum=['payme', 'click', 'manual'],
            ),
            OpenApiParameter(
                name='holat', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter: kutilmoqda | muvaffaqiyatli | bekor | xato",
                required=False,
                enum=['kutilmoqda', 'muvaffaqiyatli', 'bekor', 'xato'],
            ),
        ],
        responses={200: TolovAdminSerializer(many=True)},
        tags=["Admin: Obuna"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Tolov.objects.none()
        qs = Tolov.objects.select_related('obuna__rieltor__user')
        provayder = self.request.query_params.get('provayder')
        holat = self.request.query_params.get('holat')
        if provayder in ['payme', 'click', 'manual']:
            qs = qs.filter(provayder=provayder)
        if holat in ['kutilmoqda', 'muvaffaqiyatli', 'bekor', 'xato']:
            qs = qs.filter(holat=holat)
        return qs


class AdminTolovTasdiqlashView(APIView):
    """
    Admin to'lovni qo'lda tasdiqlaydi (masalan bank o'tkazmasi).
    To'lov → muvaffaqiyatli, obuna → faol.
    """
    permission_classes = [IsAdmin]

    @extend_schema(
        summary="To'lovni qo'lda tasdiqlash (Admin)",
        request=None,
        responses={
            200: OpenApiResponse(description="Tasdiqlandi va obuna faollashtirildi"),
            400: OpenApiResponse(description="To'lov allaqachon qayta ishlangan"),
            404: OpenApiResponse(description="To'lov topilmadi"),
        },
        tags=["Admin: Obuna"],
    )
    def post(self, request, pk):
        tolov = get_object_or_404(Tolov, pk=pk)

        if tolov.holat != Tolov.Holat.KUTILMOQDA:
            return Response(
                {'error': f"To'lov allaqachon '{tolov.get_holat_display()}' holatida"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tolov.muvaffaqiyatli_deb_belgilash()
        return Response({
            "message": "To'lov tasdiqlandi, obuna faollashtirildi",
            "obuna_id": tolov.obuna_id,
        })
