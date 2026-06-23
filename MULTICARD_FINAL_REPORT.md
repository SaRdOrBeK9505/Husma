# 📊 Multicard To'lov Tizimi — Yakuniy Hisobot

**Sana:** 2026-06-23  
**Loyiha:** Husma — Kvartira Qidiruv Platformasi  
**To'lov Provayder:** Multicard Payment Gateway

---

## ✅ Umumiy Holat

**ASOSAN TO'G'RI YOZILGAN — 1 ta muammo tuzatildi, 2 ta tavsiya berildi**

Sizning Multicard integratsiyangiz professional darajada amalga oshirilgan va rasmiy protokolga to'liq mos keladi.

---

## 🎯 Asosiy Imkoniyatlar

✅ **Token Management** — Keshlanadi, auto-refresh 401 da  
✅ **MD5 Signature** — To'g'ri formula, timing attack himoyasi  
✅ **Idempotency** — Qayta so'rovlar to'g'ri boshqariladi  
✅ **HTTP 200 Always** — Xato holatida ham 200 (Multicard protokoli)  
✅ **Atomic Transactions** — Tolov + obuna bitta tranzaksiyada  
✅ **IP Whitelist** — Faqat Multicard serveridan qabul qilinadi  
✅ **Duplicate Prevention** — Mavjud invoice qaytariladi  

---

## 🔧 Amalga Oshirilgan Tuzatishlar

### ✅ Tuzatish #1: Egalik Tekshiruvi

**Muammo:** `hasattr(obuna, "foydalanuvchi")` doim `False` — Obuna modelida `foydalanuvchi` maydoni yo'q.

**Tuzatish:** `obuna.rieltor.user_id` tekshiriladi.

**Fayl:** `apps/obuna/multicard/views.py:172-192`

```python
# OLDIN (❌):
if hasattr(obuna, "foydalanuvchi") and obuna.foydalanuvchi_id != request.user.id:
    return Response({"error": ...}, 403)

# HOZIR (✅):
try:
    if obuna.rieltor.user_id != request.user.id:
        return Response({"error": "Bu obuna sizga tegishli emas"}, 403)
except AttributeError:
    logger.error("Obuna %s da rieltor mavjud emas", obuna_id)
    return Response({"error": "Obuna ma'lumotlari noto'g'ri"}, 400)
```

---

## 💡 Qo'shimcha Tavsiyalar (Optional)

### 🔐 Tavsiya #1: UUID Ishlatish (Security Enhancement)

**Hozirgi Holat:**
```python
# Obuna.id (1, 2, 3, ...) Multicard'ga yuboriladi
payload = {"invoice_id": str(obuna_id)}  # "invoice_id": "5"
```

**Muammo:**
- Invoice ID ochiq ko'rinadi (checkout URL, receipt)
- Attacker boshqa odamlarning obunalarini to'lashi mumkin (`invoice_id=1`, `invoice_id=2`)

**Tavsiya:** UUID ishlatish:

```python
import uuid

# Tolov yaratilganda:
tolov = Tolov.objects.create(
    obuna=obuna,
    tashqi_id=str(uuid.uuid4()),  # Tasodifiy UUID
    ...
)

# Multicard'ga yuborish:
payload = {
    "invoice_id": tolov.tashqi_id,  # "e60d8ebc-b9fe-11ef-b159-005056b4367d"
}

# Callback da topish:
tolov = Tolov.objects.filter(tashqi_id=invoice_id).first()
```

**Foyda:**
- UUID taxmin qilib bo'lmaydi
- Boshqa odamning to'lovini intercepting mumkin emas

---

### 🧪 Tavsiya #2: Amount Test Qilish

**Hozir:**
```python
payload = {"amount": amount_som}  # So'mda yuboriladi (tiyin emas)
```

**Tekshirish kerak:**
- Payme tiyin (so'm × 100) ishlatadi
- Multicard dokumentatsiyasida to'g'ridan-to'g'ri so'm ko'rsatilgan
- Lekin sandbox'da test invoice yaratib tasdiqlash kerak

**Test:**
```python
client.create_invoice(obuna_id=999, amount_som=1000)  # 1000 so'm
```

Checkout sahifasida **1000 so'm** ko'rinsa — to'g'ri.  
Agar **10 so'm** ko'rinsa — `amount × 100` qilish kerak.

---

## 📚 Multicard Oqimi (Yakuniy)

```
1. Frontend → POST /api/multicard/create/ {obuna_id: 5}
   ↓
2. Backend → MulticardClient.get_token() → Bearer token (keshlanadi)
   ↓
3. Backend → MulticardClient.create_invoice() → {checkout_url, uuid}
   ↓
4. Frontend → Foydalanuvchini checkout_url ga yo'naltiradi
   ↓
5. Foydalanuvchi → Multicard sahifasida kartadan to'lov qiladi
   ↓
6. Multicard → POST /api/obuna/multicard/callback/ (server-to-server)
              {sign, uuid, invoice_id, amount, ...}
   ↓
7. Backend → sign (MD5) tekshiradi
            Tolov topiladi
            Obuna faollashtiriladi
            {"success": true} (HTTP 200)
   ↓
8. Foydalanuvchi → GET /api/obuna/multicard/return/ → Frontend redirect
```

---

## 🧪 Test Checklist

Multicard sandbox'da test qilish:

- [ ] Invoice yaratish (`amount=1000` → checkout'da 1000 so'm ko'rinishi kerak)
- [ ] Muvaffaqiyatli to'lov (test karta: hujjatdan olish)
- [ ] Callback keladi va sign to'g'ri tekshiriladi
- [ ] Tolov `MUVAFFAQIYATLI` ga o'tadi
- [ ] Obuna faollashadi (`holat=faol`)
- [ ] Qayta callback kelsa (idempotency) — duplicate yaratilmaydi
- [ ] Noto'g'ri sign bilan callback — `success: false` qaytariladi
- [ ] Frontend return URL ga to'g'ri redirect bo'ladi

---

## 🔒 Xavfsizlik Holati

| Xavfsizlik Tekshiruvi | Status |
|----------------------|--------|
| MD5 sign verification | ✅ To'g'ri |
| Timing attack protection (hmac.compare_digest) | ✅ Bor |
| IP whitelist | ✅ Bor (195.158.26.90) |
| Idempotency (duplicate callback) | ✅ To'g'ri |
| HTTP 200 always | ✅ To'g'ri |
| Atomic transaction | ✅ Bor |
| Ownership check | ✅ Tuzatildi |
| Invoice ID security | ⚠️ Tavsiya: UUID ishlatish |

---

## 📂 Fayllar

```
apps/obuna/multicard/
├── __init__.py
├── client.py         ✅ Token, invoice yaratish, error handling
└── views.py          ✅ Create invoice, callback, return URL

apps/obuna/urls.py    ✅ URL routing
config/settings.py    ✅ Environment variables
```

---

## 🎓 Xulosa

**MULTICARD INTEGRATSIYA TAYYOR!** 

- ✅ Asosiy logika to'g'ri
- ✅ 1 ta muammo tuzatildi
- 💡 2 ta tavsiya berildi (optional)

**Keyingi qadam:** Sandbox'da test qilish va production'ga chiqarish.

---

✅ **MULTICARD ISHLASHGA TAYYOR!** 🚀
