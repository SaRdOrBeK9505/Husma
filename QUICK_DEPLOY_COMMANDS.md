# ⚡ Tezkor Deploy Buyruqlar (Copy-Paste Ready)

Bu faylda barcha buyruqlar ketma-ket joylashgan - copy-paste qilish oson.

---

## 1️⃣ SSH va Server Tayyorlash

```bash
# SSH orqali ulanish (parol so'raydi)
ssh root@185.196.214.123

# Server yangilash
apt update && apt upgrade -y

# Asosiy paketlar
apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib nginx git curl wget \
    build-essential libpq-dev supervisor
```

---

## 2️⃣ PostgreSQL Sozlash

```bash
# PostgreSQL ishga tushirish
systemctl start postgresql
systemctl enable postgresql

# Database yaratish
sudo -u postgres psql << EOF
CREATE DATABASE husma_db;
CREATE USER husma_user WITH PASSWORD 'kuchli_parol_12345_ABC';
ALTER ROLE husma_user SET client_encoding TO 'utf8';
ALTER ROLE husma_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE husma_user SET timezone TO 'Asia/Tashkent';
GRANT ALL PRIVILEGES ON DATABASE husma_db TO husma_user;
\c husma_db
GRANT ALL ON SCHEMA public TO husma_user;
\q
EOF
```

**ESLATMA:** `kuchli_parol_12345_ABC` ni o'zgartiring!

---

## 3️⃣ Foydalanuvchi va Loyiha

```bash
# Foydalanuvchi yaratish
adduser husma
# Parol kiriting: [kuchli_parol]
# Boshqa savollar: Enter bosing

# Foydalanuvchiga o'tish
su - husma

# Git clone (PRIVATE REPO BO'LSA TOKEN KERAK)
cd ~
git clone https://github.com/username/Husma.git
cd Husma
```

---

## 4️⃣ Python Environment

```bash
# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Requirements
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5️⃣ .env Fayl Yaratish

```bash
# .env nusxa olish
cp .env.example .env

# SECRET_KEY generatsiya qilish
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Output'ni copy qiling

# .env tahrirlash
nano .env
```

**.env SHABLONI (to'ldiring):**

```env
SECRET_KEY=django-insecure-[YUQORIDAGI OUTPUT]
DEBUG=False
ALLOWED_HOSTS=yourdomain.uz,www.yourdomain.uz,185.196.214.123

CORS_ALLOWED_ORIGINS=https://yourdomain.uz,https://www.yourdomain.uz

DB_ENGINE=postgresql
DATABASE_NAME=husma_db
DATABASE_USER=husma_user
DATABASE_PASSWORD=kuchli_parol_12345_ABC
DATABASE_HOST=localhost
DATABASE_PORT=5432

TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

PAYME_MERCHANT_ID=
PAYME_KEY=
PAYME_TEST_MODE=False

CLICK_SERVICE_ID=
CLICK_MERCHANT_ID=
CLICK_SECRET_KEY=
CLICK_MERCHANT_USER_ID=

MULTICARD_APPLICATION_ID=
MULTICARD_SECRET=
MULTICARD_STORE_ID=
MULTICARD_TEST_MODE=False
MULTICARD_BASE_URL=https://mesh.multicard.uz
MULTICARD_CALLBACK_URL=https://yourdomain.uz/api/obuna/multicard/callback/
MULTICARD_RETURN_URL=https://yourdomain.uz/api/obuna/multicard/return/
MULTICARD_TIMEOUT=15

FRONTEND_URL=https://yourdomain.uz
```

**CTRL+O, Enter, CTRL+X**

```bash
# Xavfsizlik
chmod 600 .env
```

---

## 6️⃣ Django Sozlamalari

```bash
# Migrations
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

## 7️⃣ Gunicorn Sozlash

```bash
# husma'dan chiqish (root bo'lish kerak)
exit

# Logs papkasi
sudo -u husma mkdir -p /home/husma/Husma/logs

# Systemd service
sudo nano /etc/systemd/system/gunicorn.service
```

**gunicorn.service MATNI:**

```ini
[Unit]
Description=Gunicorn daemon for Husma Django app
After=network.target

[Service]
User=husma
Group=www-data
WorkingDirectory=/home/husma/Husma
Environment="PATH=/home/husma/Husma/venv/bin"
ExecStart=/home/husma/Husma/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/husma/Husma/gunicorn.sock \
          --timeout 60 \
          --access-logfile /home/husma/Husma/logs/gunicorn-access.log \
          --error-logfile /home/husma/Husma/logs/gunicorn-error.log \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

**CTRL+O, Enter, CTRL+X**

```bash
# Gunicorn yoqish
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

---

## 8️⃣ Nginx Sozlash

```bash
sudo nano /etc/nginx/sites-available/husma
```

**Nginx KONFIGURATSIYA (yourdomain.uz ni o'zgartiring):**

```nginx
server {
    listen 80;
    server_name yourdomain.uz www.yourdomain.uz;

    client_max_body_size 20M;

    access_log /var/log/nginx/husma-access.log;
    error_log /var/log/nginx/husma-error.log;

    location /static/ {
        alias /home/husma/Husma/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/husma/Husma/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://unix:/home/husma/Husma/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**CTRL+O, Enter, CTRL+X**

```bash
# Nginx faollashtirish
sudo ln -s /etc/nginx/sites-available/husma /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Ruxsatlar
sudo chown -R husma:www-data /home/husma/Husma/staticfiles
sudo chown -R husma:www-data /home/husma/Husma/media
sudo chmod -R 755 /home/husma/Husma/staticfiles
sudo chmod -R 755 /home/husma/Husma/media
sudo chmod 755 /home/husma
sudo chmod 755 /home/husma/Husma
```

---

## 9️⃣ SSL Sertifikat

```bash
# Certbot o'rnatish
sudo apt install certbot python3-certbot-nginx -y

# DNS tekshirish (domeningiz IP ga yo'naltirilgan bo'lishi kerak)
ping yourdomain.uz

# SSL olish
sudo certbot --nginx -d yourdomain.uz -d www.yourdomain.uz

# Email: sizning@email.com
# Terms: A (Agree)
# Share: N (No)
# Redirect: 2 (Yes)

# Nginx restart
sudo systemctl restart nginx
```

---

## 🔟 Firewall

```bash
sudo apt install ufw -y
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 1️⃣1️⃣ Cron Job

```bash
# husma foydalanuvchiga o'tish
sudo su - husma

# Crontab
crontab -e
# Editor: 1 (nano)
```

**Crontab ichiga:**

```cron
0 0 * * * cd /home/husma/Husma && /home/husma/Husma/venv/bin/python manage.py obunalarni_tekshir >> /home/husma/Husma/logs/cron.log 2>&1
```

**CTRL+O, Enter, CTRL+X**

---

## ✅ Test Qilish

```bash
# Browser'da:
https://yourdomain.uz
https://yourdomain.uz/admin/

# Curl bilan:
curl https://yourdomain.uz/api/
curl https://yourdomain.uz/api/hududlar/
```

---

## 🔧 Muammolarni Hal Qilish

### Gunicorn ishlamayapti

```bash
sudo journalctl -u gunicorn -n 50 --no-pager
sudo systemctl restart gunicorn
```

### Nginx 502 Bad Gateway

```bash
sudo systemctl status gunicorn
sudo chmod 777 /home/husma/Husma/gunicorn.sock
sudo systemctl restart gunicorn nginx
```

### Database connection error

```bash
# PostgreSQL tekshirish
sudo systemctl status postgresql

# .env tekshirish
cat /home/husma/Husma/.env | grep DATABASE

# Qo'lda ulanib ko'rish
psql -U husma_user -d husma_db -h localhost
```

---

## 🔄 Yangilanishlar (Git Pull)

```bash
# husma foydalanuvchi sifatida
cd ~/Husma
git pull origin main

# Virtual env activate
source venv/bin/activate

# Yangi requirements (agar kerak bo'lsa)
pip install -r requirements.txt

# Migrations (agar yangi bo'lsa)
python manage.py migrate

# Static files
python manage.py collectstatic --noinput

# Gunicorn restart
exit  # root'ga qaytish
sudo systemctl restart gunicorn
```

---

## 📊 Monitoring

```bash
# Loglarni kuzatish
sudo tail -f /home/husma/Husma/logs/gunicorn-error.log
sudo tail -f /var/log/nginx/husma-error.log
sudo journalctl -u gunicorn -f

# Xotira va CPU
free -h
top
df -h
```

---

## 🎯 Muhim Fayllar Yo'llari

```
Loyiha:           /home/husma/Husma/
Virtual env:      /home/husma/Husma/venv/
.env:             /home/husma/Husma/.env
Logs:             /home/husma/Husma/logs/
Static:           /home/husma/Husma/staticfiles/
Media:            /home/husma/Husma/media/

Gunicorn service: /etc/systemd/system/gunicorn.service
Nginx config:     /etc/nginx/sites-available/husma
SSL certs:        /etc/letsencrypt/live/yourdomain.uz/

Gunicorn logs:    /home/husma/Husma/logs/gunicorn-*.log
Nginx logs:       /var/log/nginx/husma-*.log
Django logs:      /home/husma/Husma/logs/telegram_auth.log
Cron logs:        /home/husma/Husma/logs/cron.log
```

---

**Deploy vaqti:** ~30-45 daqiqa (SSL kutish bilan)  
**Yaratilgan:** 23-iyun, 2026
