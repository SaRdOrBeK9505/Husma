# 🚀 Ahost VPS'ga Django Loyihani To'liq Yuklash (IP'dan boshlab)

**Maqsad:** Husma loyihasini Ahost VPS serveriga to'liq deploy qilish  
**Muhit:** Ubuntu 22.04 / 20.04 LTS  
**Stack:** Django + PostgreSQL + Gunicorn + Nginx + SSL

---

## 📋 BOSQICHLAR RO'YXATI

1. [SSH orqali serverga ulanish](#1-ssh-orqali-serverga-ulanish)
2. [Server yangilash va asosiy paketlar](#2-server-yangilash-va-asosiy-paketlar)
3. [PostgreSQL o'rnatish va sozlash](#3-postgresql-ornatish-va-sozlash)
4. [Loyiha uchun foydalanuvchi yaratish](#4-loyiha-uchun-foydalanuvchi-yaratish)
5. [Git orqali loyihani clone qilish](#5-git-orqali-loyihani-clone-qilish)
6. [Python virtual environment](#6-python-virtual-environment)
7. [.env fayl yaratish va secret keylar](#7-env-fayl-yaratish-va-secret-keylar)
8. [Django sozlamalari (migrate, static, superuser)](#8-django-sozlamalari)
9. [Gunicorn sozlash](#9-gunicorn-sozlash)
10. [Nginx sozlash](#10-nginx-sozlash)
11. [SSL sertifikat (Let's Encrypt)](#11-ssl-sertifikat-lets-encrypt)
12. [Firewall sozlash](#12-firewall-sozlash)
13. [Cron job (obuna tekshirish)](#13-cron-job-obuna-tekshirish)
14. [Testing va monitoring](#14-testing-va-monitoring)

---

## 1. SSH orqali serverga ulanish

### 1.1. Ahost'dan server ma'lumotlarini oling

Ahost panelingizdan quyidagilarni ko'chirib oling:
- **IP Address:** Masalan: `185.196.214.123`
- **SSH Port:** Odatda `22` (ba'zan `2222` yoki boshqa)
- **Username:** `root` yoki sizga berilgan username
- **Password:** Ahost panelingizda

### 1.2. SSH client orqali ulaning

**Windows (PowerShell):**
```powershell
ssh root@185.196.214.123
# Yoki port boshqa bo'lsa:
ssh -p 2222 root@185.196.214.123
```

**Birinchi ulanishda:**
```
The authenticity of host '185.196.214.123' can't be established.
Are you sure you want to continue connecting (yes/no)? yes
```

**Parolni kiriting** (ko'rinmaydi, shunchaki yozing va Enter bosing)

### 1.3. Muvaffaqiyatli ulangansiz!

```bash
root@server:~# 
```

---

## 2. Server yangilash va asosiy paketlar

### 2.1. Sistema yangilanishlarini o'rnatish

```bash
# Paket ro'yxatini yangilash
apt update

# Mavjud paketlarni yangilash
apt upgrade -y

# Asosiy paketlarni o'rnatish
apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib nginx git curl wget \
    build-essential libpq-dev supervisor
```

**Kutish vaqti:** ~5-10 daqiqa (internet tezligiga bog'liq)

### 2.2. Python versiyasini tekshirish

```bash
python3 --version
# Output: Python 3.10.x yoki 3.11.x
```

---

## 3. PostgreSQL o'rnatish va sozlash

### 3.1. PostgreSQL xizmatini ishga tushirish

```bash
# Xizmatni yoqish
systemctl start postgresql
systemctl enable postgresql

# Holatni tekshirish
systemctl status postgresql
# Ko'k "active (running)" ko'rish kerak
# 'q' bosib chiqing
```

### 3.2. Database va foydalanuvchi yaratish

```bash
# PostgreSQL'ga kirish
sudo -u postgres psql

# Quyidagi buyruqlarni psql ichida bajaring:
```

**PostgreSQL ichida:**
```sql
-- Database yaratish
CREATE DATABASE husma_db;

-- Foydalanuvchi yaratish
CREATE USER husma_user WITH PASSWORD 'kuchli_parol_12345_ABC';

-- Ruxsatlar berish
ALTER ROLE husma_user SET client_encoding TO 'utf8';
ALTER ROLE husma_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE husma_user SET timezone TO 'Asia/Tashkent';
GRANT ALL PRIVILEGES ON DATABASE husma_db TO husma_user;

-- PostgreSQL 15+ uchun qo'shimcha ruxsat
\c husma_db
GRANT ALL ON SCHEMA public TO husma_user;

-- Chiqish
\q
```

**MUHIM:** `kuchli_parol_12345_ABC` o'rniga o'zingizning kuchli parolingizni yozing!

### 3.3. Parolni eslab qoling!

```
Database Name: husma_db
Database User: husma_user
Database Password: kuchli_parol_12345_ABC
```

---

## 4. Loyiha uchun foydalanuvchi yaratish

### 4.1. Yangi foydalanuvchi yaratish

```bash
# husma nomli foydalanuvchi yaratish
adduser husma

# Parol so'raydi - kuchli parol kiriting
# Full Name va boshqa ma'lumotlar - Enter bosib o'tkazing

# sudo ruxsati berish (kerak bo'lsa)
usermod -aG sudo husma
```

### 4.2. Foydalanuvchiga o'tish

```bash
su - husma
```

Endi siz `husma` foydalanuvchisiz:
```bash
husma@server:~$
```

---

## 5. Git orqali loyihani clone qilish

### 5.1. Home papkasiga loyihani clone qilish

```bash
cd ~
pwd
# Output: /home/husma

# GitHub'dan clone (agar private repo bo'lsa, token kerak)
git clone https://github.com/sizning-username/Husma.git

# Yoki agar public bo'lsa:
# git clone https://github.com/username/Husma.git
```

**Agar private repository bo'lsa:**

```bash
# GitHub Personal Access Token yarating:
# GitHub.com → Settings → Developer settings → Personal access tokens → Generate new token
# 'repo' ruxsatini bering

# Clone qilish:
git clone https://<TOKEN>@github.com/username/Husma.git

# Yoki SSH key orqali:
ssh-keygen -t ed25519 -C "sizning@email.com"
cat ~/.ssh/id_ed25519.pub
# Bu chiqgan kalitni GitHub → Settings → SSH keys ga qo'shing
git clone git@github.com:username/Husma.git
```

### 5.2. Loyiha papkasiga kirish

```bash
cd Husma
ls -la
# manage.py, requirements.txt va boshqalar ko'rinishi kerak
```

---

## 6. Python virtual environment

### 6.1. Virtual environment yaratish

```bash
# Husma papkasida:
python3 -m venv venv

# Activate qilish
source venv/bin/activate

# (venv) ko'rinishi kerak:
(venv) husma@server:~/Husma$
```

### 6.2. Requirements o'rnatish

```bash
# pip yangilash
pip install --upgrade pip

# Requirements o'rnatish
pip install -r requirements.txt
```

**Kutish vaqti:** ~5-10 daqiqa

**Agar xato bo'lsa:**
```bash
# psycopg2 xatosi:
sudo apt install libpq-dev python3-dev -y
pip install psycopg2-binary

# Pillow xatosi:
sudo apt install libjpeg-dev zlib1g-dev -y
pip install Pillow
```

---

## 7. .env fayl yaratish va secret keylar

### 7.1. .env.example'dan nusxa olish

```bash
cp .env.example .env
nano .env
```

### 7.2. Django SECRET_KEY yaratish

**Yangi terminal ochib (Windows PowerShell yoki Git Bash):**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Yoki serverda:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Output misol:**
```
django-insecure-7x#m2$w@9k_abc123...xyz789
```

### 7.3. .env faylini to'ldirish

**nano .env ichida:**

```env
# ===== ASOSIY SOZLAMALAR =====
SECRET_KEY=django-insecure-7x#m2$w@9k_abc123...xyz789
DEBUG=False
ALLOWED_HOSTS=yourdomain.uz,www.yourdomain.uz,185.196.214.123

# ===== CORS =====
CORS_ALLOWED_ORIGINS=https://yourdomain.uz,https://www.yourdomain.uz

# ===== DATABASE =====
DB_ENGINE=postgresql
DATABASE_NAME=husma_db
DATABASE_USER=husma_user
DATABASE_PASSWORD=kuchli_parol_12345_ABC
DATABASE_HOST=localhost
DATABASE_PORT=5432

# ===== TELEGRAM BOT =====
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789

# ===== PAYME (PRODUCTION) =====
# Payme kabinetdan oling: https://checkout.paycom.uz
PAYME_MERCHANT_ID=your_merchant_id_here
PAYME_KEY=your_payme_secret_key_here
PAYME_TEST_MODE=False

# ===== CLICK (agar kerak bo'lsa) =====
CLICK_SERVICE_ID=
CLICK_MERCHANT_ID=
CLICK_SECRET_KEY=
CLICK_MERCHANT_USER_ID=

# ===== MULTICARD (PRODUCTION) =====
# Multicard kabinetdan: https://cabinet.multicard.uz
MULTICARD_APPLICATION_ID=your_app_id
MULTICARD_SECRET=your_multicard_secret
MULTICARD_STORE_ID=your_store_id
MULTICARD_TEST_MODE=False
MULTICARD_BASE_URL=https://mesh.multicard.uz
MULTICARD_CALLBACK_URL=https://yourdomain.uz/api/obuna/multicard/callback/
MULTICARD_RETURN_URL=https://yourdomain.uz/api/obuna/multicard/return/
MULTICARD_TIMEOUT=15

# ===== FRONTEND =====
FRONTEND_URL=https://yourdomain.uz
```

**CTRL+O** (saqlash) → **Enter** → **CTRL+X** (chiqish)

### 7.4. .env xavfsizligini ta'minlash

```bash
# Faqat husma foydalanuvchi o'qiy oladi
chmod 600 .env

# Tekshirish
ls -la .env
# Output: -rw------- 1 husma husma ... .env
```

---

## 8. Django sozlamalari

### 8.1. Database migration

```bash
# Virtual environment yoqilganligini tekshiring
source ~/Husma/venv/bin/activate

cd ~/Husma

# Migratsiyalarni ko'rish
python manage.py showmigrations

# Migratsiyalarni qo'llash
python manage.py migrate
```

**Output:**
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying obuna.0005_... OK
```

### 8.2. Static fayllarni yig'ish

```bash
python manage.py collectstatic --noinput
```

**Output:**
```
Copying '...'
...
123 static files copied to '/home/husma/Husma/staticfiles'.
```

### 8.3. Superuser yaratish

```bash
python manage.py createsuperuser
```

**Savollarga javob:**
```
Telegram id: [Enter - bo'sh qoldiring]
Username: admin
Password: [kuchli parol]
Password (again): [kuchli parol]
```

### 8.4. Initial data yuklash

```bash
# Hududlarni yuklash
python manage.py seed_hudud

# Tariflarni yuklash
python manage.py seed_tariflar
```

### 8.5. Test qilish

```bash
# Development serverda test (FAQAT TEST UCHUN!)
python manage.py runserver 0.0.0.0:8000

# Boshqa terminaldan:
curl http://185.196.214.123:8000/api/

# Ctrl+C bosib to'xtating
```

---

## 9. Gunicorn sozlash

### 9.1. Gunicorn test qilish

```bash
cd ~/Husma
source venv/bin/activate

# Test
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Ishlayotganini ko'rsangiz Ctrl+C bosing
```

### 9.2. Gunicorn systemd service yaratish

**root foydalanuvchiga o'ting:**
```bash
exit  # husma'dan chiqish
```

**Systemd service file yaratish:**
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

**Fayl ichiga:**
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

**CTRL+O** → **Enter** → **CTRL+X**

### 9.3. Logs papkasini yaratish

```bash
sudo -u husma mkdir -p /home/husma/Husma/logs
```

### 9.4. Gunicorn xizmatini ishga tushirish

```bash
# Systemd reload
sudo systemctl daemon-reload

# Gunicorn yoqish
sudo systemctl start gunicorn

# Holatni tekshirish
sudo systemctl status gunicorn

# Avtomatik ishga tushirish (reboot bo'lsa)
sudo systemctl enable gunicorn
```

**Status active (running) bo'lishi kerak!**

**Agar xato bo'lsa:**
```bash
# Loglarni ko'rish
sudo journalctl -u gunicorn -n 50 --no-pager

# Yoki
cat /home/husma/Husma/logs/gunicorn-error.log
```

---

## 10. Nginx sozlash

### 10.1. Nginx konfiguratsiya yaratish

```bash
sudo nano /etc/nginx/sites-available/husma
```

**Fayl ichiga (DOMAIN BILAN):**

```nginx
server {
    listen 80;
    server_name yourdomain.uz www.yourdomain.uz;

    client_max_body_size 20M;

    # Logs
    access_log /var/log/nginx/husma-access.log;
    error_log /var/log/nginx/husma-error.log;

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
        add_header Cache-Control "public";
    }

    # Gunicorn proxy
    location / {
        proxy_pass http://unix:/home/husma/Husma/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**CTRL+O** → **Enter** → **CTRL+X**

**MUHIM:** `yourdomain.uz` o'rniga o'z domeningizni yozing!

### 10.2. Nginx konfigni faollashtirish

```bash
# Symlink yaratish
sudo ln -s /etc/nginx/sites-available/husma /etc/nginx/sites-enabled/

# Default konfigni o'chirish (agar kerak bo'lsa)
sudo rm /etc/nginx/sites-enabled/default

# Sintaksisni tekshirish
sudo nginx -t
# Output: syntax is ok

# Nginx restart
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 10.3. Ruxsatlarni sozlash

```bash
# www-data (nginx) media va static o'qiy olishi uchun
sudo chown -R husma:www-data /home/husma/Husma/staticfiles
sudo chown -R husma:www-data /home/husma/Husma/media
sudo chmod -R 755 /home/husma/Husma/staticfiles
sudo chmod -R 755 /home/husma/Husma/media

# Gunicorn socket uchun
sudo chmod 755 /home/husma
sudo chmod 755 /home/husma/Husma
```

---

## 11. SSL sertifikat (Let's Encrypt)

### 11.1. Certbot o'rnatish

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 11.2. Domain DNS ni tekshirish

**MUHIM:** Domeningiz serveringiz IP'siga yo'naltirilgan bo'lishi kerak!

```bash
# DNS tekshirish
ping yourdomain.uz
# IP: 185.196.214.123 (sizning server IP)
```

**Agar yo'naltirilmagan bo'lsa:**
1. Domain provayderingizga kiring (Ahost, Uzinfocom, etc)
2. DNS sozlamalarida A record qo'shing:
   ```
   A     @           185.196.214.123
   A     www         185.196.214.123
   ```
3. 5-10 daqiqa kuting (DNS propagation)

### 11.3. SSL sertifikat olish

```bash
sudo certbot --nginx -d yourdomain.uz -d www.yourdomain.uz
```

**Savollar:**
```
Enter email address: sizning@email.com
Terms of Service: A (Agree)
Share email: N (No)
Redirect HTTP to HTTPS: 2 (Yes)
```

**Muvaffaqiyatli bo'lsa:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/yourdomain.uz/fullchain.pem
```

### 11.4. Avtomatik yangilanish

```bash
# Test qilish
sudo certbot renew --dry-run

# Cron job allaqachon sozlangan (certbot o'rnatish bilan)
```

### 11.5. Nginx'ni qayta ishga tushirish

```bash
sudo systemctl restart nginx
```

---

## 12. Firewall sozlash

### 12.1. UFW (Uncomplicated Firewall) yoqish

```bash
# UFW o'rnatilganligini tekshirish
sudo apt install ufw -y

# SSH ruxsat (JUDA MUHIM!)
sudo ufw allow OpenSSH
sudo ufw allow 22/tcp

# HTTP va HTTPS
sudo ufw allow 'Nginx Full'
# Yoki
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# PostgreSQL faqat localhost (xavfsizlik)
# Tashqi kirish kerak emas

# Firewall yoqish
sudo ufw enable

# Holatni tekshirish
sudo ufw status
```

**Output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

---

## 13. Cron job (obuna tekshirish)

### 13.1. Cron job yaratish

```bash
# husma foydalanuvchiga o'ting
sudo su - husma

# Crontab ochish
crontab -e

# Editor tanlash (birinchi marta): 1 (nano)
```

**Crontab ichiga:**
```cron
# Har kuni soat 00:00 da obunalarni tekshirish
0 0 * * * cd /home/husma/Husma && /home/husma/Husma/venv/bin/python manage.py obunalarni_tekshir >> /home/husma/Husma/logs/cron.log 2>&1

# Har 5 daqiqada health check (opsional)
*/5 * * * * curl -f http://localhost/api/ > /dev/null 2>&1 || sudo systemctl restart gunicorn
```

**CTRL+O** → **Enter** → **CTRL+X**

### 13.2. Cron logini tekshirish

```bash
# Cron ishga tushgandan keyin
cat /home/husma/Husma/logs/cron.log
```

---

## 14. Testing va monitoring

### 14.1. Saytni brauzerda ochish

```
https://yourdomain.uz
```

**Ko'rinishi kerak:** Swagger UI (API documentation)

### 14.2. API testlari

```bash
# Health check
curl https://yourdomain.uz/api/

# Hudud API
curl https://yourdomain.uz/api/hududlar/

# Admin panel
https://yourdomain.uz/admin/
# Login: superuser (yuqorida yaratgan)
```

### 14.3. Loglarni monitoring qilish

```bash
# Gunicorn logs
tail -f /home/husma/Husma/logs/gunicorn-error.log
tail -f /home/husma/Husma/logs/gunicorn-access.log

# Nginx logs
sudo tail -f /var/log/nginx/husma-error.log
sudo tail -f /var/log/nginx/husma-access.log

# Django logs
tail -f /home/husma/Husma/logs/telegram_auth.log

# System logs
sudo journalctl -u gunicorn -f
sudo journalctl -u nginx -f
```

### 14.4. Xotira va CPU monitoring

```bash
# Xotira
free -h

# CPU
top
# 'q' bosib chiqish

# Disk
df -h
```

---

## 🔧 MUAMMOLARNI HAL QILISH

### 502 Bad Gateway

```bash
# Gunicorn ishlamayotgan bo'lishi mumkin
sudo systemctl status gunicorn
sudo systemctl restart gunicorn

# Socket fayliga ruxsat
sudo chmod 777 /home/husma/Husma/gunicorn.sock

# SELinux (agar yoqilgan bo'lsa)
sudo setenforce 0
```

### 500 Internal Server Error

```bash
# Django loglarni tekshiring
tail -f /home/husma/Husma/logs/gunicorn-error.log

# DEBUG=True qilib test qiling (FAQAT TEST UCHUN!)
nano ~/Husma/.env
# DEBUG=True
sudo systemctl restart gunicorn
```

### Static files yuklanmayapti

```bash
# Ruxsatlarni tekshiring
ls -la /home/husma/Husma/staticfiles/

# Qayta yig'ing
cd ~/Husma
source venv/bin/activate
python manage.py collectstatic --noinput

# Nginx restart
sudo systemctl restart nginx
```

### Database connection error

```bash
# PostgreSQL ishga tushganligini tekshiring
sudo systemctl status postgresql

# .env da ma'lumotlarni tekshiring
cat ~/Husma/.env | grep DATABASE

# PostgreSQL'ga ulanib ko'ring
psql -U husma_user -d husma_db -h localhost
# Parol: .env dagi parol
```

---

## 📱 KEYINGI QADAMLAR

### 1. Multicard va Payme sozlash

**Multicard:**
1. https://cabinet.multicard.uz ga kiring
2. Application yarating
3. API credentials oling (APPLICATION_ID, SECRET, STORE_ID)
4. .env ga kiriting
5. Gunicorn restart: `sudo systemctl restart gunicorn`

**Payme:**
1. https://checkout.paycom.uz ga kiring
2. Merchant yarating
3. Webhook URL: `https://yourdomain.uz/api/obuna/payme/`
4. API credentials oling
5. .env ga kiriting

### 2. Telegram Bot sozlash

```bash
# Bot yarating: @BotFather
# Token oling: 1234567890:ABC...
# .env ga qo'shing
nano ~/Husma/.env
# TELEGRAM_BOT_TOKEN=...

# Restart
sudo systemctl restart gunicorn
```

### 3. Monitoring o'rnatish (opsional)

```bash
# Prometheus + Grafana
# Sentry (error tracking)
# Uptime Robot (sayt monitoring)
```

### 4. Backup sozlash

```bash
# Database backup script
nano ~/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/husma/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
PGPASSWORD=kuchli_parol_12345_ABC pg_dump -U husma_user -h localhost husma_db > $BACKUP_DIR/db_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/husma/Husma/media/

# Eski backuplarni o'chirish (7 kundan eski)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x ~/backup.sh

# Cron'ga qo'shish (har kuni 02:00 da)
crontab -e
0 2 * * * /home/husma/backup.sh >> /home/husma/backups/backup.log 2>&1
```

---

## ✅ YAKUNIY TEKSHIRUV RO'YXATI

- [ ] SSH orqali serverga ulandim
- [ ] Server yangilandi
- [ ] PostgreSQL o'rnatildi va database yaratildi
- [ ] Loyiha foydalanuvchi (husma) yaratildi
- [ ] Git clone qilindi
- [ ] Virtual environment yaratildi
- [ ] Requirements o'rnatildi
- [ ] .env fayl to'ldirildi (SECRET_KEY, DATABASE, TELEGRAM_BOT_TOKEN)
- [ ] Django migrate bajarildi
- [ ] Static files yig'ildi
- [ ] Superuser yaratildi
- [ ] Hududlar va tariflar yuklandi
- [ ] Gunicorn sozlandi va ishga tushdi
- [ ] Nginx sozlandi
- [ ] SSL sertifikat olindi
- [ ] Firewall sozlandi
- [ ] Cron job sozlandi
- [ ] Sayt brauzerda ochildi va ishlayapti
- [ ] Admin panel ishlayapti
- [ ] API testlari muvaffaqiyatli
- [ ] Multicard/Payme sozlandi (keyingi bosqich)

---

## 🎉 TABRIKLAYMAN!

Loyihangiz muvaffaqiyatli ishga tushdi!

**Saytingiz:** https://yourdomain.uz  
**Admin:** https://yourdomain.uz/admin/  
**API Docs:** https://yourdomain.uz/

---

**Yaratilgan:** 23-iyun, 2026  
**Versiya:** 1.0  
**Texnik yordam:** Agar muammo bo'lsa, loglarni tekshiring va error xabarlarini o'qing.
