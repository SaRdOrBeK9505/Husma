"""
Multicard Payment Gateway — API Client
=======================================
Rasmiy hujjat: https://docs.multicard.uz

Oqim:
  1. client.get_token()          → Bearer token olish (auth javobidagi "expiry"ga qarab kechadi)
  2. client.create_invoice()     → Invoice yaratish → checkout_url (foydalanuvchini shu yerga yo'naltirasan)
  3. Multicard callback (POST)   → views.py da MD5 sign tekshirib qayta ishlanadi
  4. obuna.faollashtirish()      → To'lov tasdiqlangach obuna faollashadi

Sozlamalar (.env):
  MULTICARD_APPLICATION_ID=<sizga berilgan application_id>
  MULTICARD_SECRET=<sizga berilgan secret>
  MULTICARD_STORE_ID=<sizga berilgan store_id>
  MULTICARD_BASE_URL=https://dev-mesh.multicard.uz   # sandbox
  # MULTICARD_BASE_URL=https://mesh.multicard.uz      # production
  MULTICARD_CALLBACK_URL=https://domeningiz.uz/api/payments/multicard/callback/
  MULTICARD_RETURN_URL=https://domeningiz.uz/obuna/natija

DIQQAT:
  - Auth endpoint: POST /auth  body: {"application_id", "secret"}  (login/parol EMAS)
  - Invoice endpoint: POST /payment/invoice
  - Javobdagi to'lov havolasi maydoni: "checkout_url" (invoice_url EMAS)
  - Invoice identifikatori: "uuid" (Multicard tomonidan beriladi) va "invoice_id" (siz bergan)
  - amount tiyinda yuboriladi (so'm * 100) — sandbox'da albatta
    bitta test invoice yaratib summani tasdiqlang, chunki hujjat misolida raqamlar
    so'rov/javobda farq qilgan.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger("multicard")

# Token cache — server xotirasida saqlanadi (restart bo'lsa yangilanadi)
_token_cache: dict = {
    "token": None,
    "expires_at": None,
}

BASE_URL = getattr(settings, "MULTICARD_BASE_URL", "https://mesh.multicard.uz")


class MulticardError(Exception):
    """Multicard API xatosi."""

    def __init__(self, message: str, status_code: int = 0, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}

    def __str__(self):
        return f"{self.args[0]} (status={self.status_code}, response={self.response})"


class MulticardClient:
    """
    Multicard API bilan ishlash uchun client.

    Foydalanish:
        client = MulticardClient()
        result = client.create_invoice(obuna_id=42, amount_som=99000)
        # result["checkout_url"] ga foydalanuvchini yo'naltirasiz
    """

    def __init__(self):
        self.application_id = getattr(settings, "MULTICARD_APPLICATION_ID", "")
        self.secret = getattr(settings, "MULTICARD_SECRET", "")
        self.store_id = getattr(settings, "MULTICARD_STORE_ID", "")
        self.base_url = BASE_URL.rstrip("/")
        self.timeout = getattr(settings, "MULTICARD_TIMEOUT", 15)

        if not self.application_id or not self.secret:
            logger.warning(
                "[Multicard] MULTICARD_APPLICATION_ID yoki MULTICARD_SECRET "
                "sozlanmagan! .env faylni tekshiring."
            )
        if not self.store_id:
            logger.warning(
                "[Multicard] MULTICARD_STORE_ID sozlanmagan! "
                "Invoice yaratish ishlamaydi."
            )

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Bearer token olish. Token keshlanadi va muddati tugamasa
        qayta so'rov yuborilmaydi. Muddat Multicard javobidagi
        "expiry" maydonidan olinadi (qattiq kodlangan soat emas).
        """
        now = datetime.utcnow()
        if (
            not force_refresh
            and _token_cache["token"]
            and _token_cache["expires_at"]
            and now < _token_cache["expires_at"]
        ):
            return _token_cache["token"]

        logger.info("[Multicard] Token yangilanmoqda...")
        url = f"{self.base_url}/auth"
        try:
            resp = requests.post(
                url,
                json={
                    "application_id": self.application_id,
                    "secret": self.secret,
                },
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.error("[Multicard] Token so'rovida tarmoq xatosi: %s", exc)
            raise MulticardError(f"Multicard bilan bog'lanib bo'lmadi: {exc}")

        data = self._safe_json(resp)

        if resp.status_code != 200:
            logger.error(
                "[Multicard] Token xatosi: %s %s", resp.status_code, data
            )
            raise MulticardError(
                "Multicard token olishda xato",
                status_code=resp.status_code,
                response=data,
            )

        token = data.get("token")
        expiry_str = data.get("expiry")  # masalan: "2023-03-18 16:40:31"

        if not token:
            raise MulticardError("Multicard tokenni qaytarmadi", response=data)

        if expiry_str:
            try:
                expires_at = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.warning(
                    "[Multicard] expiry formatini tushunib bo'lmadi: %s", expiry_str
                )
                expires_at = now + timedelta(minutes=30)
        else:
            # expiry kelmasa — xavfsiz tomondan, qisqa muddat bilan keshlaymiz
            expires_at = now + timedelta(minutes=30)

        # Muddat tugashidan 2 daqiqa oldin yangilanishi uchun zaxira qoldiramiz
        _token_cache["token"] = token
        _token_cache["expires_at"] = expires_at - timedelta(minutes=2)

        logger.info(
            "[Multicard] Token olindi, amal qilish muddati: %s", expiry_str
        )
        return token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Token eskirgan bo'lsa (401) — bir marta tokenni yangilab qayta urinadi.
        """
        headers = self._headers()
        kwargs["headers"] = headers
        try:
            resp = requests.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise MulticardError(f"Multicard bilan bog'lanib bo'lmadi: {exc}")

        if resp.status_code == 401:
            logger.info("[Multicard] 401 keldi — token yangilanmoqda va qayta urinilmoqda")
            self.get_token(force_refresh=True)
            kwargs["headers"] = self._headers()
            try:
                resp = requests.request(method, url, timeout=self.timeout, **kwargs)
            except requests.RequestException as exc:
                raise MulticardError(f"Multicard bilan bog'lanib bo'lmadi: {exc}")

        return resp

    # ------------------------------------------------------------------
    # Invoice — Multicard to'lov sahifasida to'lash
    # ------------------------------------------------------------------

    def create_invoice(
        self,
        obuna_id: int,
        amount_som: int,
        return_url: str = "",
        callback_url: str = "",
        lang: str = "uz",
        ofd: Optional[list] = None,
    ) -> dict:
        """
        Invoice yaratadi va to'lov uchun checkout_url qaytaradi.

        Args:
            obuna_id     : Bizning DB dagi Obuna.id — Multicard'ga "invoice_id" sifatida boradi
            amount_som   : Summa so'mda (Multicard hujjatidagi misolga ko'ra tiyinga
                            aylantirilmaydi — sandbox'da bitta test bilan tasdiqlang)
            return_url   : To'lovdan keyin foydalanuvchi qaytadigan URL
            callback_url : Multicard to'lov natijasini shu URL ga POST qiladi
                           (bo'sh qoldirilsa settings.MULTICARD_CALLBACK_URL ishlatiladi)
            lang         : To'lov sahifasi tili ("uz" | "ru")
            ofd          : Fiskal chek uchun mahsulotlar ro'yxati (ixtiyoriy)

        Returns:
            {
                "invoice_id": "42",
                "uuid": "f6339f31-...",          # Multicard transaction ID — DB ga saqlang
                "checkout_url": "https://...",   # foydalanuvchini shu yerga yo'naltiring
                "short_link": "https://...",     # QR-kod uchun (faqat production)
                "amount": 99000,
            }

        Raises:
            MulticardError: API xato qaytarsa yoki store_id sozlanmagan bo'lsa
        """
        if not self.store_id:
            raise MulticardError("MULTICARD_STORE_ID sozlanmagan (.env tekshiring)")

        payload = {
            "store_id": self.store_id,
            "amount": amount_som*100,
            "invoice_id": str(obuna_id),
            "lang": lang,
            "return_url": return_url or getattr(settings, "MULTICARD_RETURN_URL", ""),
            "callback_url": callback_url or getattr(settings, "MULTICARD_CALLBACK_URL", ""),
        }
        if ofd:
            payload["ofd"] = ofd

        logger.info(
            "[Multicard] Invoice yaratilmoqda: obuna_id=%s, summa=%s so'm",
            obuna_id, amount_som,
        )

        url = f"{self.base_url}/payment/invoice"
        resp = self._request_with_retry("POST", url, json=payload)
        data = self._safe_json(resp)

        if resp.status_code not in (200, 201) or not data.get("success"):
            logger.error("[Multicard] Invoice xatosi: %s %s", resp.status_code, data)
            error = data.get("error") or {}
            raise MulticardError(
                f"Invoice yaratishda xato: {error.get('details', data)}",
                status_code=resp.status_code,
                response=data,
            )

        inner = data.get("data", {})
        checkout_url = inner.get("checkout_url")
        if not checkout_url:
            raise MulticardError("Multicard checkout_url qaytarmadi", response=data)

        logger.info(
            "[Multicard] Invoice yaratildi: uuid=%s checkout_url=%s",
            inner.get("uuid"), checkout_url,
        )
        return {
            "invoice_id": str(obuna_id),
            "uuid": inner.get("uuid"),
            "checkout_url": checkout_url,
            "short_link": inner.get("short_link"),
            "deeplink": inner.get("deeplink"),
            "amount": amount_som*100,
        }

    def get_invoice(self, uuid: str) -> dict:
        """
        Invoice holati haqida ma'lumot olish (uuid bo'yicha).
        """
        url = f"{self.base_url}/payment/invoice/{uuid}"
        resp = self._request_with_retry("GET", url)
        data = self._safe_json(resp)

        if resp.status_code != 200 or not data.get("success"):
            raise MulticardError(
                "Invoice ma'lumotini olishda xato",
                status_code=resp.status_code,
                response=data,
            )
        return data.get("data", data)

    def cancel_invoice(self, uuid: str) -> bool:
        """
        Invoice ni bekor qilish (foydalanuvchi obunani bekor qilganda).
        True qaytarsa muvaffaqiyatli.
        """
        url = f"{self.base_url}/payment/invoice/{uuid}"
        try:
            resp = self._request_with_retry("DELETE", url)
        except MulticardError as exc:
            logger.warning("[Multicard] Invoice bekor qilishda xato: %s", exc)
            return False
        return resp.status_code in (200, 204)

    # ------------------------------------------------------------------
    # Yordamchi
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_json(resp: requests.Response) -> dict:
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text[:500]}


def get_client() -> MulticardClient:
    """Har safar yangi instance (stateless, token modul darajasida keshlanadi)."""
    return MulticardClient()