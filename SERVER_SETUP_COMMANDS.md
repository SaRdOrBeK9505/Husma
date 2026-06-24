# Server Setup — Tezkor Buyruqlar

## 1. Kod Yangilash
```bash
cd /var/www/Husma
git pull origin main
```

## 2. Redis O'rnatish
```bash
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis
redis-cli ping  # PONG chiqishi kerak
```

## 3. Python Kutubxonalar
```bash
source venv/bin/activate  # yoki .venv/bin/activate
pip install -r requirements.txt
```

## 4. .env Yangilash
```bash
nano .env
# Quyidagilarni qo'shing:
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 5. Migratsiya
```bash
python manage.py migrate
```

## 6. Celery Servislar (Systemd)

### Worker Service
```bash
sudo nano /etc/systemd/system/celery-worker.service
```
```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/Husma
Environment="PATH=/var/www/Husma/venv/bin"
ExecStart=/var/www/Husma/venv/bin/celery -A config worker \
    --loglevel=info \
    --pidfile=/var/run/celery/worker.pid \
    --logfile=/var/log/celery/worker.log
Restart=always

[Install]
WantedBy=multi-user.target
```

### Beat Service
```bash
sudo nano /etc/systemd/system/celery-beat.service
```
```ini
[Unit]
Description=Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/Husma
Environment="PATH=/var/www/Husma/venv/bin"
ExecStart=/var/www/Husma/venv/bin/celery -A config beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/var/log/celery/beat.log
Restart=always

[Install]
WantedBy=multi-user.target
```

### Log Kataloglar
```bash
sudo mkdir -p /var/run/celery /var/log/celery
sudo chown www-data:www-data /var/run/celery /var/log/celery
```

### Ishga Tushirish
```bash
sudo systemctl daemon-reload
sudo systemctl start celery-worker
sudo systemctl start celery-beat
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat
```

## 7. Status Tekshirish
```bash
# Servislar
sudo systemctl status redis
sudo systemctl status celery-worker
sudo systemctl status celery-beat

# Loglar
sudo tail -f /var/log/celery/worker.log
sudo tail -f /var/log/celery/beat.log
```

## 8. Gunicorn Restart
```bash
sudo systemctl restart gunicorn
# yoki
sudo systemctl restart husma
```

## 9. Nginx Restart
```bash
sudo systemctl restart nginx
```

---

## Bitta Komanda (Hammasi)
```bash
cd /var/www/Husma && \
git pull origin main && \
source venv/bin/activate && \
pip install -r requirements.txt && \
python manage.py migrate && \
sudo systemctl restart celery-worker celery-beat && \
sudo systemctl restart gunicorn && \
sudo systemctl restart nginx && \
echo "✅ Hammasi tugadi!"
```

---

## Tekshirish
```bash
# 1. Redis
redis-cli ping

# 2. Celery
celery -A config inspect active

# 3. Tasks.py
cat /var/www/Husma/apps/obuna/tasks.py

# 4. .env
grep CELERY /var/www/Husma/.env

# 5. Settings
grep CELERY /var/www/Husma/config/settings.py
```
