"""
Multicard Callback va Swagger test views.
===========================================
Rasmiy hujjat: https://docs.multicard.uz/callback-success-19729300e0

MUHIM (hujjatga ko'ra):
  - Multicard X-Signature header EMAS, balki body ichida "sign" maydoni yuboradi.
  - sign = MD5("{store_id}{invoice_id}{amount}{secret}")  — qiymatlar to'g'ridan-to'g'ri
    ulanadi, ajratuvchisiz.
  - So'rov 195.158.26.90 IP manzilidan keladi (qo'shimcha himoya sifatida tekshirish mumkin).
  - Javob HAR DOIM HTTP 200 bo'lishi kerak. Tanada {"success": true} yoki
    {"success": false, "message": "..."} qaytariladi.
  - Agar 200 dan boshqa status qaytarilsa YOKI success != true bo'lsa —
    Multicard to'lovni BEKOR qiladi va pulni qaytaradi. Shuning uchun xato holatlarida
    ham status=200 qaytarish va faqat success:false bilan bildirish kerak.
  - Bir xil "uuid" bilan qayta so'rov kelishi mumkin (timeout/500 holatida) —
    idempotentlik shart.

Ikkita endpoint:
  1. /obuna/multicard/callback/  — Multicard server-to-server POST (asosiy, MD5 bilan himoyalangan)
  2. /obuna/multicard/return/    — foydalanuvchi to'lovdan keyin qaytadigan GET (return_url)
"""
import hashlib
import hmac
import logging
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample
from .client import MulticardClient, MulticardError

from apps.obuna.models import Tolov, Obuna

logger = logging.getLogger("multicard")

# Multicard callback so'rovlari shu IP dan keladi (hujjatda ko'rsatilgan)
MULTICARD_CALLBACK_IP = "195.158.26.90"


def _calc_sign(store_id, invoice_id, amount, secret: str) -> str:
    """
    Hujjat formulasi: MD5({store_id}{invoice_id}{amount}{secret})
    Qiymatlar string sifatida, bo'shliqsiz va ajratuvchisiz ulanadi.
    """
    raw = f"{store_id}{invoice_id}{amount}{secret}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _verify_callback_signature(data: dict) -> bool:
    secret = getattr(settings, "MULTICARD_SECRET", "")
    if not secret:
        logger.error(
            "[Multicard] MULTICARD_SECRET sozlanmagan! "
            "Imzo tekshirib bo'lmaydi — so'rov rad etiladi."
        )
        return False

    expected = _calc_sign(
        data.get("store_id"),
        data.get("invoice_id"),
        data.get("amount"),
        secret,
    )
    received = str(data.get("sign", ""))
    is_valid = hmac.compare_digest(expected, received)

    if not is_valid:
        logger.warning(
            "[Multicard] Noto'g'ri sign! Kelgan=%s Kutilgan=%s store_id=%s invoice_id=%s amount=%s",
            received, expected, data.get("store_id"), data.get("invoice_id"), data.get("amount"),
        )
    return is_valid


def _is_trusted_ip(request) -> bool:
    """
    Qo'shimcha himoya qatlami (asosiy himoya — sign tekshiruvi).
    Productionda Nginx ortida bo'lsa X-Forwarded-For to'g'ri kelishini tekshiring.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    remote = request.META.get("REMOTE_ADDR", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else remote
    return client_ip == MULTICARD_CALLBACK_IP


CALLBACK_REQUEST_EXAMPLE = OpenApiExample(
    "Multicard callback namunasi",
    value={
        "store_id": 6,
        "amount": 20000,
        "invoice_id": "42",
        "billing_id": "20241214242009869794410864028760",
        "payment_time": "2026-06-20 14:36:31",
        "phone": "998901234567",
        "card_pan": "860030******5959",
        "ps": "uzcard",
        "card_token": "6225f3c93f7a880142782fa4",
        "uuid": "e60d8ebc-b9fe-11ef-b159-005056b4367d",
        "receipt_url": "https://dev-checkout.multicard.uz/check/e60d8ebc-b9fe-11ef-b159-005056b4367d",
        "sign": "553b4292b0f1d8e0e18e6daeb3af3761",
    },
    request_only=True,
)


class MulticardCreateInvoiceView(APIView):
    """
    Frontend "To'lash" tugmasi bosilganda chaqiradigan endpoint.

    Foydalanuvchi avtorizatsiyadan o'tgan bo'lishi shart (JWT) — shuning uchun
    IsAuthenticated. Faqat o'zining obunasi uchun to'lov yaratishi mumkin
    (egalik tekshiruvi pastda bor).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Multicard orqali to'lov yaratish",
        description=(
            "Berilgan obuna_id uchun Multicard invoice yaratadi va "
            "foydalanuvchi yo'naltiriladigan checkout_url qaytaradi."
        ),
        tags=["Multicard"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "obuna_id": {"type": "integer", "example": 5},
                },
                "required": ["obuna_id"],
            }
        },
        examples=[
            OpenApiExample(
                "So'rov namunasi",
                value={"obuna_id": 5},
                request_only=True,
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "checkout_url": {"type": "string"},
                    "short_link": {"type": "string", "nullable": True},
                    "amount": {"type": "integer"},
                },
            },
        },
    )
    def post(self, request):
        obuna_id = request.data.get("obuna_id")
        if not obuna_id:
            return Response(
                {"error": "obuna_id majburiy"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            obuna = Obuna.objects.get(id=obuna_id)
        except Obuna.DoesNotExist:
            return Response(
                {"error": "Obuna topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # --- Egalik tekshiruvi: faqat o'z obunasi uchun to'lov yaratsin ---
        # Obuna rieltor uchun yaratiladi (foydalanuvchi maydoni yo'q)
        try:
            if obuna.rieltor.user_id != request.user.id:
                logger.warning(
                    "[Multicard] Foydalanuvchi %s o'ziga tegishli bo'lmagan obuna_id=%s uchun to'lov yaratmoqchi",
                    request.user.id, obuna_id,
                )
                return Response(
                    {"error": "Bu obuna sizga tegishli emas"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except AttributeError:
            # rieltor yoki rieltor.user mavjud emas — obuna buzilgan
            logger.error("[Multicard] Obuna %s da rieltor mavjud emas", obuna_id)
            return Response(
                {"error": "Obuna ma'lumotlari noto'g'ri"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Allaqachon faol/kutilayotgan to'lov bormi ---
        mavjud_tolov = Tolov.objects.filter(
            obuna=obuna,
            provayder=Tolov.Provayder.MULTICARD,
            holat=Tolov.Holat.KUTILMOQDA,
        ).order_by("-created_at").first()

        if mavjud_tolov and mavjud_tolov.metadata.get("checkout_url"):
            logger.info(
                "[Multicard] Mavjud kutilayotgan invoice qaytarildi: tolov_id=%s",
                mavjud_tolov.id,
            )
            return Response({
                "checkout_url": mavjud_tolov.metadata["checkout_url"],
                "short_link": mavjud_tolov.metadata.get("short_link"),
                "amount": mavjud_tolov.summa,
            })

        # --- Summani aniqlash (sening narxlash logikangga moslab o'zgartir) ---
        amount_som = obuna.narx  # masalan Obuna modelida narx maydoni bo'lsa

        # --- Tolov yozuvini oldindan yaratamiz (KUTILMOQDA holatida) ---
        with transaction.atomic():
            tolov = Tolov.objects.create(
                obuna=obuna,
                provayder=Tolov.Provayder.MULTICARD,
                holat=Tolov.Holat.KUTILMOQDA,
                summa=amount_som,
            )

        # --- Multicard'da invoice yaratamiz ---
        client = MulticardClient()
        try:
            result = client.create_invoice(
                obuna_id=obuna.id,
                amount_som=amount_som,
            )
        except MulticardError as exc:
            logger.error("[Multicard] Invoice yaratishda xato: %s", exc)
            tolov.holat = Tolov.Holat.XATO
            tolov.metadata = {"error": str(exc)}
            tolov.save(update_fields=["holat", "metadata", "updated_at"])
            return Response(
                {"error": "To'lov tizimida xatolik yuz berdi, birozdan keyin urinib ko'ring"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # --- uuid va checkout_url ni saqlaymiz ---
        tolov.tashqi_id = result["uuid"]
        tolov.metadata = result
        tolov.save(update_fields=["tashqi_id", "metadata", "updated_at"])

        logger.info(
            "[Multicard] Invoice yaratildi: tolov_id=%s uuid=%s",
            tolov.id, result["uuid"],
        )

        return Response({
            "checkout_url": result["checkout_url"],
            "short_link": result.get("short_link"),
            "amount": result["amount"],
        })



class MulticardCallbackView(APIView):
    """
    Multicard server-to-server callback.

    To'lov muvaffaqiyatli amalga oshganda Multicard shu URL ga POST so'rov yuboradi
    (invoice yaratishda yuborilgan callback_url). Bu endpoint:
      1. sign (MD5) imzosini tekshiradi
      2. invoice_id bo'yicha Tolov topadi
      3. Muvaffaqiyatli bo'lsa — obunani faollashtiradi
      4. Har doim HTTP 200 qaytaradi (success:true/false orqali natija bildiriladi)

    MUHIM: AllowAny — Multicard JWT autentifikatsiyasiz murojaat qiladi.
           Xavfsizlik sign (MD5) orqali ta'minlanadi.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Multicard Callback (server-to-server)",
        description=(
            "Multicard to'lov natijasini shu endpoint ga POST qiladi. "
            "Xavfsizlik MD5 'sign' maydoni bilan ta'minlanadi: "
            "sign = MD5(store_id + invoice_id + amount + secret). "
            "Javob HAR DOIM HTTP 200 bo'lishi shart — aks holda Multicard to'lovni bekor qiladi."
        ),
        tags=["Multicard"],
        examples=[CALLBACK_REQUEST_EXAMPLE],
        responses={200: dict},
    )
    def post(self, request):
        data = request.data
        logger.info("[Multicard Callback] So'rov keldi: %s", data)

        if not _is_trusted_ip(request):
            logger.warning(
                "[Multicard] Ishonchsiz IP dan so'rov: %s",
                request.META.get("REMOTE_ADDR"),
            )
            # Faqat log qilamiz — asosiy himoya sign tekshiruvi (IP spoofing/proxy
            # holatlarida noto'g'ri rad etmaslik uchun)

        # --- 1. Imzoni tekshirish ---
        if not _verify_callback_signature(data):
            return Response(
                {"success": False, "message": "Noto'g'ri imzo (sign)"},
                status=status.HTTP_200_OK,  # MUHIM: 200 qaytarish shart
            )

        invoice_id = str(data.get("invoice_id", ""))
        mc_uuid = str(data.get("uuid", ""))
        amount = data.get("amount")

        if not invoice_id or not mc_uuid:
            logger.warning("[Multicard Callback] invoice_id yoki uuid yo'q: %s", data)
            return Response(
                {"success": False, "message": "invoice_id va uuid majburiy"},
                status=status.HTTP_200_OK,
            )

        # --- 2. Tolovni DB dan topish ---
        try:
            tolov = Tolov.objects.select_related("obuna").filter(
                provayder=Tolov.Provayder.MULTICARD,
                obuna_id=int(invoice_id) if invoice_id.isdigit() else None,
            ).order_by("-created_at").first()
        except Exception as exc:
            logger.error("[Multicard Callback] DB xatosi: %s", exc)
            return Response(
                {"success": False, "message": "Server xatosi"},
                status=status.HTTP_200_OK,
            )

        if not tolov:
            logger.warning(
                "[Multicard Callback] Tolov topilmadi: invoice_id=%s uuid=%s",
                invoice_id, mc_uuid,
            )
            return Response(
                {"success": False, "message": "Invoys topilmadi"},
                status=status.HTTP_200_OK,
            )

        # --- 3. Idempotentlik: bir xil uuid bilan qayta kelgan so'rov ---
        if tolov.holat == Tolov.Holat.MUVAFFAQIYATLI:
            logger.info(
                "[Multicard Callback] Tolov allaqachon muvaffaqiyatli — qayta yuborilgan so'rov (uuid=%s)",
                mc_uuid,
            )
            return Response({"success": True}, status=status.HTTP_200_OK)

        if tolov.holat not in (Tolov.Holat.KUTILMOQDA,):
            logger.info(
                "[Multicard Callback] Tolov '%s' holatida, bekor qilingan/xato bo'lishi mumkin — o'tkazib yuborildi",
                tolov.holat,
            )
            return Response(
                {"success": False, "message": "Tolov holati mos kelmadi"},
                status=status.HTTP_200_OK,
            )

        # --- 4. Muvaffaqiyatli deb belgilash ---
        with transaction.atomic():
            tolov.tashqi_id = mc_uuid
            tolov.metadata = data
            tolov.save(update_fields=["tashqi_id", "metadata", "updated_at"])
            tolov.muvaffaqiyatli_deb_belgilash()

        logger.info(
            "[Multicard Callback] To'lov muvaffaqiyatli: tolov_id=%s obuna_id=%s summa=%s",
            tolov.id, tolov.obuna_id, amount,
        )
        return Response({"success": True}, status=status.HTTP_200_OK)


class MulticardReturnView(APIView):
    """
    Foydalanuvchi to'lov sahifasidan qaytganda redirect bo'ladigan URL (GET).
    Bu — invoice yaratishda yuborilgan `return_url`.

    Bu endpoint asosiy ishlov bermaydi (callback POST qiladi).
    Faqat frontendni kerakli sahifaga yo'naltiradi.

    Multicard bu yerga qanday query parametrlar bilan qaytarishi hujjatda aniq
    ko'rsatilmagan — shuning uchun invoice_id/uuid bo'lmasa ham frontendga
    umumiy "natija tekshirilmoqda" sahifasiga yo'naltiramiz (haqiqiy holatni
    callback allaqachon DB ga yozgan bo'ladi).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Multicard return_url (foydalanuvchi uchun)",
        description="To'lovdan keyin foydalanuvchi shu URL ga redirect qilinadi.",
        tags=["Multicard"],
    )
    def get(self, request):
        invoice_id = request.query_params.get("invoice_id", "")
        logger.info("[Multicard Return] invoice_id=%s qaytdi", invoice_id)

        frontend_base = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        if not frontend_base:
            return Response({
                "invoice_id": invoice_id,
                "message": "To'lov natijasi callback orqali qayta ishlanadi.",
            })

        redirect_url = f"{frontend_base}/obuna/natija?invoice_id={invoice_id}"
        return HttpResponseRedirect(redirect_url)