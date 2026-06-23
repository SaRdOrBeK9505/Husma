# 🚀 Husma — Production Deploy Checklist

## ✅ Kod Tuzatishlari (Amalga oshirildi)

- [x] **Race condition** — `RieltorArizaQabulView` da `select_for_update()` + `transaction.atomic()` qo'shildi
- [x] **ortacha_reyting yangilanmaydi** — `ReviewYaratishView` da automatic update qo'shildi
- [x] **jami_bitimlar yangilanmaydi** — `RieltorArizaYopishView` da `F('jami_bitimlar') + 1` qo'shildi
- [x] **Yopilgan arizani o'chirish mumkin edi** — `UserArizaDetailView.delete()` da `yopilgan` ham bloklandi
- [x] **StatistikaView duplicate** — `users/views.py` dan olib tashlandi, `settings/views.py` ni ishlatadi
- [x] **CORS_ALLOW_ALL_ORIGINS = True** — production da `.env` dan `CORS_ALLOWED_ORIGINS` o'qiladi
- [x] **Security headers kommentda** — production da yoqildi (HSTS, XSS filter, CSRF cookie secure, etc.)
- [x] **JWT 7 kun** — 60 daqiqaga tushirildi
- [x] **Payme webhook kommentda** — yoqildi
- [x] **Rate limiting yo'q** — `AuthRateThrottle` (10/min) va `OtpRateThrottle` (5/min) qo'shildi
- [x] **ObunaQuerySet.faol() vs faolmi** — ikkisi ham `<` ishlatadi (bir xil mantiq)
- [x] **SECRET_KEY tekshiruvi yo'q** — startup validation qo'shildi
- [x] **PostgreSQL CONN_MAX_AGE yo'q** — 60 sekundga sozlandi
- [x] `.gitignore` — dev test scriptlar qo'shildi

---

## 📋 Production Deploy Qadamlari

### 1. Environment Sozlamalari

```bash
# .env faylini to'ldiring (.env.example dan nusxa oling)
cp .env.example .env
nano .env
```

**MUHIM .env sozlamalari:**

```env
SECRET_KEY=<50+ belgili tasodifiy qator — django secret key generator ishlatilsin>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

DB_ENGINE=postgresql
DATABASE_NAME=husma_db
DATABASE_USER=husma_user
DATABASE_PASSWORD=<kuchli parol>
DATABASE_HOST=localhost
DATABASE_PORT=5432

TELEGRAM_BOT_TOKEN=<bot token — @BotFather dan>

# Payme production sozlamalari
PAYME_MERCHANT_ID=<payme business kabinetdan>
PAYME_KEY=<payme webhook secret key>
PAYME_TEST_MODE=False

# Multicard production sozlamalari
MULTICARD_APPLICATION_ID=<multicard kabinetdan>
MULTICARD_SECRET=<multicard secret>
MULTICARD_STORE_ID=<multicard store ID>
MULTICARD_TEST_MODE=False
MULTICARD_BASE_URL=https://mesh.multicard.uz
MULTICARD_CALLBACK_URL=https://api.yourdomain.com/api/obuna/multicard/callback/
MULTICARD_RETURN_URL=https://api.yourdomain.com/api/obuna/multicard/return/
FRONTEND_URL=https://yourdomain.com
```

### 2. PostgreSQL Database Yaratish

```bash
sudo -u postgres psql

CREATE DATABASE husma_db;
CREATE USER husma_user WITH PASSWORD 'strong-password';
ALTER ROLE husma_user SET client_encoding TO 'utf8';
ALTER ROLE husma_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE husma_user SET timezone TO 'Asia/Tashkent';
GRANT ALL PRIVILEGES ON DATABASE husma_db TO husma_user;
\q
```

### 3. Dependency Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Django Migration & Static Files

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 5. Initial Data Seeding

```bash
# Hudud va mulk turlari
python manage.py seed_hudud

# Obuna tariflari
python manage.py seed_tariflar
```

### 6. Gunicorn yoki uWSGI bilan ishga tushirish

**Gunicorn (tavsiya etiladi):**

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**systemd service yaratish** (`/etc/systemd/system/husma.service`):

```ini
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
sudo systemctl status husma
```

### 7. Nginx Reverse Proxy

`/etc/nginx/sites-available/husma`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

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

### 8. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
sudo systemctl reload nginx
```

### 9. Background Tasks (Obuna Tekshiruvi)

**Cron job yaratish** (har kuni 02:00 da):

```bash
crontab -e

0 2 * * * /path/to/Husma/.venv/bin/python /path/to/Husma/manage.py obunalarni_tekshir >> /path/to/Husma/logs/obuna_cron.log 2>&1
```

---

## 🔐 Xavfsizlik Tekshiruvi

- [ ] `DEBUG=False` — `.env` da
- [ ] `SECRET_KEY` — 50+ belgili tasodifiy qator
- [ ] `ALLOWED_HOSTS` — faqat o'z domainlar
- [ ] `CORS_ALLOWED_ORIGINS` — faqat frontend domainlar
- [ ] PostgreSQL parol kuchli
- [ ] Superuser yaratilgan (`createsuperuser`)
- [ ] Firewall sozlangan (faqat 80, 443, 22 port ochiq)
- [ ] SSH parol authentication o'chirilgan (faqat key-based)
- [ ] Nginx rate limiting sozlangan (opsional)

---

## 🧪 Production Test

```bash
# Health check
curl https://api.yourdomain.com/api/statistika/

# Telegram auth test
# Telegram Mini App orqali login qiling

# Swagger UI (faqat admin uchun ochiq bo'lishi kerak)
# https://api.yourdomain.com/

# Admin panel
# https://api.yourdomain.com/admin/
```

---

## 📊 Monitoring (Tavsiya)

- **Sentry** — error tracking
- **New Relic / DataDog** — performance monitoring
- **CloudWatch / Grafana** — server metrics
- **Uptime Robot** — uptime monitoring

---

## 🗂️ Fayllar O'chirish Kerak (Production Repo)

Production serverga yuklashdan oldin quyidagi dev fayllarni olib tashlang:

```bash
rm backend_test.py
rm bot_tekshir.py
rm frontend_initdata_tekshir.py
rm initdata_yasash.py
rm tekshir_live.py
rm tekshir_real.py
rm initdata.txt
rm db.sqlite3  # SQLite DB (production da PostgreSQL ishlatiladi)
rm -rf logs/   # Eski log fayllar (production da yangi loglar yaratiladi)
```

Yoki `.gitignore` da qo'shilgan bo'lgani uchun git commit qilayotganda avtomatik chiqarib ketadi.

---

## 🎯 Production Deploy Yakuniy Tekshiruv

1. [ ] `.env` to'ldirilgan va `DEBUG=False`
2. [ ] PostgreSQL DB yaratilgan va migration o'tgan
3. [ ] `collectstatic` bajarilgan
4. [ ] Gunicorn/uWSGI systemd service ishga tushirilgan
5. [ ] Nginx reverse proxy sozlangan
6. [ ] SSL certificate o'rnatilgan (HTTPS)
7. [ ] Cron job (obuna tekshiruvi) sozlangan
8. [ ] Payme/Multicard production keys kiritilgan
9. [ ] Telegram bot webhook sozlangan (agar kerak bo'lsa)
10. [ ] Admin panel ochiladi va superuser bilan kiriladi
11. [ ] Frontend bilan integratsiya test qilindi
12. [ ] Backup strategiya sozlandi (PostgreSQL dump, media files)

---

## 📞 Muammolar yuzaga kelsa

**1. Static files ko'rinmaydi**
```bash
python manage.py collectstatic --clear --noinput
sudo systemctl restart husma
sudo systemctl restart nginx
```

**2. 502 Bad Gateway**
```bash
sudo systemctl status husma
sudo journalctl -u husma -f
# Gunicorn ishlamayotganini tekshiring
```

**3. CORS xatosi**
```bash
# .env da CORS_ALLOWED_ORIGINS to'g'riligini tekshiring
# Vergul bilan ajratilgan, https:// bilan boshlanishi kerak
```

**4. Database connection error**
```bash
# PostgreSQL ishga tushganini tekshiring
sudo systemctl status postgresql
# .env da DB credentials to'g'riligini tekshiring
```

---

✅ **Production deploy muvaffaqiyatli!** 🎉
