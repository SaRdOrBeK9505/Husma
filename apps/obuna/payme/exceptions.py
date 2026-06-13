"""
Payme Merchant API JSON-RPC xato kodlari.

Payme protokoli xatolarni JSON-RPC `error` obyekti orqali kutadi:
    {"error": {"code": <int>, "message": {...}, "data": <str>}}
"""


class PaymeError(Exception):
    """Payme JSON-RPC xatosi uchun bazaviy klass."""
    code: int = -32400
    message: str = "Xatolik"

    def __init__(self, data: str | None = None, message: str | None = None):
        self.data = data
        if message:
            self.message = message
        super().__init__(self.message)

    def as_rpc_error(self) -> dict:
        return {
            "code": self.code,
            "message": {
                "ru": self.message,
                "uz": self.message,
                "en": self.message,
            },
            "data": self.data,
        }


# ===== Tranzaksiya / hisob xatolari (Payme spetsifikatsiyasi) =====

class TransactionNotFound(PaymeError):
    code = -31003
    message = "Tranzaksiya topilmadi"


class InvalidAmount(PaymeError):
    code = -31001
    message = "Noto'g'ri summa"


class AccountNotFound(PaymeError):
    # -31050..-31099 oralig'i hisob (account) maydonlari uchun ajratilgan
    code = -31050
    message = "Buyurtma (obuna) topilmadi"


class CantPerformOperation(PaymeError):
    code = -31008
    message = "Operatsiyani bajarib bo'lmaydi"


# ===== Tizim / autentifikatsiya xatolari =====

class MethodNotFound(PaymeError):
    code = -32601
    message = "Metod topilmadi"


class InsufficientPrivilege(PaymeError):
    code = -32504
    message = "Avtorizatsiya yetarli emas"


class InvalidJsonRPC(PaymeError):
    code = -32600
    message = "Noto'g'ri so'rov"
