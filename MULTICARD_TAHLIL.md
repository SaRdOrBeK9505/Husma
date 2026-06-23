# 🔍 Multicard Integratsiya — To'liq Tahlil va Tuzatishlar

**Tahlil Sanasi:** 2026-06-23  
**Maqsad:** Multicard to'lov tizimi to'g'ri ishlashini tekshirish va kichik xatolarni tuzatish

---

## 📋 Umumiy Xulosa

**✅ ASOSIY LOGIKA TO'G'RI YOZILGAN**

Sizning Multicard integratsiyangiz **professional darajada** yozilgan va rasmiy hujjatlarga to'liq mos keladi:

- ✅ Token management va keshlash to'g'ri
- ✅ MD5 sign verification to'g'ri (timing attack himoyasi bilan)
- ✅ Idempotency (qayta so'rovlar) to'g'ri
- ✅ HTTP 200 har doim qaytariladi (Multicard protokoli)
- ✅ Atomic transaction (tolov + obuna faollashtirish)
- ✅ IP whitelist qo'shilgan
- ✅ Duplicate invoice oldini olish

**❗ 3 ta kichik muammo topildi va tuzatish kerak.**

---

## 🎯 Multicard Payment Oqimi

```
┌─────────────┐
│  1. Frontend│  POST /api/multicard/create/ {obuna_id: 5}
│   (JWT)     │  Authorization: Bearer <token>
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  2. Backend (MulticardCreateInvoiceView)        │
│     ├─ Obuna topiladi va egalik tekshiriladi    │
│     ├─ MulticardClient.get_token()              │
│     │   └─ Keshdan yoki yangi token olinadi     │
│     ├─ MulticardClient.create_invoice()         │
│     │   └─ POST /payment/invoice                │
│     └─ Response: {checkout_url, uuid}           │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│  3. Frontend                              │
│     Foydalanuvchini checkout_url ga       │
│     yo'naltiradi (Multicard to'lov sahif)│
│     https://dev-checkout.multicard.uz/... │
└──────────────────┬────────────────────────┘
                   │
                   ▼
┌───────────────────────────────────────────┐
│  4. Foydalanuvchi                         │
│     Kartadan to'lov qiladi                │
└──────────────────┬────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌────────────────┐   ┌─────────────────────────┐
│ 5a. Callback   │   │ 5b. Return URL          │
│  (server-to-   │   │  (foydalanuvchi uchun)  │
│   server)      │   │                         │
│                │   │                         │
│  POST callback/│   │  GET return/            │
│  {sign, uuid,  │   │  ?invoice_id=...        │
│   invoice_id,  │   │                         │
│   amount, ...} │   │  → Frontend redirect    │
│                │   │                         │
│  ├─ sign MD5   │   └─────────────────────────┘
│  │  verify     │
│  ├─ Tolov top  │
│  ├─ Obuna faol │
│  └─ {"success" │
│      : true}   │
│  HTTP 200      │
└────────────────┘
```

---

## ✅ To'g'ri Yozilgan Joylar (Details)

### 1. **Token Management — Keshlanadi**

**Fayl:** `apps/obuna/multicard/client.py:25-28`

```python
_token_cache: dict = {
    "token": None,
    "expires_at": None,
}
```

**✅ Har invoice uchun yangi token olinmaydi** — server xotirasida keshlanadi.

**✅ 401 error da auto-refresh:**
```python
if resp.status_code == 401:
    self.get_token(force_refresh=True)
    # qayta urinadi
```

**✅ Token expiry multicard javobidan olinadi** (qattiq kodlangan 30 daqiqa emas):
```python
expiry_str = data.get("expiry")  # "2023-03-18 16:40:31"
expires_at = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
```

---

### 2. **MD5 Sign Verification — Xavfsiz**

**Fayl:** `apps/obuna/multicard/views.py:32-35`

```python
def _calc_sign(store_id, invoice_id, amount, secret: str) -> str:
    raw = f"{store_id}{invoice_id}{amount}{secret}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
```

**✅ Formula to'g'ri:** `MD5(store_id + invoice_id + amount + secret)` — hech qanday separator yo'q.

**✅ Timing attack himoyasi:**
```python
is_valid = hmac.compare_digest(expected, received)
```

`==` o'rniga `hmac.compare_digest` — vaqt bo'yicha tahlil hujumidan himoya.

---

### 3. **Idempotency — Qayta So'rovlar**

**Fayl:** `apps/obuna/multicard/views.py:317-324`

```python
if tolov.holat == Tolov.Holat.MUVAFFAQIYATLI:
    logger.info("...qayta yuborilgan so'rov (uuid=%s)", mc_uuid)
    return Response({"success": True}, status=status.HTTP_200_OK)
```

**✅ Bir xil UUID bilan qayta kelgan so'rov** muvaffaqiyatli deb qaytariladi (duplicate processing oldini oladi).

---

### 4. **HTTP 200 HAR DOIM Qaytariladi**

**Fayl:** `apps/obuna/multicard/views.py:286-290`

```python
if not _verify_callback_signature(data):
    return Response(
        {"success": False, "message": "Noto'g'ri imzo (sign)"},
        status=status.HTTP_200_OK,  # ← MUHIM!
    )
```

**✅ Xato holatlarda ham 200 qaytariladi** — Multicard protokoli talabi. Aks holda to'lov bekor qilinadi va pul qaytariladi.

---

### 5. **Atomic Transaction**

**Fayl:** `apps/obuna/multicard/views.py:334-338`

```python
with transaction.atomic():
    tolov.tashqi_id = mc_uuid
    tolov.metadata = data
    tolov.save(update_fields=["tashqi_id", "metadata", "updated_at"])
    tolov.muvaffaqiyatli_deb_belgilash()  # → obuna.faollashtirish()
```

**✅ Tolov va obuna faollashtirish bitta atomik tranzaksiyada** — agar xato bo'lsa rollback bo'ladi.

---

### 6. **IP Whitelist**

**Fayl:** `apps/obuna/multicard/views.py:24`

```python
MULTICARD_CALLBACK_IP = "195.158.26.90"
```

**✅ Qo'shimcha xavfsizlik qatlami** — faqat Multicard serveridan kelgan so'rovlar qabul qilinadi (asosiy himoya — MD5 sign).

---

### 7. **Duplicate Invoice Oldini Olish**

**Fayl:** `apps/obuna/multicard/views.py:172-184`

```python
mavjud_tolov = Tolov.objects.filter(
    obuna=obuna,
    provayder=Tolov.Provayder.MULTICARD,
    holat=Tolov.Holat.KUTILMOQDA,
).order_by("-created_at").first()

if mavjud_tolov and mavjud_tolov.metadata.get("checkout_url"):
    return Response({"checkout_url": ...})  # Mavjudini qaytaradi
```

**✅ Agar kutilayotgan to'lov mavjud bo'lsa** — yangi invoice yaratilmaydi, mavjudini qaytaradi.

---

## ⚠️ Topilgan Muammolar va Tuzatishlar

### ❌ Muammo #1: Egalik Tekshiruvi Noto'g'ri

**Fayl:** `apps/obuna/multicard/views.py:166-173`

```python
# ❌ XATO KOD:
if hasattr(obuna, "foydalanuvchi") and obuna.foydalanuvchi_id != request.user.id:
    return Response({"error": "Bu obuna sizga tegishli emas"}, 403)
```

**Muammo:**
1. `Obuna` modelida `foydalanuvchi` maydoni YO'Q
2. Obuna **rieltor** uchun yaratiladi, oddiy user uchun emas
3. `hasattr` doim `False` qaytaradi → egalik hech qachon tekshirilmaydi

**Haqiqiy Model** (`apps/obuna/models.py:54-58`):
```python
class Obuna(models.Model):
    rieltor = models.ForeignKey('makler.MaklerProfil', ...)  # ← Bu mavjud
    tarif = models.ForeignKey(Tarif, ...)
    # foydalanuvchi maydoni yo'q!
```

**✅ TUZATILGAN KOD:**
```python
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
    # rieltor yoki rieltor.user mavjud emas
    logger.error("[Multicard] Obuna %s da rieltor mavjud emas", obuna_id)
    return Response(
        {"error": "Obuna ma'lumotlari noto'g'ri"},
        status=status.HTTP_400_BAD_REQUEST,
    )
```

---

### ❌ Muammo #2: Invoice ID — Obuna ID Ochiq Ko'rinadi (Security Risk)

**Fayl:** `apps/obuna/multicard/client.py:230`

```python
# ❌ XATO:
payload = {
    "invoice_id": str(obuna_id),  # ← Obuna.id (1, 2, 3, ...)
}
```

**Muammo:**
- `invoice_id` sifatida Obuna.id (1, 2, 3, ...) yuboriladi
- Multicard bu IDni **ochiq** ko'rsatadi (checkout URL, receipt, callback)
- Attacker `invoice_id=1`, `invoice_id=2` bilan **boshqa odamlarning obunalarini to'lashi** mumkin

**Misol Attack:**
```
1. Ali obuna_id=5 uchun to'lov yaratadi
2. Vali checkout URL ni ko'radi: ...?invoice_id=5
3. Vali invoice_id=6 (Bobur ning obunasi) ga o'zgartiradi
4. Vali Boburning obunasini to'laydi (lekin obuna Boburga faollashadi)
```

**✅ YECHIM: UUID Ishlatish**

```python
import uuid

# 1. Tolov yaratilganda UUID generate qilish
tolov = Tolov.objects.create(
    obuna=obuna,
    provayder=Tolov.Provayder.MULTICARD,
    holat=Tolov.Holat.KUTILMOQDA,
    summa=amount_som,
    tashqi_id=str(uuid.uuid4()),  # ← Tasodifiy UUID
)

# 2. Multicard'ga UUID yuborish
payload = {
    "invoice_id": tolov.tashqi_id,  # UUID (e60d8ebc-b9fe-11ef-b159-005056b4367d)
    "amount": amount_som,
    ...
}

# 3. Callback da UUID bo'yicha topish
tolov = Tolov.objects.filter(
    provayder=Tolov.Provayder.MULTICARD,
    tashqi_id=invoice_id,  # UUID bo'yicha
).select_related("obuna").first()
```

**Foyda:**
- UUID taxmin qilib bo'lmaydi (`e60d8ebc-b9fe-11ef-b159-005056b4367d`)
- Boshqa odamning to'lovini intercepting mumkin emas

---

### ❌ Muammo #3: Callback — `obuna_id` Orqali Qidirish Noto'g'ri

**Fayl:** `apps/obuna/multicard/views.py:306-310`

```python
# ❌ XATO:
tolov = Tolov.objects.filter(
    provayder=Tolov.Provayder.MULTICARD,
    obuna_id=int(invoice_id) if invoice_id.isdigit() else None,
).order_by("-created_at").first()
```

**Muammo:**
1. `invoice_id` (Obuna.id) bir nechta to'lovda bo'lishi mumkin
2. `order_by('-created_at').first()` — eng oxirgi to'lov olinadi
3. **Agar birinchi to'lov bekor qilingan bo'lsa** — ikkinchi to'lov faollashadi, lekin Multicard birinchi to'lov uchun callback yuboradi

**Misol:**
```sql
-- DB holati:
Tolov(id=1, obuna_id=5, holat='bekor', tashqi_id=NULL)
Tolov(id=2, obuna_id=5, holat='kutilmoqda', tashqi_id='uuid-456')

-- Multicard callback: invoice_id=5 (obuna_id)
-- Kod id=2 ni topadi (eng oxirgi), lekin callback id=1 uchun bo'lishi mumkin
```

**✅ YECHIM:**

Muammo #2 ni tuzatish bilan hal bo'ladi — UUID ishlatish (`tashqi_id` unique bo'ladi).

---

## 🔧 Tuzatish Ketma-ketligi

### Step 1: Egalik Tekshiruvini Tuzatish

<function_calls>
<invoke name="str_replace">
<parameter name="path">c:\Users\Tasanno\PycharmProjects\Husma\apps\obuna\multicard\views.py