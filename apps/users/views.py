from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from apps.ariza.models import Ariza
from apps.makler.models import MaklerProfil
from apps.hudud.models import Hudud
from .models import CustomUser
from .serializers import (
    TelegramAuthSerializer,
    UserSerializer,
    RieltorRoliSorovSerializer,
    RieltorRegisterSerializer,
    RieltorLoginSerializer,
    RieltorProfileResponseSerializer,
)
from .auth import verify_telegram_auth, parse_webapp_user


class TelegramAuthView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Telegram orqali login",
        description="Telegram WebApp initData yuboriladi, JWT token qaytariladi",
        request=TelegramAuthSerializer,
        responses={
            200: OpenApiResponse(
                description="Muvaffaqiyatli login",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={
                            "access": "eyJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiJ9...",
                            "user": {
                                "id": 1,
                                "telegram_id": 123456789,
                                "full_name": "Ali Valiyev",
                                "telegram_username": "ali_uz",
                                "role": "user",
                            },
                            "is_new": True,
                        }
                    )
                ]
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
                {'error': 'initData noto\'g\'ri formatda'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not verify_telegram_auth(parsed):
            return Response(
                {'error': 'Telegram autentifikatsiya muvaffaqiyatsiz'},
                status=status.HTTP_401_UNAUTHORIZED
            )

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
        serializer = UserSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RieltorRoliSorovView(APIView):
    """
    User rieltor bo'lmoqchi bo'lsa shu endpoint orqali so'rov yuboradi.
    Admin verify qilgunicha 'pending' holatda turadi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Rieltor bo'lish uchun so'rov",
        description="""
        User rieltor bo'lmoqchi bo'lsa shu endpoint ga murojaat qiladi.
        - Role 'makler' ga o'zgaradi
        - RieltorProfil yaratiladi (pending holatda)
        - Admin verify qilgunicha arizalar ko'rinmaydi
        """,
        request=RieltorRoliSorovSerializer,
        responses={
            200: OpenApiResponse(description="So'rov yuborildi"),
            400: OpenApiResponse(description="Allaqachon rieltor"),
        },
        tags=["Auth"],
    )
    def post(self, request):
        if request.user.role == 'makler':
            return Response(
                {'error': 'Siz allaqachon rieltor rolidasisiz'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RieltorRoliSorovSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        hududlar_ids = data.get('hududlar', [])

        hududlar = Hudud.objects.filter(
            id__in=hududlar_ids,
            is_active=True
        )
        if hududlar.count() != len(hududlar_ids):
            return Response(
                {'error': 'Bir yoki bir nechta hudud topilmadi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.role = 'makler'
        request.user.save(update_fields=['role'])

        rieltor_profil, created = MaklerProfil.objects.get_or_create(
            user=request.user,
            defaults={
                'bio': data.get('bio', ''),
                'telegram_link': data.get('telegram_link', ''),
            }
        )

        if not created:
            rieltor_profil.bio = data.get('bio', rieltor_profil.bio)
            rieltor_profil.telegram_link = data.get('telegram_link', rieltor_profil.telegram_link)
            rieltor_profil.save(update_fields=['bio', 'telegram_link'])

        rieltor_profil.hududlar.set(hududlar)

        return Response({
            'message': 'So\'rovingiz qabul qilindi. Admin tasdiqlashini kuting.',
            'verify_holat': rieltor_profil.verify_holat,
            'hududlar': [h.nomi for h in hududlar],
        }, status=status.HTTP_200_OK)


class StatistikaView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Umumiy statistika",
        description="Bosh sahifadagi statistika ma'lumotlari",
        responses={
            200: OpenApiResponse(
                description="Statistika",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={
                            "jami_bitimlar": 500,
                            "jami_rieltorlar": 50,
                            "javob_vaqti": "2s",
                        }
                    )
                ]
            )
        },
        tags=["Statistika"],
    )
    def get(self, request):
        data = {
            "jami_bitimlar": Ariza.objects.filter(holat='yopilgan').count(),
            "jami_rieltorlar": MaklerProfil.objects.filter(
                verify_holat='verified'
            ).count(),
            "javob_vaqti": "2s",
        }
        return Response(data)


# ===== RIELTOR USERNAME/PAROL AUTH =====

class RieltorRegisterView(APIView):
    """
    Rieltor ro'yxatdan o'tish.
    Username + parol bilan — Telegram'ga bog'liq emas.
    Ro'yxatdan o'tgach admin verify qilgunicha 'pending' holatda turadi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Rieltor ro'yxatdan o'tish",
        description=(
            "Yangi rieltor ro'yxatdan o'tadi. "
            "Yaratilgach `verify_holat='pending'` bo'ladi. "
            "Admin `verified` qilgunicha arizalar ko'rinmaydi."
        ),
        request=RieltorRegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Muvaffaqiyatli ro'yxatdan o'tildi",
                examples=[OpenApiExample(
                    name="Success",
                    value={
                        "message": "Ro'yxatdan o'tdingiz. Admin tasdiqlashini kuting.",
                        "access": "eyJ...",
                        "refresh": "eyJ...",
                        "rieltor": {
                            "id": 1,
                            "username": "ali_rieltor",
                            "full_name": "Ali Valiyev",
                            "verify_holat": "pending",
                        }
                    }
                )]
            ),
            400: OpenApiResponse(description="Validatsiya xatosi"),
        },
        tags=["Auth"],
    )
    def post(self, request):
        serializer = RieltorRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # User yaratish — to'g'ridan create() emas, to'liq nazorat uchun
        user = CustomUser(
            username=data['username'],
            full_name=data['full_name'],
            phone=data.get('phone') or '',
            role=CustomUser.Role.MAKLER,
        )
        user.set_password(data['password'])
        user.save()

        # Rieltor profil yaratish (pending)
        rieltor = MaklerProfil.objects.create(
            user=user,
            bio=data.get('bio', ''),
            telegram_link=data.get('telegram_link', ''),
            verify_holat=MaklerProfil.VerifyHolat.PENDING,
        )

        # Hududlarni bog'lash
        hududlar = Hudud.objects.filter(id__in=data['hududlar'], is_active=True)
        rieltor.hududlar.set(hududlar)

        # JWT token
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Ro'yxatdan o'tdingiz. Admin tasdiqlashini kuting.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "rieltor": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "verify_holat": rieltor.verify_holat,
                "bio": rieltor.bio,
                "telegram_link": rieltor.telegram_link,
            }
        }, status=status.HTTP_201_CREATED)


class RieltorLoginView(APIView):
    """
    Rieltor login — username + parol.
    verify_holat har doim response da qaytariladi,
    frontend shunga qarab yo panelni ko'rsatadi, yo 'kutish' ekranini.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Rieltor kirish",
        description=(
            "Username va parol bilan kirish. "
            "`verify_holat` ni tekshiring: "
            "`verified` → panel, `pending` → kutish ekrani, `rejected` → rad etildi."
        ),
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
                            "verify_holat": "verified",
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

        # Django authenticate — USERNAME_FIELD = telegram_id bo'lgani uchun
        # to'g'ridan-to'g'ri user ni topamiz
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
                "verify_holat": rieltor.verify_holat,
                "bio": rieltor.bio,
                "telegram_link": rieltor.telegram_link,
            }
        }, status=status.HTTP_200_OK)


class RieltorVerifyHolatView(APIView):
    """
    Rieltor o'z verify holatini tekshiradi.
    Frontend polling yoki sahifa ochilganda tekshirish uchun.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Rieltor verify holatini tekshirish",
        description="Pending rieltor admin tasdiqlashini kutayotganda shu endpoint ni so'raydi.",
        responses={
            200: OpenApiResponse(
                description="Verify holat",
                examples=[OpenApiExample(
                    name="Pending",
                    value={"verify_holat": "pending", "message": "Admin tasdiqlashini kuting"}
                ), OpenApiExample(
                    name="Verified",
                    value={"verify_holat": "verified", "message": "Tasdiqlandi! Panelga kirishingiz mumkin."}
                ), OpenApiExample(
                    name="Rejected",
                    value={"verify_holat": "rejected", "message": "Arizangiz rad etildi. Admin bilan bog'laning."}
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

        messages = {
            'pending': "Admin tasdiqlashini kuting",
            'verified': "Tasdiqlandi! Panelga kirishingiz mumkin.",
            'rejected': "Arizangiz rad etildi. Admin bilan bog'laning.",
        }

        return Response({
            "verify_holat": rieltor.verify_holat,
            "message": messages.get(rieltor.verify_holat, ""),
        })
