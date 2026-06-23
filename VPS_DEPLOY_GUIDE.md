# 🚀 VPS Deploy — To'liq Qo'llanma

**Server:** Ubuntu 22.04 LTS (yoki 20.04)  
**Stack:** Nginx + Gunicorn + PostgreSQL + Django  
**SSL:** Let's Encrypt (Certbot)

---

## 📋 Requirements.txt Holati

### ✅ Barcha Kerakli Paketlar Mavjud

| Paket | Versiya | Maqsad |
|-------|---------|--------|
| Django | 6.0.5 | Web framework |
| djangorestframework | 3.17.1 | REST API |
| gunicorn | 23.0.0 | **WSGI server (production)** |
| psycopg2-binary | 2.9.12 | PostgreSQL driver |
| django-cors-headers | 4.9.0 | CORS sozlamalari |
| djangorestframework-simplejwt | 5.5.1 | JWT auth |
| drf-spectacular | 0.29.0 | Swagger/OpenAPI |
| python-dotenv | 1.2.2 | .env file loader |
| requests | 2.34.2 | HTTP client (Multicard) |
| pillow | 12.2.0 | Image processing |

**✅ Hammasi tayyor!**

---

## 🛠️ VPS Sozlash (Step-by-Step)

### Step 1: Server Tayyorlash

```bash
# SSH orqali serverga kirish
ssh root@your_server_ip

# Sistemani yangilash
sudo apt update && sudo apt upgrade -y

# Kerakli paketlar
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y nginx postgresql postgresql-contrib
sudo apt install -y git curl
```

---

### Step 2: PostgreSQL Sozlash

```bash
# PostgreSQL ga kirish
sudo -u postgres psql

# Database yaratish
CREATE DATABASE husma_db;

# User yaratish
CREATE USER husma_user WITH PASSWORD 'KUCHLI_PAROL_QOYING';

# Ruxsatlar berish
ALTER ROLE husma_user SET client_encoding TO 'utf8';
ALTER ROLE husma_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE husma_user SET timezone TO 'Asia/Tashkent';
GRANT ALL PRIVILEGES ON DATABASE husma_db TO husma_user;

# Chiqish
\q
```

**PostgreSQL Remote Access (Agar kerak bo'lsa):**

```bash
# pg_hba.conf ni tahrirlash
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Qo'shing (oxiriga):
# host    husma_db        husma_user      0.0.0.0/0               md5

# postgresql.conf ni tahrirlash
sudo nano /etc/postgresql/14/main/postgresql.conf

# Qo'shing:
# listen_addresses = '*'

# Restart
sudo systemctl restart postgresql
```

---

### Step 3: Loyihani Clone Qilish

```bash
# User yaratish (opsional)
sudo adduser husma
sudo usermod -aG sudo husma
su - husma

# Loyihani clone qilish
cd ~
git clone https://github.com/YOUR_USERNAME/Husma.git
cd Husma

# Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Paketlarni o'rnatish
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 4: .env Faylini Sozlash

```bash
cp .env.example .env
nano .env
```

**Majburiy sozlamalar:**

```env
SECRET_KEY=<50-belgili-tasodifiy-qator>
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

DB_ENGINE=postgresql
DATABASE_NAME=husma_db
DATABASE_USER=husma_user
DATABASE_PASSWORD=<yuqoridagi-parol>
DATABASE_HOST=localhost
DATABASE_PORT=5432

TELEGRAM_BOT_TOKEN=<bot-token>

# Multicard (production)
MULTICARD_APPLICATION_ID=<app-id>
MULTICARD_SECRET=<secret>
MULTICARD_STORE_ID=<store-id>
MULTICARD_TEST_MODE=False
MULTICARD_BASE_URL=https://mesh.multicard.uz
MULTICARD_CALLBACK_URL=https://api.yourdomain.com/api/obuna/multicard/callback/
MULTICARD_RETURN_URL=https://api.yourdomain.com/api/obuna/multicard/return/
FRONTEND_URL=https://yourdomain.com
```

**SECRET_KEY generatsiya:**

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### Step 5: Django Migration

```bash
# Activate venv
source .venv/bin/activate

# Migration
python manage.py makemigrations
python manage.py migrate

# Static files
python manage.py collectstatic --noinput

# Superuser
python manage.py createsuperuser

# Initial data
python manage.py seed_hudud
python manage.py seed_tariflar
```

---

### Step 6: Gunicorn Sozlash

**Test (ishga tushiradimi tekshirish):**

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Agar ishlasa — `Ctrl+C` bilan to'xtating.

**Systemd Service:**

```bash
sudo nano /etc/systemd/system/husma.service
```

**Fayl ichida:**

```ini
[Unit]
Description=Husma Django Application
After=network.target

[Service]
User=husma
Group=www-data
WorkingDirectory=/home/husma/Husma
Environment="PATH=/home/husma/Husma/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
ExecStart=/home/husma/Husma/.venv/bin/gunicorn \
          --workers 4 \
          --bind 127.0.0.1:8000 \
          --access-logfile /home/husma/Husma/logs/gunicorn-access.log \
          --error-logfile /home/husma/Husma/logs/gunicorn-error.log \
          config.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Logs papka yaratish:**

```bash
mkdir -p /home/husma/Husma/logs
```

**Serviceini yoqish:**

```bash
sudo systemctl daemon-reload
sudo systemctl start husma
sudo systemctl enable husma
sudo systemctl status husma
```

---

### Step 7: Nginx Sozlash

```bash
sudo nano /etc/nginx/sites-available/husma
```

**Fayl ichida:**

```nginx
# Upstream — Gunicorn backend
upstream husma_backend {
    server 127.0.0.1:8000;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name api.yourdomain.com yourdomain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates (Certbot qo'shadi)
    # ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Client body size (file upload uchun)
    client_max_body_size 20M;

    # Static files
    location /static/ {
        alias /home/husma/Husma/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/husma/Husma/media/;
        expires 7d;
    }

    # Django application
    location / {
        proxy_pass http://husma_backend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**Faollashtirish:**

```bash
sudo ln -s /etc/nginx/sites-available/husma /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Step 8: SSL Certificate (Let's Encrypt)

```bash
# Certbot o'rnatish
sudo apt install certbot python3-certbot-nginx -y

# Certificate olish
sudo certbot --nginx -d api.yourdomain.com -d yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

**Certbot avtomatik Nginx config'ni yangilaydi** — SSL sertifikat yo'llarini qo'shadi.

---

### Step 9: Firewall Sozlash

```bash
# UFW o'rnatish (agar yo'q bo'lsa)
sudo apt install ufw

# SSH, HTTP, HTTPS ruxsat berish
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'

# Yoqish
sudo ufw enable

# Holat
sudo ufw status
```

---

### Step 10: Cron Job (Obuna Tekshiruvi)

```bash
crontab -e

# Qo'shing:
0 2 * * * /home/husma/Husma/.venv/bin/python /home/husma/Husma/manage.py obunalarni_tekshir >> /home/husma/Husma/logs/obuna_cron.log 2>&1
```

---

## 🧪 Test Qilish

### 1. Health Check

```bash
curl https://api.yourdomain.com/api/statistika/
```

Javob kelishi kerak:
```json
{
  "bitimlar": 0,
  "rieltor_soni": 0,
  "javob_vaqti": "..."
}
```

### 2. Swagger UI

Brauzerda: `https://api.yourdomain.com/`

### 3. Admin Panel

Brauzerda: `https://api.yourdomain.com/admin/`

### 4. Logs Tekshirish

```bash
# Django logs
sudo journalctl -u husma -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Gunicorn logs
tail -f /home/husma/Husma/logs/gunicorn-error.log
```

---

## 🔧 Troubleshooting

### 502 Bad Gateway

```bash
# Gunicorn ishga tushganini tekshiring
sudo systemctl status husma

# Logs
sudo journalctl -u husma -n 50

# Restart
sudo systemctl restart husma
```

### Permission Error (Static/Media)

```bash
sudo chown -R husma:www-data /home/husma/Husma/staticfiles
sudo chown -R husma:www-data /home/husma/Husma/media
sudo chmod -R 755 /home/husma/Husma/staticfiles
sudo chmod -R 755 /home/husma/Husma/media
```

### Database Connection Failed

```bash
# PostgreSQL ishga tushganini tekshiring
sudo systemctl status postgresql

# .env faylda credentials to'g'riligini tekshiring
cat /home/husma/Husma/.env | grep DATABASE
```

### CORS Error

```bash
# .env da CORS_ALLOWED_ORIGINS to'g'ri formatda:
CORS_ALLOWED_ORIGINS=https://domain1.com,https://domain2.com
# (vergul bilan ajratilgan, bo'sh joy yo'q)

# Restart
sudo systemctl restart husma
```

---

## 📊 Production Checklist

- [ ] PostgreSQL yaratildi va sozlandi
- [ ] `.env` fayli to'ldirildi (`DEBUG=False`)
- [ ] Migration o'tkazildi (`migrate`)
- [ ] Static files to'plandi (`collectstatic`)
- [ ] Superuser yaratildi
- [ ] Initial data seed qilindi (`seed_hudud`, `seed_tariflar`)
- [ ] Gunicorn service ishga tushdi
- [ ] Nginx sozlandi
- [ ] SSL certificate o'rnatildi
- [ ] Firewall sozlandi (80, 443, 22)
- [ ] Cron job qo'shildi
- [ ] Logs tekshirildi (xatolar yo'q)
- [ ] Health check test o'tdi
- [ ] Admin panel ochiladi
- [ ] Frontend bilan integratsiya test qilindi

---

## 🎯 Yakuniy Komandalar

```bash
# Loyihani yangilash (git pull qilganda)
cd /home/husma/Husma
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart husma

# Backup (har kuni)
pg_dump -U husma_user husma_db > /home/husma/backups/husma_$(date +%Y%m%d).sql
```

---

✅ **VPS TAYYOR!** 🚀
