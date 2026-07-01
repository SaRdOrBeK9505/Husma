# Admin Autentifikatsiya Tizimi

Bu loyihada **3 ta alohida autentifikatsiya tizimi** mavjud. Har biri bir-biriga aralashmaydi.

---

## 1. 👤 Telegram User Auth (oddiy foydalanuvchilar)

**Kim uchun:** Oddiy foydalanuvchilar (ariza beruvchilar)

**Qanday kiradi:**
- Telegram WebApp orqali
- `initData` orqali autentifikatsiya
- Username/password **KERAK EMAS**

**Endpoint:** `POST /api/auth/telegram/`

**Role:** `user`

---

## 2. 🏢 Rieltor Auth (ko'chmas mulk agentlari)

**MUHIM:** Rieltorlar **FAQAT Telegram orqali** kiradi. Username va parol kerak emas!

### Registratsiya jarayoni (2 qadam):

#### Qadam 1: Telegram auth
- Avval oddiy user sifatida Telegram orqali login qiling
- Endpoint: `POST /api/auth/telegram/`
- JWT token olinadi (role='user')

#### Qadam 2: OTP so'rovi
**Endpoint:** `POST /api/auth/rieltor/register/otp-sorov/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "full_name": "Ali Valiyev",
  "phone": "+998901234567",
  "hududlar": [1, 2],
  "mulk_turlari": [1, 3]
}
```

- Telegramga 6 xonali kod yuboriladi (5 daqiqa amal qiladi)
- ⚠️ Username va parol **KERAK EMAS**

#### Qadam 3: OTP tasdiqlash
**Endpoint:** `POST /api/auth/rieltor/register/otp-verify/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "kode": "123456"
}
```

**Natija:**
- User role='makler'ga o'tadi
- MaklerProfil yaratiladi
- 7 kunlik bepul sinov muddati beriladi
- ⚠️ **Yangi token chiqarilmaydi** - eski token davom etadi

### Rieltor login:
- Har doim `POST /api/auth/telegram/` orqali kiradi
- Username/password login **YO'Q**

---

## 3. 🔐 Admin Auth (tizim administratorlari)

**Kim uchun:** Django admin panel foydalanuvchilari

**Qanday kiradi:**
- Faqat username va parol bilan
- Telegram ID **kerak emas**

**Role:** `admin` yoki `is_staff=True`

### Admin yaratish (3 usul):

#### ✅ Usul 1: Custom command (TAVSIYA ETILADI)

```bash
# Argument bilan:
python manage.py create_admin --username admin --password SecurePass123!

# Yoki interaktiv:
python manage.py create_admin
```

#### Usul 2: Django admin panel orqali

1. Django admin panelga kiring: http://127.0.0.1:8000/admin/
2. "Users" -> "Add user" ni bosing
3. Formani to'ldiring:
   - **Username:** majburiy (masalan: `superadmin`)
   - **Full name:** ixtiyoriy
   - **Parol:** majburiy - 2 marta kiriting
   - **Role:** `admin` tanlang
   - **is_staff:** ✅ belgilang
   - **is_superuser:** ✅ belgilang (barcha huquq uchun)
4. "Save" ni bosing

#### Usul 3: Django shell orqali

```python
python manage.py shell

from apps.users.models import CustomUser

user = CustomUser.objects.create(
    username='admin',
    role='admin',
    is_staff=True,
    is_superuser=True,
    full_name='Super Admin',
    telegram_id=None,
)
user.set_password('SecurePass123!')
user.save()
```

### Admin login (API orqali):

**Endpoint:** `POST /api/admin/auth/login/`

**Request:**
```json
{
  "username": "admin",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "admin": {
    "id": 2,
    "username": "admin",
    "full_name": "Super Admin",
    "role": "admin",
    "is_staff": true,
    "is_superuser": true
  }
}
```

### Admin endpointlar:
- `POST /api/admin/auth/login/` - Login
- `GET /api/admin/auth/me/` - O'z profilini ko'rish (JWT kerak)
- `POST /api/admin/auth/change-password/` - Parolni o'zgartirish (JWT kerak)

### Parolni o'zgartirish:

**Endpoint:** `POST /api/admin/auth/change-password/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "old_password": "SecurePass123!",
  "new_password": "NewSecurePass456!",
  "new_password_confirm": "NewSecurePass456!"
}
```

**Response:**
```json
{
  "message": "Parol muvaffaqiyatli o'zgartirildi. Iltimos qaytadan login qiling."
}
```

---

## 🔑 JWT Token Custom Claims

Barcha tokenlar quyidagi custom claim'larga ega:

```json
{
  "user_id": 1,
  "role": "admin",      // yoki "user", "makler"
  "is_staff": true,
  "username": "admin"   // agar mavjud bo'lsa
}
```

**Fayl:** `apps/users/tokens.py`

---

## 🛡️ Permission Classes

**Fayl:** `apps/users/permissions.py`

- `IsAdminUser` - Faqat admin roleiga ruxsat
- `IsStaffUser` - Faqat staff userga ruxsat
- `IsAdminOrReadOnly` - Admin yozishi mumkin, boshqalar faqat o'qiydi

**Ishlatish:**
```python
from apps.users.permissions import IsAdminUser

class MyView(APIView):
    permission_classes = [IsAdminUser]
```

---

## 🔒 Xavfsizlik

### Rate Limiting
- Auth endpointlar: `AuthRateThrottle`
- OTP so'rovlar: `OtpRateThrottle`
- 5 ta noto'g'ri OTP urinishdan keyin kod bekor qilinadi

### Password Security
- Django default parol tekshirish
- `check_password()` va `set_password()` ishlatiladi
- Parollar hashlanib saqlanadi (pbkdf2_sha256)
- Admin uchun eski parol tekshiriladi

---

## ⚠️ Muhim eslatmalar

1. ❌ **Rieltorlar uchun username/password YO'Q** - faqat Telegram!
2. ✅ **Admin uchun Telegram ID kerak emas** - faqat username va parol
3. 🔐 **Tokenlar role bo'yicha claim'larga ega** - frontend role tekshirishi oson
4. 🎯 **Har bir role uchun alohida endpoint** - aralashish yo'q
5. ⚡ **CustomUser.username unique** - lekin null bo'lishi mumkin (Telegram userlar uchun)

---

## 📚 Swagger/OpenAPI hujjatlari

Barcha endpointlar Swagger UI'da test qilish mumkin:
- **URL:** http://127.0.0.1:8000/api/schema/swagger-ui/

**Tag'lar:**
- `Auth` - User va Rieltor auth  
- `Admin Auth` - Admin auth

---

## 🧪 Testlash (Swagger UI orqali)

### 1. Admin login test:
1. Swagger UI'ni oching: http://127.0.0.1:8000/api/schema/swagger-ui/
2. `Admin Auth` section'ga o'ting
3. `POST /api/admin/auth/login/` ni oching
4. "Try it out" ni bosing
5. Request body'ni to'ldiring:
   ```json
   {
     "username": "admin",
     "password": "sizning_parolingiz"
   }
   ```
6. "Execute" ni bosing
7. Response'dan `access` tokenni nusxalang

### 2. Admin profil test:
1. `GET /api/admin/auth/me/` ni oching
2. "Try it out" ni bosing
3. Yuqoridagi "Authorize" 🔓 tugmasini bosing
4. `Bearer <access_token>` formatida tokenniykiriting
5. "Authorize" ni bosing
6. "Execute" ni bosing

### 3. Parol o'zgartirish test:
1. `POST /api/admin/auth/change-password/` ni oching
2. "Try it out" ni bosing
3. "Authorize" tugmasi orqali token kiriting
4. Request body'ni to'ldiring
5. "Execute" ni bosing

---

## 🔧 Muammolarni hal qilish

### ❌ "UNIQUE constraint failed: users_customuser.username"
**Sabab:** Bu username allaqachon mavjud

**Yechim:**
```bash
# Database'dagi userlarni ko'rish:
python manage.py shell -c "from apps.users.models import CustomUser; users = CustomUser.objects.values('id', 'username', 'telegram_id', 'role'); import json; print(json.dumps(list(users), indent=2, default=str))"

# Boshqa username tanlang yoki mavjud username'ni o'zgartiring
```

### ❌ "Username yoki parol noto'g'ri"
**Yechim:**
```bash
# Username va parolni tekshiring
# User has_password bo'lishi kerak:
python manage.py shell -c "from apps.users.models import CustomUser; u=CustomUser.objects.get(username='admin'); print(f'Has password: {bool(u.password)}')"
```

### ❌ "Sizda admin panel huquqi yo'q"
**Yechim:**
```bash
# User role='admin' yoki is_staff=True bo'lishi kerak:
python manage.py shell -c "from apps.users.models import CustomUser; u=CustomUser.objects.get(username='admin'); print(f'Role: {u.role}\\nis_staff: {u.is_staff}\\nis_superuser: {u.is_superuser}')"
```

---

## 📁 Muhim fayllar

- `apps/users/models.py` - CustomUser modeli
- `apps/users/views.py` - Auth view'lar
- `apps/users/serializers.py` - Auth serializer'lar
- `apps/users/tokens.py` - JWT token generatsiyasi
- `apps/users/permissions.py` - Permission class'lar
- `apps/users/admin.py` - Django admin konfiguratsiyasi
- `apps/users/management/commands/create_admin.py` - Admin yaratish command
