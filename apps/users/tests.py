import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from apps.hudud.models import Hudud, MulkTuri
from apps.makler.models import MaklerProfil
from .models import CustomUser, OTPKode


TEST_BOT_TOKEN = "123456:TEST_BOT_TOKEN_FOR_UNIT_TESTS"


def build_init_data(user_dict, token=TEST_BOT_TOKEN, auth_date=None):
    """
    Haqiqiy Telegram WebApp initData stringini yasaydi (to'g'ri HMAC hash bilan).
    Bu prod kodidagi verify_telegram_auth() ni o'tadigan ma'lumot.
    """
    if auth_date is None:
        auth_date = int(time.time())

    fields = {
        "user": json.dumps(user_dict, separators=(",", ":")),
        "auth_date": str(auth_date),
    }

    # parse_webapp_user user maydonini json.loads qiladi —
    # verify ham aynan shu (string) qiymat ustidan hash hisoblaydi.
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(fields.items())
    )

    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    valid_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    fields["hash"] = valid_hash
    return urlencode(fields)


@override_settings(TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN)
class TelegramAuthTest(APITestCase):
    """user Telegram WebApp orqali kirishi."""

    def setUp(self):
        self.url = reverse("telegram-auth")
        self.tg_user = {
            "id": 555000111,
            "first_name": "Ali",
            "last_name": "Valiyev",
            "username": "ali_uz",
        }

    def test_yangi_user_royxatdan_otadi(self):
        init_data = build_init_data(self.tg_user)
        resp = self.client.post(self.url, {"init_data": init_data}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertTrue(resp.data["is_new"])
        self.assertEqual(resp.data["user"]["telegram_id"], 555000111)
        self.assertEqual(resp.data["user"]["role"], "user")
        self.assertEqual(resp.data["user"]["full_name"], "Ali Valiyev")

        user = CustomUser.objects.get(telegram_id=555000111)
        self.assertEqual(user.telegram_username, "ali_uz")

    def test_mavjud_user_login_qiladi(self):
        CustomUser.objects.create_user(
            telegram_id=555000111, telegram_username="eski", full_name="Eski Ism"
        )
        init_data = build_init_data(self.tg_user)
        resp = self.client.post(self.url, {"init_data": init_data}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertFalse(resp.data["is_new"])
        # profil yangilanadi
        self.assertEqual(resp.data["user"]["telegram_username"], "ali_uz")
        self.assertEqual(CustomUser.objects.filter(telegram_id=555000111).count(), 1)

    def test_notogri_hash_rad_etiladi(self):
        init_data = build_init_data(self.tg_user, token="BOSHQA:TOKEN")
        resp = self.client.post(self.url, {"init_data": init_data}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_eski_auth_date_rad_etiladi(self):
        old = int(time.time()) - 90000  # 25 soat oldin
        init_data = build_init_data(self.tg_user, auth_date=old)
        resp = self.client.post(self.url, {"init_data": init_data}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_buzuq_init_data(self):
        resp = self.client.post(self.url, {"init_data": "buzuq???"}, format="json")
        self.assertIn(
            resp.status_code,
            (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED),
        )


@override_settings(TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN)
class RieltorRegisterFlowTest(APITestCase):
    """
    Telegram orqali kirgan user rieltor bo'lib ro'yxatdan o'tishi:
    OTP so'rov -> OTP verify -> rieltor login.
    """

    def setUp(self):
        # 1. Telegram auth orqali user yaratamiz va token olamiz
        self.tg_user = {
            "id": 777000222,
            "first_name": "Vali",
            "username": "vali_uz",
        }
        auth_resp = self.client.post(
            reverse("telegram-auth"),
            {"init_data": build_init_data(self.tg_user)},
            format="json",
        )
        assert auth_resp.status_code == 200, auth_resp.data
        self.access = auth_resp.data["access"]
        self.user = CustomUser.objects.get(telegram_id=777000222)

        # 2. Hudud va mulk turi (register uchun majburiy)
        self.hudud = Hudud.objects.create(nomi="Chilonzor")
        self.mulk = MulkTuri.objects.create(kod="kvartira", nomi="Kvartira")

        self.sorov_url = reverse("rieltor-otp-sorov")
        self.verify_url = reverse("rieltor-otp-verify")
        self.login_url = reverse("rieltor-login")

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

    @patch("apps.users.views.otp_yuborish", return_value=True)
    def test_toliq_register_login_oqimi(self, mock_yuborish):
        self._auth()

        # --- 1-qadam: OTP so'rov ---
        sorov_body = {
            "full_name": "Vali Aliyev",
            "phone": "+998901234567",
            "username": "vali_rieltor",
            "password": "parol123",
            "hududlar": [self.hudud.id],
            "mulk_turlari": [self.mulk.id],
        }
        r1 = self.client.post(self.sorov_url, sorov_body, format="json")
        self.assertEqual(r1.status_code, status.HTTP_200_OK, r1.data)
        self.assertTrue(mock_yuborish.called)

        otp = OTPKode.objects.get(telegram_id=777000222)
        self.assertEqual(otp.register_data["username"], "vali_rieltor")

        # --- 2-qadam: OTP verify ---
        r2 = self.client.post(self.verify_url, {"kode": otp.kode}, format="json")
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED, r2.data)
        self.assertIn("access", r2.data)
        self.assertEqual(r2.data["rieltor"]["role"], "makler")
        self.assertTrue(r2.data["rieltor"]["faol"])

        # User makler rolega o'tdi
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, CustomUser.Role.MAKLER)
        self.assertEqual(self.user.username, "vali_rieltor")
        self.assertTrue(self.user.check_password("parol123"))

        # MaklerProfil yaratildi, hudud/mulk bog'landi
        rieltor = self.user.rieltor_profil
        self.assertEqual(rieltor.verify_holat, MaklerProfil.VerifyHolat.VERIFIED)
        self.assertIn(self.hudud, rieltor.hududlar.all())
        self.assertIn(self.mulk, rieltor.mulk_turlari.all())
        self.assertTrue(rieltor.faol)  # 7 kunlik bepul muddat

        # OTP o'chirildi
        self.assertFalse(OTPKode.objects.filter(telegram_id=777000222).exists())

        # --- 3-qadam: rieltor username/parol bilan login ---
        self.client.credentials()  # tokenni tozalaymiz
        r3 = self.client.post(
            self.login_url,
            {"username": "vali_rieltor", "password": "parol123"},
            format="json",
        )
        self.assertEqual(r3.status_code, status.HTTP_200_OK, r3.data)
        self.assertIn("access", r3.data)
        self.assertEqual(r3.data["rieltor"]["username"], "vali_rieltor")
        self.assertTrue(r3.data["rieltor"]["faol"])

    def test_token_siz_sorov_rad_etiladi(self):
        r = self.client.post(self.sorov_url, {}, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.users.views.otp_yuborish", return_value=True)
    def test_band_username_rad_etiladi(self, _):
        CustomUser.objects.create_user(telegram_id=999, username="vali_rieltor")
        self._auth()
        body = {
            "full_name": "Vali Aliyev",
            "phone": "+998901234567",
            "username": "vali_rieltor",
            "password": "parol123",
            "hududlar": [self.hudud.id],
            "mulk_turlari": [self.mulk.id],
        }
        r = self.client.post(self.sorov_url, body, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.views.otp_yuborish", return_value=True)
    def test_hududsiz_register_rad_etiladi(self, _):
        self._auth()
        body = {
            "full_name": "Vali Aliyev",
            "phone": "+998901234567",
            "username": "vali_rieltor",
            "password": "parol123",
            "hududlar": [],
            "mulk_turlari": [self.mulk.id],
        }
        r = self.client.post(self.sorov_url, body, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_notogri_kode_verify_rad_etiladi(self):
        self._auth()
        OTPKode.objects.create(
            telegram_id=777000222, kode="111111", register_data={}
        )
        r = self.client.post(self.verify_url, {"kode": "999999"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.users.views.otp_yuborish", return_value=True)
    def test_takroriy_register_rad_etiladi(self, _):
        # User allaqachon makler
        self.user.role = CustomUser.Role.MAKLER
        self.user.save(update_fields=["role"])
        self._auth()
        body = {
            "full_name": "Vali Aliyev",
            "phone": "+998901234567",
            "username": "vali_rieltor",
            "password": "parol123",
            "hududlar": [self.hudud.id],
            "mulk_turlari": [self.mulk.id],
        }
        r = self.client.post(self.sorov_url, body, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN)
class RieltorLoginTest(APITestCase):
    """Rieltor login chekka holatlari."""

    def setUp(self):
        self.login_url = reverse("rieltor-login")

    def test_notogri_parol(self):
        user = CustomUser.objects.create_user(
            telegram_id=123, username="rieltor1", role=CustomUser.Role.MAKLER
        )
        user.set_password("togri_parol")
        user.save()
        MaklerProfil.objects.create(user=user)

        r = self.client.post(
            self.login_url,
            {"username": "rieltor1", "password": "xato"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_makler_bolmagan_user_login_qila_olmaydi(self):
        user = CustomUser.objects.create_user(
            telegram_id=124, username="oddiy", role=CustomUser.Role.USER
        )
        user.set_password("parol123")
        user.save()

        r = self.client.post(
            self.login_url,
            {"username": "oddiy", "password": "parol123"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_mavjud_bolmagan_username(self):
        r = self.client.post(
            self.login_url,
            {"username": "yoq", "password": "parol123"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
