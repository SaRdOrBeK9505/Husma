"""
Payme checkout (to'lov sahifasi) havolasini yasash.

Payme GET link formatini qo'llab-quvvatlaydi: kassa parametrlari base64 ga
o'giriladi va checkout.paycom.uz ga qo'shiladi. Foydalanuvchi shu havolaga
o'tib karta ma'lumotlarini kiritadi.

Hujjat: https://developer.help.paycom.uz/initsializatsiya-platezhey/
"""
import base64

from django.conf import settings


def payme_checkout_url(obuna_id: int, amount_som: int, callback_url: str = "") -> str:
    """
    obuna_id  — Payme "account" maydoni (kassa sozlamasidagi nomi: obuna_id)
    amount_som — summa SO'MDA (funksiya ichida tiyinga o'giriladi)
    callback_url — to'lovdan keyin qaytadigan URL (ixtiyoriy)
    """
    amount_tiyin = amount_som * 100
    params = (
        f"m={settings.PAYME_MERCHANT_ID};"
        f"ac.obuna_id={obuna_id};"
        f"a={amount_tiyin}"
    )
    if callback_url:
        params += f";c={callback_url}"

    encoded = base64.b64encode(params.encode("utf-8")).decode("utf-8")
    return f"{settings.PAYME_CHECKOUT_URL}/{encoded}"
