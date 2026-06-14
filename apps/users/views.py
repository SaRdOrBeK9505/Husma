from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from apps.ariza.models import Ariza
from apps.makler.models import MaklerProfil
from .models import CustomUser, OTPKode
from .otp_service import kode_generatsiya, otp_yuborish
from .serializers import (
    TelegramAuthSerializer,
    UserSerializer,
    RieltorLoginSerializer,
    RieltorOTPSorovSerializer,
    RieltorOTPVerifySerializer,
)
from .auth import verify_telegram_auth, parse_webapp_user, parse_webapp_user_dict


# ===== USER AUTH =====

class TelegramAuthView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Telegram orqali login",
        description="Telegram WebApp initData yuboriladi, JWT token qaytariladi",
        request=TelegramAuthSerializer,
        responses={
            200: OpenApiResponse(
                description="Muvaffaqiyatli login",
                examples=[OpenApiExample(
                    name="Success",
                    value={
                        "access": "eyJ...",
                        "refresh": "eyJ...",
                        "user": {
                            "id": 1,
                            "telegram_id": 123456789,
                            "full_name": "Ali Valiyev",
                            "telegram_username": "ali_uz",
                            "role": "user",
                        },
                        "is_new": True,
                    }
                )]
            ),
            400: OpenApiResponse(description="Noto'g'ri ma'lumot"),
            401: OpenApiResponse(description="Autentifikatsiya muvaffaqiyatsiz"),
        },
        tags=["Auth"],
    )
    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        init_data = serializer.validated_data['init_data']

        try:
            parsed = parse_webapp_user(init_data)
        except Exception:
            return Response(
                {'error': "initData noto'g'ri formatda"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not verify_telegram_auth(parsed):
            return Response(
                {'error': 'Telegram autentifikatsiya muvaffaqiyatsiz'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verify o'tdi — endi 'user' ni dict ko'rinishida olamiz
        parsed = parse_webapp_user_dict(init_data)
        tg_user = parsed.get('user', {})
        telegram_id = tg_user.get('id')

        if not telegram_id:
            return Response(
                {'error': 'Telegram ID topilmadi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, created = CustomUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'telegram_username': tg_user.get('username'),
                'full_name': f"{tg_user.get('first_name', '')} {tg_user.get('last_name', '')}".strip(),
            }
        )

        if not created:
            user.telegram_username = tg_user.get('username', user.telegram_username)
            user.full_name = (
                f"{tg_user.get('first_name', '')} {tg_user.get('last_name', '')}".strip()
                or user.full_name
            )
            user.save(update_fields=['telegram_username', 'full_name'])

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'is_new': created,
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="O'z profilini ko'rish",
        responses={200: UserSerializer},
        tags=["Users"],
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        summary="Profilni yangilash",
        request=UserSerializer,
        responses={200: UserSerializer},
        tags=["Users"],
    )
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StatistikaView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Umumiy statistika",
        description="Bosh sahifadagi statistika ma'lumotlari",
        responses={
            200: OpenApiResponse(
                description="Statistika",
                examples=[OpenApiExample(
                    name="Success",
                    value={
                        "jami_bitimlar": 500,
                        "jami_rieltorlar": 50,
                        "javob_vaqti": "2s",
                    }
                )]
            )
        },
        tags=["Statistika"],
    )
    def get(self, request):
        return Response({
            "jami_bitimlar": Ariza.objects.filter(holat='yopilgan').count(),
            "jami_rieltorlar": MaklerProfil.objects.filter(verify_holat='verified').count(),
            "javob_vaqti": "2s",
        })


# ===== RIELTOR AUTH =====

class RieltorLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Rieltor kirish",
        description="Username va parol bilan kirish.",
        request=RieltorLoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Muvaffaqiyatli kirish",
                examples=[OpenApiExample(
                    name="Success",
                    value={
                        "access": "eyJ...",
                        "refresh": "eyJ...",
                        "rieltor": {
                            "id": 1,
                            "username": "ali_rieltor",
                            "full_name": "Ali Valiyev",
                            "faol": True,
                            "bepul_muddat_tugash": "2026-06-11T10:00:00Z",
                        }
                    }
                )]
            ),
            401: OpenApiResponse(description="Username yoki parol noto'g'ri"),
            403: OpenApiResponse(description="Rieltor profil topilmadi"),
        },
        tags=["Auth"],
    )
    def post(self, request):
        serializer = RieltorLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': "Username yoki parol noto'g'ri"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'error': "Username yoki parol noto'g'ri"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.role != CustomUser.Role.MAKLER:
            return Response(
                {'error': "Bu kirish faqat rieltorlar uchun"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            rieltor = user.rieltor_profil
        except MaklerProfil.DoesNotExist:
            return Response(
                {'error': "Rieltor profil topilmadi"},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "rieltor": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "faol": rieltor.faol,
                "bepul_muddat_tugash": rieltor.bepul_muddat_tugash,
                "bio": rieltor.bio,
                "telegram_link": rieltor.telegram_link,
            }
        }, status=status.HTTP_200_OK)


class RieltorFaollikView(APIView):
    """Rieltor bepul muddat yoki obuna holatini tekshiradi."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Rieltor faollik holatini tekshirish",
        responses={
            200: OpenApiResponse(
                description="Faollik holat",
                examples=[OpenApiExample(
                    name="Faol",
                    value={
                        "faol": True,
                        "bepul_muddat_tugash": "2026-06-11T10:00:00Z",
                        "obuna_faol": False,
                        "message": "Bepul sinov muddati davom etmoqda."
                    }
                ), OpenApiExample(
                    name="Tugagan",
                    value={
                        "faol": False,
                        "bepul_muddat_tugash": "2026-05-01T10:00:00Z",
                        "obuna_faol": False,
                        "message": "Bepul sinov muddati tugagan. Obuna oling."
                    }
                )]
            ),
            403: OpenApiResponse(description="Rieltor profil topilmadi"),
        },
        tags=["Auth"],
    )
    def get(self, request):
        try:
            rieltor = request.user.rieltor_profil
        except MaklerProfil.DoesNotExist:
            return Response(
                {'error': "Rieltor profil topilmadi"},
                status=status.HTTP_403_FORBIDDEN
            )

        if rieltor.faol:
            message = "Obunangiz faol." if rieltor.obuna_faol else "Bepul sinov muddati davom etmoqda."
        else:
            message = "Bepul sinov muddati tugagan. Obuna oling."

        return Response({
            "faol": rieltor.faol,
            "bepul_muddat_tugash": rieltor.bepul_muddat_tugash,
            "obuna_faol": rieltor.obuna_faol,
            "obuna_tugash": rieltor.obuna_tugash,
            "message": message,
        })


# ===== OTP ORQALI RIELTOR REGISTER =====

class RieltorOTPSorovView(APIView):
    """
    Rieltor register — 1-qadam.
    Telegram auth o'tgan user JWT bilan murojaat qiladi.
    telegram_id request.user dan olinadi.
    Telegramga 6 xonali OTP kodi yuboriladi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Rieltor OTP so'rovi (1-qadam)",
        description=(
            "Telegram auth o'tgan user rieltor bo'lmoqchi bo'lganda chaqiradi. "
            "Body: full_name, phone, username, password, hududlar, mulk_turlari. "
            "Hududlar va mulk turlari majburiy (kamida bittadan). "
            "Telegramga 6 xonali tasdiqlash kodi yuboriladi (5 daqiqa amal qiladi)."
        ),
        request=RieltorOTPSorovSerializer,
        responses={
            200: OpenApiResponse(
                description="Kode yuborildi",
                examples=[OpenApiExample(
                    name="Success",
                    value={"message": "Tasdiqlash kodi Telegramingizga yuborildi"}
                )]
            ),
            400: OpenApiResponse(description="Validatsiya xatosi yoki allaqachon rieltor"),
            403: OpenApiResponse(description="Telegram ID topilmadi"),
            503: OpenApiResponse(description="Telegram xabar yuborilmadi"),
        },
        tags=["Auth"],
    )
    def post(self, request):
        telegram_id = request.user.telegram_id
        if not telegram_id:
            return Response(
                {'error': "Akkauntingizda Telegram ID topilmadi. Telegram orqali kiring."},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.user.role == CustomUser.Role.MAKLER:
            return Response(
                {'error': "Siz allaqachon rieltor rolidasisiz."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RieltorOTPSorovSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Avvalgi kodlarni o'chirib tashlaymiz
        OTPKode.objects.filter(telegram_id=telegram_id).delete()

        kode = kode_generatsiya()
        otp = OTPKode.objects.create(
            telegram_id=telegram_id,
            kode=kode,
            register_data={
                'full_name': data['full_name'],
                'phone': data['phone'],
                'username': data['username'],
                'password': data['password'],
                'hududlar': [h.id for h in data['hududlar']],
                'mulk_turlari': [m.id for m in data['mulk_turlari']],
            }
        )

        yuborildi = otp_yuborish(otp)
        if not yuborildi:
            otp.delete()
            return Response(
                {'error': "Telegram ga xabar yuborib bo'lmadi. Bot bilan /start qilganingizni tekshiring."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response({
            "message": "Tasdiqlash kodi Telegramingizga yuborildi",
        }, status=status.HTTP_200_OK)


class RieltorOTPVerifyView(APIView):
    """
    Rieltor register — 2-qadam.
    Telegram auth o'tgan user JWT bilan kode yuboradi.
    To'g'ri bo'lsa user makler roliga o'tadi, MaklerProfil yaratiladi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Rieltor OTP tasdiqlash (2-qadam)",
        description=(
            "Telegramga kelgan 6 xonali kode yuboriladi. "
            "Muvaffaqiyatli bo'lsa rieltor yaratiladi, 7 kunlik bepul muddat boshlanadi."
        ),
        request=RieltorOTPVerifySerializer,
        responses={
            201: OpenApiResponse(
                description="Rieltor yaratildi",
                examples=[OpenApiExample(
                    name="Success",
                    value={
                        "message": "Ro'yxatdan o'tdingiz. 7 kunlik bepul sinov muddati boshlandi.",
                        "access": "eyJ...",
                        "refresh": "eyJ...",
                        "rieltor": {
                            "id": 1,
                            "username": "ali_rieltor",
                            "full_name": "Ali Valiyev",
                            "faol": True,
                            "bepul_muddat_tugash": "2026-06-11T10:00:00Z",
                        }
                    }
                )]
            ),
            400: OpenApiResponse(description="Noto'g'ri yoki muddati o'tgan kod"),
            403: OpenApiResponse(description="Telegram ID topilmadi"),
        },
        tags=["Auth"],
    )
    def post(self, request):
        telegram_id = request.user.telegram_id
        if not telegram_id:
            return Response(
                {'error': "Akkauntingizda Telegram ID topilmadi. Telegram orqali kiring."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RieltorOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        kode = serializer.validated_data['kode']

        try:
            otp = OTPKode.objects.get(telegram_id=telegram_id, kode=kode)
        except OTPKode.DoesNotExist:
            return Response(
                {'error': "Kod noto'g'ri yoki topilmadi"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.muddati_otganmi:
            otp.delete()
            return Response(
                {'error': "Kod muddati o'tgan. Qaytadan boshlang."},
                status=status.HTTP_400_BAD_REQUEST
            )

        reg = otp.register_data

        # request.user ni yangilaymiz
        user = request.user
        user.full_name = reg['full_name']
        user.phone = reg['phone']
        user.username = reg['username']
        user.role = CustomUser.Role.MAKLER
        user.set_password(reg['password'])
        user.save()

        # Rieltor profil — 7 kunlik bepul muddat bilan
        bepul_muddat = timezone.now() + timedelta(days=7)

        rieltor, created = MaklerProfil.objects.get_or_create(
            user=user,
            defaults={
                'verify_holat': MaklerProfil.VerifyHolat.VERIFIED,
                'bepul_muddat_tugash': bepul_muddat,
            }
        )
        if not created:
            rieltor.verify_holat = MaklerProfil.VerifyHolat.VERIFIED
            rieltor.bepul_muddat_tugash = bepul_muddat
            rieltor.save(update_fields=['verify_holat', 'bepul_muddat_tugash'])

        # Registratsiyada tanlangan hudud va mulk turlarini bog'laymiz
        hududlar = reg.get('hududlar', [])
        mulk_turlari = reg.get('mulk_turlari', [])
        if hududlar:
            rieltor.hududlar.set(hududlar)
        if mulk_turlari:
            rieltor.mulk_turlari.set(mulk_turlari)

        otp.delete()

        # Role o'zgargani uchun yangi JWT
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Ro'yxatdan o'tdingiz. 7 kunlik bepul sinov muddati boshlandi.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "rieltor": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "faol": rieltor.faol,
                "bepul_muddat_tugash": rieltor.bepul_muddat_tugash,
            }
        }, status=status.HTTP_201_CREATED)
