# 🔧 Production Tayyorgarlik — O'zgarishlar

**Sana:** 2026-06-23  
**Maqsad:** Loyihani VPS serverga deploy qilish uchun tayyorlash

---

## ✨ Yangi Funksiyalar

### Admin Autentifikatsiya Tizimi (2026-07-01)
**Fayllar:** `apps/users/views.py`, `apps/users/tokens.py`, `apps/users/permissions.py`, `apps/users/serializers.py`

**Qo'shilgan:**
- `POST /api/admin/auth/login/` — Admin username/parol bilan kirish
- `GET /api/admin/auth/me/` — Admin profil
- JWT token'da custom claims: `role`, `is_staff`, `username`
- Permission classes: `IsAdminUser`, `IsStaffUser`, `IsAdminOrReadOnly`
- `CustomUser.username` maydoni unique qilindi

**Ishlash tartibi:**
1. Admin CLI orqali yaratiladi: `python manage.py createsuperuser`
2. Login qilganda JWT token oladi
3. Token'da `role='admin'` va `is_staff=True` claim'lari bor
4. Admin endpointlar `IsAdminUser` permission bilan himoyalangan

**Qo'llanma:** `ADMIN_AUTH_README.md` faylida batafsil

---

## 🐛 Tuzatilgan Bug'lar

### 1. Race Condition — Ariza Qabul Qilish (KRITIK)
**Fayl:** `apps/ariza/views.py` → `RieltorArizaQabulView.post()`

**Muammo:** Ikki rieltor bir vaqtda bir arizani qabul qilsa, ikkalasi ham `BOGLANDI` holatiga o'tadi.

**Tuzatish:**
```python
with transaction.atomic():
    ariza = Ariza.objects.select_for_update().get(pk=pk)
    if ariza.holat != Ariza.Holat.YANGI:
        return Response({'error': ...}, 400)
    # ... state transition
```

---

### 2. `ortacha_reyting` Hech Qachon Yangilanmaydi (KRITIK)
**Fayl:** `apps/review/views.py` → `ReviewYaratishView.post()`

**Muammo:** Review yaratilganda rieltor `ortacha_reyting` hech qachon recalculate qilinmaydi, doim 0.00 turadi.

**Tuzatish:**
```python
# Review yaratilgandan keyin
avg = Review.objects.filter(rieltor=review.rieltor).aggregate(o=Avg('yulduz'))['o'] or 0
MaklerProfil.objects.filter(pk=review.rieltor_id).update(ortacha_reyting=round(avg, 2))
```

---

### 3. `jami_bitimlar` Hech Qachon Yangilanmaydi (KRITIK)
**Fayl:** `apps/ariza/views.py` → `RieltorArizaYopishView.post()`

**Muammo:** Ariza yopilganda rieltor `jami_bitimlar` oshirilmaydi, statistika noto'g'ri.

**Tuzatish:**
```python
from django.db.models import F
MaklerProfil.objects.filter(pk=rieltor.pk).update(
    jami_bitimlar=F('jami_bitimlar') + 1
)
```

---

### 4. Yopilgan Arizani O'chirish Mumkin Edi
**Fayl:** `apps/ariza/views.py` → `UserArizaDetailView.delete()`

**Muammo:** Faqat `korilmoqda` bloklangan, `yopilgan` esa o'chirilishi mumkin edi. Bu review va to'lov ma'lumotlarini cascade delete qiladi.

**Tuzatish:**
```python
if ariza.holat in (Ariza.Holat.KORILMOQDA, Ariza.Holat.YOPILGAN):
    return Response({'error': ...}, 400)
```

---

### 5. `StatistikaView` Duplicate va Eskirgan
**Fayl:** `apps/users/views.py` → `StatistikaView` (o'chirildi)

**Muammo:** `javob_vaqti: "2s"` hardcode qilingan, `apps/settings/views.py` da to'g'ri versiya bor.

**Tuzatish:** `users/views.py` dan o'chirildi, `settings/views.py → UserStatistikaView` ishlatiladi. URL `users/urls.py` dan `settings/urls.py` ga ko'chirildi.

---

### 6. `ObunaQuerySet.faol()` vs `Obuna.faolmi` — Off-by-One
**Fayl:** `apps/obuna/models.py`

**Muammo:**
- `faol()`: `tugash_vaqti__gt=now` (strictly >)
- `faolmi`: `now <= tugash_vaqti` (<=, ikkala yo'l ham ishlaydi)

**Tuzatish:** Ikkisi ham `<` ishlatadi (bir xil mantiq):
```python
# QuerySet
tugash_vaqti__gt=now  # now < tugash_vaqti

# Property
timezone.now() < self.tugash_vaqti
```

---

## 🔐 Xavfsizlik Tuzatishlari

### 1. CORS — Barcha Originlardan Ochiq Edi (KRITIK)
**Fayl:** `config/settings.py`

**Muammo:** `CORS_ALLOW_ALL_ORIGINS = True` shartsiz yozilgan, production da xavfli.

**Tuzatish:**
```python
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
        if origin.strip()
    ]
```

---

### 2. Security Headers Kommentda (KRITIK)
**Fayl:** `config/settings.py`

**Muammo:** HSTS, XSS filter, CSRF cookie secure — barchasi kommentda.

**Tuzatish:** Production da yoqildi:
```python
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 yil
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

---

### 3. JWT Access Token — 7 Kun (XAVFLI)
**Fayl:** `config/settings.py`

**Muammo:** `ACCESS_TOKEN_LIFETIME = timedelta(days=7)` — token o'g'irlansa hafta bo'yi ishlatiladi.

**Tuzatish:**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 7 kun emas, 1 soat
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}
```

---

### 4. Rate Limiting Yo'q Edi (KRITIK)
**Fayl:** `apps/users/views.py`

**Muammo:** Auth va OTP endpointlari cheklovsiz — brute force va OTP flood mumkin.

**Tuzatish:**
```python
class AuthRateThrottle(AnonRateThrottle):
    scope = 'auth'  # 10/minute

class OtpRateThrottle(UserRateThrottle):
    scope = 'otp'  # 5/minute

# Views
class TelegramAuthView(RequestLogMixin, APIView):
    throttle_classes = [AuthRateThrottle]

class RieltorOTPSorovView(RequestLogMixin, APIView):
    throttle_classes = [OtpRateThrottle]
```

`settings.py` ga qo'shildi:
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '300/minute',
        'auth': '10/minute',
        'otp': '5/minute',
    },
}
```

---

### 5. `SECRET_KEY` Validatsiya Yo'q (KRITIK)
**Fayl:** `config/settings.py`

**Muammo:** Agar `.env` da `SECRET_KEY` bo'lmasa, Django `SECRET_KEY=None` bilan ishga tushadi va barcha signature buziladi.

**Tuzatish:**
```python
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Iltimos .env faylini tekshiring.")
```

---

### 6. Payme Webhook Kommentda (TO'LOV ISHLAMAYDI)
**Fayl:** `apps/obuna/urls.py`

**Muammo:** `# path('obuna/payme/webhook/', ...)` — Payme callback kelmaydi, to'lov faollashmaydi.

**Tuzatish:** Yoqildi:
```python
path('obuna/payme/webhook/', PaymeWebhookView.as_view(), name='payme-webhook'),
```

---

## ⚡ Performance Yaxshilanishlari

### 1. PostgreSQL Connection Pooling
**Fayl:** `config/settings.py`

**Tuzatish:**
```python
DATABASES = {
    'default': {
        ...
        'CONN_MAX_AGE': 60,  # Connection pooling
    }
}
```

---

## 📝 Fayllar va Konfiguratsiya

### 1. `.gitignore` Yangilandi
**Fayl:** `.gitignore`

**Qo'shildi:**
```
# Dev test scripts
backend_test.py
bot_tekshir.py
frontend_initdata_tekshir.py
initdata_yasash.py
tekshir_live.py
tekshir_real.py
initdata.txt

# Logs
logs/
*.log
```

---

### 2. `.env.example` To'ldirildi
**Fayl:** `.env.example`

**Qo'shildi:** Barcha environment variables (Multicard, CORS, Frontend URL, etc.)

---

### 3. Production Checklist Yaratildi
**Fayl:** `PRODUCTION_CHECKLIST.md`

Deploy qadamlari, xavfsizlik tekshiruvi, troubleshooting.

---

## 🔄 URL va View O'zgarishlari

| Endpoint | Eski Joy | Yangi Joy | Sabab |
|----------|---------|----------|-------|
| `/api/statistika/` | `users.views.StatistikaView` | `settings.views.UserStatistikaView` | Duplicate, hardcoded `javob_vaqti` |

---

## ✅ Production Tayyor

Loyihani VPS serverga deploy qilish mumkin. Barcha kritik bug'lar tuzatildi, xavfsizlik sozlamalari yoqildi, rate limiting qo'shildi.

**Keyingi qadam:** `PRODUCTION_CHECKLIST.md` ga qarang.
