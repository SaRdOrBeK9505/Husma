# 🏠 Husma - Ko'chmas Mulk Platformasi

Telegram Mini App orqali foydalanuvchilar va rieltorlarni bog'lovchi ko'chmas mulk platformasi.

---

## 📋 Loyiha Haqida

**Husma** - O'zbekistonda ko'chmas mulk qidiruvchilar va rieltorlarni bog'lovchi zamonaviy platforma. Foydalanuvchilar ariza qoldirishadi, rieltorlar esa o'z hududlari va ixtisoslashgan mulk turlari bo'yicha arizalarni qabul qilishadi.

### Asosiy Funksiyalar

- 🔐 Telegram WebApp orqali avtorizatsiya
- 📝 Foydalanuvchilar ariza qoldirishlari
- 👔 Rieltorlar arizalarni qabul qilishlari
- 💳 Obuna tizimi (Payme, Multicard integratsiyasi)
- ⭐ Reyting va sharh tizimi
- 📊 Statistika va hisobotlar
- 🗺️ Hudud va mulk turlari boshqaruvi

---

## 🛠️ Texnologiyalar

### Backend
- **Framework:** Django 6.0.5
- **API:** Django REST Framework 3.17.1
- **Authentication:** JWT (Simple JWT)
- **Database:** PostgreSQL 15+
- **Server:** Gunicorn + Nginx
- **API Docs:** drf-spectacular (Swagger/OpenAPI)

### To'lov Tizimlari
- **Payme:** Merchant API integratsiyasi
- **Multicard:** Payment gateway integratsiyasi
- **Click:** (keyingi versiyalarda)

### Xavfsizlik
- HTTPS (SSL/TLS)
- JWT tokenlar (60 daqiqa)
- Rate limiting (10-300 req/min)
- OTP brute-force himoyasi
- CORS sozlamalari
- Security headers (HSTS, XSS, etc)

---

## 📁 Loyiha Tuzilmasi

```
Husma/
├── apps/
│   ├── users/          # Foydalanuvchilar, auth, OTP
│   ├── makler/         # Rieltor profillar
│   ├── ariza/          # Arizalar (user va rieltor tomonlari)
│   ├── obuna/          # Obuna, tariflar, to'lovlar
│   │   ├── payme/      # Payme integratsiya
│   │   └── multicard/  # Multicard integratsiya
│   ├── review/         # Sharhlar va reytinglar
│   ├── hudud/          # Viloyat, tuman, mahalla
│   ├── kvartira/       # Kvartira moduli (keyingi versiya)
│   └── settings/       # Tizim sozlamalari
├── config/             # Django settings, urls, wsgi
├── core/               # Umumiy utilities (pagination, etc)
├── logs/               # Log fayllar
├── media/              # Media fayllar
├── staticfiles/        # Static fayllar (production)
├── .env.example        # Environment variables shabloni
├── requirements.txt    # Python dependencies
└── manage.py           # Django management
```

---

## 🚀 Tezkor Boshlash

### 1. Repository Clone

```bash
git clone https://github.com/username/Husma.git
cd Husma
```

### 2. Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

```bash
cp .env.example .env
nano .env  # To'ldiring
```

### 5. Database

```bash
# PostgreSQL yaratish
createdb husma_db

# Migrations
python manage.py migrate
```

### 6. Initial Data

```bash
python manage.py seed_hudud      # Hududlar
python manage.py seed_tariflar   # Tariflar
python manage.py createsuperuser # Admin
```

### 7. Development Server

```bash
python manage.py runserver
```

Browser: http://127.0.0.1:8000/

---

## 📦 Production Deploy

### Ahost VPS ga Deploy

**To'liq qo'llanma:** `AHOST_DEPLOY_GUIDE.md`  
**Tezkor buyruqlar:** `QUICK_DEPLOY_COMMANDS.md`

**Asosiy qadamlar:**

1. SSH orqali serverga ulanish
2. PostgreSQL o'rnatish
3. Loyiha clone qilish
4. Virtual environment va requirements
5. .env sozlash (secret keylar)
6. Django migrations va static files
7. Gunicorn sozlash
8. Nginx sozlash
9. SSL sertifikat (Let's Encrypt)
10. Firewall va cron jobs

**Deploy vaqti:** ~30-45 daqiqa

---

## 📚 Dokumentatsiya

| Fayl | Tavsif |
|------|--------|
| `AHOST_DEPLOY_GUIDE.md` | To'liq VPS deploy qo'llanmasi (IP dan boshlab) |
| `QUICK_DEPLOY_COMMANDS.md` | Copy-paste buyruqlar (tezkor) |
| `PRODUCTION_CHECKLIST.md` | Production tayorlash ro'yxati |
| `VPS_DEPLOY_GUIDE.md` | Umumiy VPS deploy guide |
| `CHANGELOG_PRODUCTION_READY.md` | Barcha o'zgarishlar tarixi |
| `BLOCKER_FIXES.md` | Tuzatilgan kritik muammolar |
| `CLEANUP_REPORT.md` | Tozalash hisoboti |
| `MULTICARD_FINAL_REPORT.md` | Multicard integratsiya |
| `TAHLIL_NATIJASI.md` | Kod tahlil natijasi |

---

## 🔐 Xavfsizlik

### Production Sozlamalari

```env
DEBUG=False
SECRET_KEY=django-insecure-... # Kuchli key yarating
ALLOWED_HOSTS=yourdomain.uz,www.yourdomain.uz

# Database
DATABASE_PASSWORD=kuchli_parol_123

# To'lov tizimlari
PAYME_TEST_MODE=False
MULTICARD_TEST_MODE=False
```

### Rate Limiting

- **Anonymous:** 60 req/min
- **Authenticated:** 300 req/min
- **Auth endpoints:** 10 req/min
- **OTP endpoints:** 5 req/min

### OTP Himoyasi

- Maksimal 5 ta noto'g'ri urinish
- 5 daqiqa amal qilish muddati
- Telegram orqali yuboriladi

---

## 🧪 Testing

```bash
# Barcha testlar
python manage.py test

# Bitta app
python manage.py test apps.users

# Coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

**Mavjud testlar:**
- `apps/users/tests.py` - 12 ta test (auth, register, login)
- `apps/obuna/tests.py` - 13 ta test (obuna, tarif, Payme)

---

## 📊 API Endpoints

### Swagger UI
```
https://yourdomain.uz/
```

### Asosiy Endpoints

**Auth:**
- `POST /api/auth/` - Telegram auth
- `POST /api/rieltor/register/sorov/` - Rieltor registratsiya (1-qadam)
- `POST /api/rieltor/register/verify/` - OTP verify (2-qadam)
- `POST /api/rieltor/login/` - Rieltor login (username/parol)

**Arizalar:**
- `GET /api/arizalarim/` - User arizalari
- `POST /api/arizalarim/` - Yangi ariza
- `GET /api/rieltor/arizalar/` - Rieltor uchun arizalar
- `POST /api/rieltor/ariza/{id}/qabul/` - Arizani qabul qilish

**Obuna:**
- `GET /api/obuna/tariflar/` - Barcha tariflar
- `POST /api/obuna/multicard/create/` - To'lov yaratish
- `GET /api/obuna/tarix/` - To'lovlar tarixi

**Hudud:**
- `GET /api/viloyatlar/` - Viloyatlar ro'yxati
- `GET /api/tumanlar/` - Tumanlar
- `GET /api/mahallalar/` - Mahallalar

---

## 🔄 Yangilanishlar

### Git Pull va Restart

```bash
# Server'da
cd /home/husma/Husma
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## 🐛 Muammolarni Hal Qilish

### Loglarni Ko'rish

```bash
# Gunicorn
tail -f /home/husma/Husma/logs/gunicorn-error.log

# Nginx
sudo tail -f /var/log/nginx/husma-error.log

# Django
tail -f /home/husma/Husma/logs/telegram_auth.log
```

### Xizmatlarni Restart

```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
sudo systemctl restart postgresql
```

### Database Backup

```bash
pg_dump -U husma_user husma_db > backup_$(date +%Y%m%d).sql
```

---

## 📞 Yordam

**Muammolar:** GitHub Issues  
**Email:** support@yourdomain.uz  
**Telegram:** @your_support_bot

---

## 📝 License

MIT License

---

## 🎯 Keyingi Versiyalar

- [ ] Click to'lov tizimi integratsiyasi
- [ ] Kvartira moduli (CRUD)
- [ ] Real-time bildirishnomalar (WebSocket)
- [ ] Mobile app (Flutter)
- [ ] Analytics dashboard
- [ ] Multi-language (Uz, Ru, En)

---

**Versiya:** 1.0.0  
**Oxirgi yangilanish:** 23-iyun, 2026  
**Status:** ✅ Production Ready
