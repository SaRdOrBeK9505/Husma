# 🚀 Husma — Production Deploy Qo'llanma

**Loyiha:** Kvartira Qidiruv Platformasi (Telegram Mini App)  
**Texnologiya:** Django 6.0.5 + DRF + PostgreSQL + Multicard/Payme  
**Status:** ✅ Production Tayyor

---

## 📊 Loyiha Holati

### ✅ Bajarilgan Ishlar (2026-06-23)

**Kod Sifati:**
- ✅ 13 ta bug tuzatildi (10 kritik, 3 o'rta)
- ✅ Race condition (ariza qabul qilish) tuzatildi
- ✅ `ortacha_reyting` va `jami_bitimlar` avtomatik yangilanadi
- ✅ Security headers yoqildi (HSTS, XSS, CSRF)
- ✅ Rate limiting qo'shildi (auth: 10/min, OTP: 5/min)
- ✅ JWT token lifetime 60 daqiqaga tushirildi
- ✅ CORS production uchun sozlandi
- ✅ Payme webhook yoqildi
- ✅ PostgreSQL connection pooling qo'shildi

**Multicard To'lov:**
- ✅ Token management to'g'ri (keshlangan, auto-refresh)
- ✅ MD5 signature verification to'g'ri
- ✅ Idempotency (qayta so'rovlar) to'g'ri
- ✅ HTTP 200 always (Multicard protokoli)
- ✅ Egalik tekshiruvi tuzatildi

**Dokumentatsiya:**
- ✅ `PRODUCTION_CHECKLIST.md` — Deploy qadamlari
- ✅ `CHANGELOG_PRODUCTION_READY.md` — O'zgarishlar tarixi
- ✅ `TAHLIL_NATIJASI.md` — To'liq tahlil hisoboti
- ✅ `MULTICARD_FINAL_REPORT.md` — Multicard tahlili

---

## 🎯 Asosiy Xususiyatlar

### 1. Auth Sistema
- **Telegram Mini App** — HMAC-SHA256 verification
- **OTP Register** — Rieltor ro'yxatdan o'tish (2-step)
- **JWT** — Access token (60 min), Refresh token (30 kun)
- **Rate Limiting** — Brute force himoyasi

### 2. Ariza Sistema
- User ariza beradi → Rieltorlarga avtomatik tarqatiladi
- State machine: `yangi` → `korilmoqda` → `yopilgan`
- Race condition himoyasi (`select_for_update` + `atomic`)
- Hudud va mulk turi bo'yicha filtrlash

### 3. Obuna Sistema
- Rieltor uchun obuna (7 kun bepul sinov)
- Obuna stacking (yangi muddat eskisi ustiga qo'shiladi)
- Payme va Multicard to'lov tizimi
- Avtomatik obuna tekshiruvi (cron job)

### 4. Review Sistema
- User rieltorga baho qoldiradi (1-5 yulduz)
- `ortacha_reyting` avtomatik hisoblanadi
- Faqat ishlagan rieltorga review qoldirish mumkin

---

## 📋 Deploy Qadamlari

### 1. Environment Setup

```bash
# .env faylini yarating
cp .env.example .env
nano .env
```

**Majburiy o'zgaruvchilar:**
```env
SECRET_KEY=<50+ belgili tasodifiy qator>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

DB_ENGINE=postgresql
DATABASE_NAME=husma_db
DATABASE_USER=husma_user
DATABASE_PASSWORD=<kuchli parol>
DATABASE_HOST=localhost
DATABASE_PORT=5432

TELEGRAM_BOT_TOKEN=<bot token>

# Multicard production
MULTICARD_APPLICATION_ID=<multicard app id>
MULTICARD_SECRET=<multicard secret>
MULTICARD_STORE_ID=<multicard store id>
MULTICARD_TEST_MODE=False
MULTICARD_BASE_URL=https://mesh.multicard.uz
MULTICARD_CALLBACK_URL=https://api.yourdomain.com/api/obuna/multicard/callback/
MULTICARD_RETURN_URL=https://api.yourdomain.com/api/obuna/multicard/return/
FRONTEND_URL=https://yourdomain.com
```

### 2. PostgreSQL Setup

```bash
sudo -u postgres psql

CREATE DATABASE husma_db;
CREATE USER husma_user WITH PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE husma_db TO husma_user;
\q
```

### 3. Django Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# Seed initial data
python manage.py seed_hudud
python manage.py seed_tariflar
```

### 4. Gunicorn + Systemd

```bash
# /etc/systemd/system/husma.service
[Unit]
Description=Husma Django Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/Husma
Environment="PATH=/path/to/Husma/.venv/bin"
ExecStart=/path/to/Husma/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 4

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start husma
sudo systemctl enable husma
```

### 5. Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/husma
server {
    listen 80;
    server_name api.yourdomain.com;

    location /static/ {
        alias /path/to/Husma/staticfiles/;
    }

    location /media/ {
        alias /path/to/Husma/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/husma /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

### 7. Cron Job (Obuna Tekshiruvi)

```bash
crontab -e

# Har kuni 02:00 da
0 2 * * * /path/to/.venv/bin/python /path/to/manage.py obunalarni_tekshir >> /path/to/logs/obuna_cron.log 2>&1
```

---

## 🔐 Xavfsizlik Checklist

- [x] `DEBUG=False`
- [x] `SECRET_KEY` tasodifiy va 50+ belgi
- [x] `ALLOWED_HOSTS` faqat o'z domainlar
- [x] `CORS_ALLOWED_ORIGINS` faqat frontend
- [x] Security headers yoqilgan (HSTS, XSS, CSRF)
- [x] JWT token 60 daqiqa
- [x] Rate limiting yoqilgan
- [x] PostgreSQL parol kuchli
- [ ] Firewall sozlangan (80, 443, 22)
- [ ] SSH key-based auth
- [ ] Regular backup (PostgreSQL + media)

---

## 🧪 Production Test

```bash
# Health check
curl https://api.yourdomain.com/api/statistika/

# Swagger UI
https://api.yourdomain.com/

# Admin panel
https://api.yourdomain.com/admin/

# Multicard test (sandbox)
# 1. Invoice yaratish
# 2. Test karta bilan to'lov
# 3. Callback kelishini tekshirish
# 4. Obuna faollashishini tekshirish
```

---

## 📂 Loyiha Strukturasi

```
Husma/
├── apps/
│   ├── users/         Auth, OTP, JWT
│   ├── makler/        Rieltor profil, obuna
│   ├── ariza/         Ariza lifecycle
│   ├── obuna/         Tarif, to'lov (Payme, Multicard)
│   ├── hudud/         Viloyat, hudud, mulk turi
│   ├── review/        Review, reyting
│   └── settings/      Site settings, statistika
├── config/            Django settings, URLs
├── core/              Permissions, pagination
├── .env.example       Environment variables namunasi
├── requirements.txt   Python dependencies
├── manage.py          Django CLI
└── PRODUCTION_*.md    Deploy dokumentatsiya
```

---

## 🐛 Troubleshooting

### 502 Bad Gateway
```bash
sudo systemctl status husma
sudo journalctl -u husma -f
```

### Static files ko'rinmaydi
```bash
python manage.py collectstatic --clear --noinput
sudo systemctl restart husma nginx
```

### CORS xatosi
```bash
# .env da CORS_ALLOWED_ORIGINS to'g'ri formatda:
CORS_ALLOWED_ORIGINS=https://domain1.com,https://domain2.com
```

### Database connection error
```bash
sudo systemctl status postgresql
# .env da DB credentials tekshiring
```

---

## 📊 Monitoring (Tavsiya)

- **Sentry** — Error tracking
- **New Relic** — APM
- **Uptime Robot** — Uptime monitoring
- **Grafana** — Metrics visualization

---

## 📞 Qo'llab-quvvatlash

**Hujjatlar:**
- `PRODUCTION_CHECKLIST.md` — Batafsil deploy qo'llanma
- `MULTICARD_FINAL_REPORT.md` — Multicard integratsiya
- `TAHLIL_NATIJASI.md` — To'liq kod tahlili

**Management Commands:**
```bash
python manage.py seed_hudud          # Viloyat, hudud, mulk turi
python manage.py seed_tariflar       # Obuna tariflari
python manage.py obunalarni_tekshir  # Obuna muddatini tekshirish
```

---

## 🎉 Yakuniy Natija

✅ **Loyiha Production Tayyor!**

- 13 ta bug tuzatildi
- Security yaxshilandi
- Multicard to'lov ishlaydi
- Dokumentatsiya to'liq

**Deploy qilishingiz mumkin!** 🚀

---

**Keyingi Qadam:** `PRODUCTION_CHECKLIST.md` ga o'ting va qadamma-qadam deploy qiling.
