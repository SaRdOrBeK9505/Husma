"""
Payme Merchant API biznes-logikasi.

Har bir JSON-RPC metod (CheckPerformTransaction, CreateTransaction,
PerformTransaction, CancelTransaction, CheckTransaction, GetStatement)
alohida handler sifatida amalga oshirilgan.

Payme bilan bog'lash uchun "account" maydoni sifatida `obuna_id` ishlatiladi.
Ya'ni Payme kassasi sozlamasida buyurtma maydoni `obuna_id` deb belgilanadi.
"""
import time

from django.utils import timezone

from apps.obuna.models import Obuna, Tolov, PaymeTransaction
from . import exceptions as exc

# Payme tranzaksiyasini "vaqti o'tdi" deb hisoblash chegarasi (millisekund)
TIMEOUT_MS = 12 * 60 * 60 * 1000  # 12 soat


def _now_ms() -> int:
    return int(time.time() * 1000)


def _account_obuna_id(params: dict) -> int:
    account = params.get("account") or {}
    obuna_id = account.get("obuna_id")
    if obuna_id is None:
        raise exc.AccountNotFound(data="obuna_id")
    try:
        return int(obuna_id)
    except (TypeError, ValueError):
        raise exc.AccountNotFound(data="obuna_id")


def _get_obuna(params: dict) -> Obuna:
    obuna_id = _account_obuna_id(params)
    try:
        return Obuna.objects.select_related("tarif").get(pk=obuna_id)
    except Obuna.DoesNotExist:
        raise exc.AccountNotFound(data="obuna_id")


def _get_tolov(obuna: Obuna) -> Tolov:
    """Obuna uchun Payme to'lovini topadi yoki yaratadi."""
    tolov = (
        obuna.tolovlar
        .filter(provayder=Tolov.Provayder.PAYME)
        .order_by("-created_at")
        .first()
    )
    if tolov is None:
        tolov = Tolov.objects.create(
            obuna=obuna,
            provayder=Tolov.Provayder.PAYME,
            summa=obuna.narx,
            holat=Tolov.Holat.KUTILMOQDA,
        )
    return tolov


def _validate_amount(obuna: Obuna, amount: int):
    """Payme summani tiyinda yuboradi. So'mga aylantirib solishtiramiz."""
    expected_tiyin = obuna.narx * 100
    if int(amount) != expected_tiyin:
        raise exc.InvalidAmount(data="amount")


class PaymeService:
    """Payme JSON-RPC metodlarini boshqaruvchi servis."""

    def call(self, method: str, params: dict) -> dict:
        handler = {
            "CheckPerformTransaction": self.check_perform_transaction,
            "CreateTransaction": self.create_transaction,
            "PerformTransaction": self.perform_transaction,
            "CancelTransaction": self.cancel_transaction,
            "CheckTransaction": self.check_transaction,
            "GetStatement": self.get_statement,
        }.get(method)

        if handler is None:
            raise exc.MethodNotFound(data=method)
        return handler(params)

    # ===== 1. CheckPerformTransaction =====
    def check_perform_transaction(self, params: dict) -> dict:
        obuna = _get_obuna(params)
        _validate_amount(obuna, params.get("amount"))

        # Obuna allaqachon faol yoki bekor bo'lsa to'lov qabul qilinmaydi
        if obuna.holat in (Obuna.Holat.FAOL, Obuna.Holat.BEKOR):
            raise exc.CantPerformOperation(data="obuna")

        return {"allow": True}

    # ===== 2. CreateTransaction =====
    def create_transaction(self, params: dict) -> dict:
        payme_id = params["id"]

        # Idempotentlik: shu payme_id allaqachon yaratilganmi
        existing = PaymeTransaction.objects.filter(payme_id=payme_id).first()
        if existing:
            if existing.state != PaymeTransaction.STATE_CREATED:
                raise exc.CantPerformOperation(data="state")
            return {
                "create_time": existing.create_time,
                "transaction": str(existing.id),
                "state": existing.state,
            }

        obuna = _get_obuna(params)
        _validate_amount(obuna, params.get("amount"))

        if obuna.holat in (Obuna.Holat.FAOL, Obuna.Holat.BEKOR):
            raise exc.CantPerformOperation(data="obuna")

        # Bu obunada boshqa ochiq Payme tranzaksiyasi bo'lmasligi kerak
        ochiq = PaymeTransaction.objects.filter(
            tolov__obuna=obuna,
            state=PaymeTransaction.STATE_CREATED,
        ).exists()
        if ochiq:
            raise exc.CantPerformOperation(data="obuna")

        tolov = _get_tolov(obuna)
        create_time = _now_ms()

        txn = PaymeTransaction.objects.create(
            tolov=tolov,
            payme_id=payme_id,
            amount=int(params["amount"]),
            state=PaymeTransaction.STATE_CREATED,
            create_time=create_time,
        )

        return {
            "create_time": create_time,
            "transaction": str(txn.id),
            "state": txn.state,
        }

    # ===== 3. PerformTransaction =====
    def perform_transaction(self, params: dict) -> dict:
        txn = self._get_txn(params["id"])

        if txn.state == PaymeTransaction.STATE_CREATED:
            # Vaqti o'tib ketganmi
            if _now_ms() - txn.create_time > TIMEOUT_MS:
                txn.state = PaymeTransaction.STATE_CANCELLED
                txn.reason = 4  # timeout
                txn.cancel_time = _now_ms()
                txn.save(update_fields=["state", "reason", "cancel_time", "updated_at"])
                txn.tolov.bekor_deb_belgilash()
                raise exc.CantPerformOperation(data="timeout")

            perform_time = _now_ms()
            txn.state = PaymeTransaction.STATE_COMPLETED
            txn.perform_time = perform_time
            txn.save(update_fields=["state", "perform_time", "updated_at"])

            # Asosiy biznes effekti: to'lov muvaffaqiyatli → obuna faollashadi
            txn.tolov.muvaffaqiyatli_deb_belgilash()

            return {
                "transaction": str(txn.id),
                "perform_time": perform_time,
                "state": txn.state,
            }

        if txn.state == PaymeTransaction.STATE_COMPLETED:
            # Idempotent javob
            return {
                "transaction": str(txn.id),
                "perform_time": txn.perform_time,
                "state": txn.state,
            }

        raise exc.CantPerformOperation(data="state")

    # ===== 4. CancelTransaction =====
    def cancel_transaction(self, params: dict) -> dict:
        txn = self._get_txn(params["id"])
        reason = params.get("reason")

        if txn.state == PaymeTransaction.STATE_CREATED:
            txn.state = PaymeTransaction.STATE_CANCELLED
            txn.reason = reason
            txn.cancel_time = _now_ms()
            txn.save(update_fields=["state", "reason", "cancel_time", "updated_at"])
            txn.tolov.bekor_deb_belgilash()

        elif txn.state == PaymeTransaction.STATE_COMPLETED:
            # Yakunlangan tranzaksiyani bekor qilish → obunani ham bekor qilamiz
            txn.state = PaymeTransaction.STATE_CANCELLED_AFTER_COMPLETE
            txn.reason = reason
            txn.cancel_time = _now_ms()
            txn.save(update_fields=["state", "reason", "cancel_time", "updated_at"])
            self._bekor_obuna(txn)

        return {
            "transaction": str(txn.id),
            "cancel_time": txn.cancel_time,
            "state": txn.state,
        }

    # ===== 5. CheckTransaction =====
    def check_transaction(self, params: dict) -> dict:
        txn = self._get_txn(params["id"])
        return {
            "create_time": txn.create_time,
            "perform_time": txn.perform_time,
            "cancel_time": txn.cancel_time,
            "transaction": str(txn.id),
            "state": txn.state,
            "reason": txn.reason,
        }

    # ===== 6. GetStatement =====
    def get_statement(self, params: dict) -> dict:
        frm = params.get("from", 0)
        to = params.get("to", _now_ms())
        qs = PaymeTransaction.objects.filter(
            create_time__gte=frm, create_time__lte=to
        ).select_related("tolov__obuna")

        return {
            "transactions": [
                {
                    "id": t.payme_id,
                    "time": t.create_time,
                    "amount": t.amount,
                    "account": {"obuna_id": t.tolov.obuna_id},
                    "create_time": t.create_time,
                    "perform_time": t.perform_time,
                    "cancel_time": t.cancel_time,
                    "transaction": str(t.id),
                    "state": t.state,
                    "reason": t.reason,
                }
                for t in qs
            ]
        }

    # ===== Yordamchi metodlar =====
    def _get_txn(self, payme_id: str) -> PaymeTransaction:
        try:
            return PaymeTransaction.objects.select_related("tolov__obuna").get(
                payme_id=payme_id
            )
        except PaymeTransaction.DoesNotExist:
            raise exc.TransactionNotFound(data="id")

    def _bekor_obuna(self, txn: PaymeTransaction):
        obuna = txn.tolov.obuna
        obuna.holat = Obuna.Holat.BEKOR
        obuna.tugash_vaqti = timezone.now()
        obuna.save(update_fields=["holat", "tugash_vaqti", "updated_at"])
        txn.tolov.bekor_deb_belgilash()
