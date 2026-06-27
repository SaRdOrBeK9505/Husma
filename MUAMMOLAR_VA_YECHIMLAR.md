# Muammolar va Yechimlar

## 1. Eski "Kutilmoqda" Obunalarni O'chirish

### Muammo
Bazada 30 daqiqadan ortiq "kutilmoqda" (PENDING) statusdagi obunalar to'planib turibdi. Celery periodic task har 15 daqiqada ishga tushishi kerak, lekin eski obunalar hali ham bazada.

### Sabablari
1. Celery Beat (periodic task scheduler) ishga tushirilmagan
2. Redis/Broker ishlamayapti
3. Celery Worker ishlamayapti

### Yechim 1: Bir Martalik Tozalash (Management Command)

Birinchi navbatda bazadagi eski obunalarni bir martalik tozalash:

```bash
# Avval nechta obuna borligini ko'ring (dry-run):
python manage.py tozalash_obunalar

# Haqiqatda o'chirish:
python manage.py tozalash_obunalar --execute

# Faqat 60 daqiqadan ortiq obunalarni o'chirish:
python manage.py tozalash_obunalar --execute --minutes=60
```

### Yechim 2: Celery va Celery Beat Ishga Tushirish

#### Windows uchun (development):

**Terminal 1 - Redis ishga tushirish:**
```bash
# Redis o'rnatilgan bo'lsa:
redis-server

# Yoki Docker orqali:
docker run -d -p 6379:6379 redis:alpine
```

**Terminal 2 - Celery Worker:**
```bash
# Windows uchun:
celery -A config worker --loglevel=info --pool=solo

# Linux/Mac uchun:
celery -A config worker --loglevel=info
```

**Terminal 3 - Celery Beat (periodic tasks):**
```bash
celery -A config beat --loglevel=info
```

#### Production (Linux) uchun:

**Supervisor yoki systemd bilan avtomatik ishga tushirish:**

`/etc/supervisor/conf.d/husma_celery.conf`:
```ini
[program:husma_celery_worker]
command=/path/to/venv/bin/celery -A config worker --loglevel=info
directory=/path/to/Husma
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:husma_celery_beat]
command=/path/to/venv/bin/celery -A config beat --loglevel=info
directory=/path/to/Husma
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

Keyin:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start husma_celery_worker husma_celery_beat
```

### Yechim 3: Celery Task Qo'lda Ishga Tushirish (Test)

```python
# Django shell
python manage.py shell

>>> from apps.obuna.tasks import bekor_qilish_kutilayotgan_obunalar
>>> result = bekor_qilish_kutilayotgan_obunalar.delay()
>>> result.get()  # Natijani kutish
```

---

## 2. Multicard 404 Xatosi

### Muammo
Frontend `/api/obuna/multicard/callback/` va `/api/obuna/multicard/return/` endpointlarini topololmayapti (404 xatosi).

### Tekshirish

#### 1. Backend URL routing to'g'riligini tekshirish:

```bash
python manage.py show_urls | findstr multicard
```

Kutilgan natija:
```
/api/obuna/multicard/callback/   apps.obuna.multicard.views.MulticardCallbackView
/api/obuna/multicard/return/     apps.obuna.multicard.views.MulticardReturnView
```

#### 2. Backend ishga tushirilganligini tekshirish:

```bash
# Django server ishga tushirish:
python manage.py runserver
```

#### 3. URL mavjudligini curl orqali tekshirish:

```bash
# Windows PowerShell:
curl http://localhost:8000/api/obuna/multicard/return/

# CMD:
curl http://localhost:8000/api/obuna/multicard/return/
```

### Yechim 1: `.env` Faylda Sozlamalarni Tekshirish

`.env` faylida quyidagi sozlamalar to'g'ri bo'lishi kerak:

```env
# Multicard sozlamalari
MULTICARD_APPLICATION_ID=your_app_id
MULTICARD_SECRET=your_secret_key
MULTICARD_STORE_ID=your_store_id
MULTICARD_BASE_URL=https://dev-mesh.multicard.uz
MULTICARD_CALLBACK_URL=https://yourdomain.com/api/obuna/multicard/callback/
MULTICARD_RETURN_URL=https://yourdomain.com/api/obuna/multicard/return/
```

**DIQQAT:** 
- `MULTICARD_CALLBACK_URL` va `MULTICARD_RETURN_URL` sizning backend domeningizni ko'rsatishi kerak
- Development da: `http://localhost:8000/api/obuna/multicard/callback/`
- Production da: `https://yourdomain.com/api/obuna/multicard/callback/`

### Yechim 2: Frontend URLni To'g'rilash

Frontend kod tekshiring - Multicard checkout URL to'g'ri olinayotganini tasdiqlang.

**Frontend (masalan React/Vue):**
```javascript
// Obuna sotib olish
const response = await fetch('/api/obuna/sotib-olish/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    tarif_id: 1,
    provayder: 'multicard'
  })
});

const data = await response.json();

// Backend'dan kelgan checkout_url ga yo'naltirish:
if (data.tolov_url) {
  window.location.href = data.tolov_url;  // Multicard to'lov sahifasiga o'tish
}
```

### Yechim 3: CORS Sozlamalari

`.env` faylida frontend domeni qo'shilganligini tekshiring:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

`config/settings.py` da:
```python
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
```

---

## 3. Multicard Callback Xavfsizligi

### IP Tekshirish

Multicard callback faqat `195.158.26.90` IP manzilidan keladi. Qo'shimcha himoya uchun Nginx/Apache da IP filtrlash:

**Nginx:**
```nginx
location /api/obuna/multicard/callback/ {
    allow 195.158.26.90;
    deny all;
    
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header X-Forwarded-For $remote_addr;
}
```

---

## Qo'shimcha Maslahatlar

### Loglarni Kuzatish

```bash
# Django development server loglari:
python manage.py runserver

# Celery worker loglari:
celery -A config worker --loglevel=info

# Celery beat loglari:
celery -A config beat --loglevel=info

# Production (supervisor loglari):
sudo tail -f /var/log/celery/worker.log
sudo tail -f /var/log/celery/beat.log
```

### Database Query (Obunalarni Tekshirish)

```python
# Django shell
python manage.py shell

>>> from apps.obuna.models import Obuna, Tolov
>>> from django.utils import timezone
>>> from datetime import timedelta

# Kutilayotgan obunalar:
>>> Obuna.objects.filter(holat='kutilmoqda').count()

# 30 daqiqadan ortiq kutilayotgan obunalar:
>>> timeout = timezone.now() - timedelta(minutes=30)
>>> Obuna.objects.filter(holat='kutilmoqda', created_at__lt=timeout).count()

# Bekor qilingan obunalar:
>>> Obuna.objects.filter(holat='bekor').count()
```

### Celery Task Holatini Tekshirish

```bash
# Celery tasklar ro'yxati:
celery -A config inspect registered

# Periodic tasks:
celery -A config inspect scheduled

# Active tasks:
celery -A config inspect active
```

---

## Tezkor Yechim (Quick Fix)

Agar tezda muammoni hal qilish kerak bo'lsa:

```bash
# 1. Eski obunalarni bir martalik tozalash:
python manage.py tozalash_obunalar --execute

# 2. Redis ishga tushirish:
docker run -d -p 6379:6379 redis:alpine

# 3. Celery ishga tushirish (Windows):
# Terminal 1:
celery -A config worker --loglevel=info --pool=solo

# Terminal 2:
celery -A config beat --loglevel=info

# 4. Django server:
python manage.py runserver
```

Production uchun supervisor/systemd bilan avtomatlashtiring.
