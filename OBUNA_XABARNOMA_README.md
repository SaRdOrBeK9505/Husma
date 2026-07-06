# Obuna Xabarnoma Tizimi

Bu loyihada obuna tugaganda avtomatik Telegram xabarnoma yuborish tizimi joriy qilindi.

## 📋 Qo'shilgan Funksiyalar

### 1. Telegram Xabarnomalar

#### Yangi xabarnoma turlari:
- **Bepul muddat tugadi** - 7 kunlik bepul sinov muddati tugaganda
- **Obuna tugadi** - To'langan obuna muddati tugaganda
- **Obuna eslatmasi** - Obuna tugashiga 3 kun qolganda eslatma

#### Fayl: `apps/obuna/notifications.py`
```python
def bepul_muddat_tugadi_xabar(rieltor)
def obuna_tugadi_xabar(obuna)
def obuna_tugashi_haqida_xabar(obuna, qolgan_kun)
```

### 2. Celery Davriy Vazifalar (Background Tasks)

#### Fayl: `apps/obuna/tasks.py`

**`obuna_tugash_xabarnomasi()`**
- **Ishga tushish vaqti**: Har kuni 10:00
- **Vazifa**: 
  - Muddati tugagan obunalarni topadi
  - Obuna holatini `TUGAGAN` ga o'zgartiradi
  - Rieltorga Telegram orqali xabar yuboradi
  - Bepul sinov muddati tugagan rieltorlarni topadi va xabar yuboradi

**`obuna_tugashidan_oldin_eslatma(kunlar=3)`**
- **Ishga tushish vaqti**: Har kuni 09:00
- **Vazifa**:
  - 3 kun ichida tugaydigan obunalarni topadi
  - Rieltorga eslatma xabari yuboradi

**`bekor_qilish_kutilayotgan_obunalar()`** (mavjud)
- **Ishga tushish vaqti**: Har 15 daqiqada
- **Vazifa**: 30 daqiqadan ortiq to'lanmagan obunalarni bekor qiladi

#### Fayl: `config/celery.py`
```python
app.conf.beat_schedule = {
    'notify-expired-subscriptions': {
        'task': 'apps.obuna.tasks.obuna_tugash_xabarnomasi',
        'schedule': crontab(hour=10, minute=0),  # Har kuni 10:00
    },
    'remind-expiring-subscriptions': {
        'task': 'apps.obuna.tasks.obuna_tugashidan_oldin_eslatma',
        'schedule': crontab(hour=9, minute=0),  # Har kuni 09:00
        'kwargs': {'kunlar': 3},
    },
}
```

### 3. Telegram Mini App Modal Oyna Tizimi

Rieltorlarning obuna holati to'g'risida real-time ma'lumot berish uchun maxsus API endpoint yaratildi.

#### Yangi Endpoint

**URL**: `GET /api/makler/rieltor/obuna-holati/`

**Authentication**: Bearer Token (Rieltor faqat)

**Response**:
```json
{
  "faol": true,
  "bloklangan": false,
  "bepul_muddat_tugash": "2026-07-13T10:00:00Z",
  "bepul_muddat_qolgan_kunlar": 7,
  "obuna_faol": false,
  "obuna_tugash": null,
  "obuna_qolgan_kunlar": null,
  "obuna_tarif_nomi": null,
  "modal_korinsin": false,
  "modal_xabar": null,
  "modal_turi": "yoq"
}
```

#### Modal Turlari (`modal_turi`)
- `yoq` - Modal ko'rsatilmaydi
- `eslatma` - Sariq rang, informatsiya (3 kun yoki kamroq qolgan)
- `obuna_tugadi` - Qizil rang, kritik (obuna tugagan)
- `bepul_tugadi` - Qizil rang, kritik (bepul muddat tugagan)
- `bloklangan` - Qora rang, xatolik (admin bloklagan)

## 🎨 Frontend Integratsiya (Telegram Mini App)

### Qachon Endpoint Chaqiriladi?

1. **App ochilganda** (onload)
2. **Asosiy ekranga qaytganda** (navigation)
3. **Ariza ko'rishga urinayotganda** (access control)

### React/Vue Misol

```javascript
// API chaqiruv
async function checkSubscriptionStatus() {
  const response = await fetch('/api/makler/rieltor/obuna-holati/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (data.modal_korinsin) {
    showModal({
      type: data.modal_turi,
      message: data.modal_xabar
    });
  }
  
  // Access control
  if (!data.faol) {
    // Arizalarga kirishni bloklash
    disableApplicationAccess();
  }
}

// Modal ko'rsatish
function showModal({ type, message }) {
  const modalColors = {
    'eslatma': 'warning',      // sariq
    'obuna_tugadi': 'danger',   // qizil
    'bepul_tugadi': 'danger',   // qizil
    'bloklangan': 'error'       // qora
  };
  
  // Modal UI ko'rsatish
  openModal({
    title: getModalTitle(type),
    message: message,
    color: modalColors[type],
    action: type !== 'bloklangan' ? 'Obuna sotib olish' : null
  });
}
```

### Telegram WebApp API Integratsiya

```javascript
// Telegram WebApp ready
Telegram.WebApp.ready();

// App ochilganda tekshirish
window.addEventListener('load', () => {
  checkSubscriptionStatus();
});

// Modal'da obuna sotib olish tugmasi bosilsa
function handleSubscribe() {
  Telegram.WebApp.openLink('/tarifs'); // Tariflar sahifasiga o'tish
}

// Modal'ni yopish
function closeModal() {
  // Agar faol emas bo'lsa, orqaga qaytarish
  if (!subscriptionData.faol) {
    Telegram.WebApp.close();
  }
}
```

### Best Practices

1. **Caching**: Statusni 5-10 daqiqaga cache qiling (har safar so'rov yubormaslik uchun)
2. **Loading State**: So'rov yuborilayotganda loading spinner ko'rsating
3. **Error Handling**: Network xatolari uchun fallback UI
4. **UX**: Modal'ni faqat kerakli joylarda ko'rsating (spam qilmang)

## 🚀 Ishga Tushirish

### 1. Celery Worker va Beat Ishga Tushirish

**Windows (CMD)**:
```bash
# Terminal 1: Celery Worker
celery -A config worker -l info --pool=solo

# Terminal 2: Celery Beat (davriy vazifalar)
celery -A config beat -l info
```

**Linux/Mac**:
```bash
# Terminal 1: Worker
celery -A config worker -l info

# Terminal 2: Beat
celery -A config beat -l info
```

### 2. Redis Tekshirish

Celery Redis'dan foydalanadi. Redis ishlab turganini tekshiring:

```bash
# Redis holatini tekshirish (Windows)
redis-cli ping
# Javob: PONG

# Redis'ni ishga tushirish (agar to'xtagan bo'lsa)
redis-server
```

### 3. Telegram Bot Token

`.env` faylingizda bot token borligini tekshiring:
```env
TELEGRAM_BOT_TOKEN=your-bot-token-here
```

## 🧪 Sinash

### 1. Qo'lda Taskni Ishga Tushirish

Django shell orqali:
```python
python manage.py shell

# Obuna tugash xabarnomasi
from apps.obuna.tasks import obuna_tugash_xabarnomasi
result = obuna_tugash_xabarnomasi.delay()
print(result.get())

# Eslatma xabarnomasi
from apps.obuna.tasks import obuna_tugashidan_oldin_eslatma
result = obuna_tugashidan_oldin_eslatma.delay(kunlar=3)
print(result.get())
```

### 2. Test Obuna Yaratish

```python
python manage.py shell

from apps.obuna.models import Obuna, Tarif
from apps.makler.models import MaklerProfil
from django.utils import timezone
from datetime import timedelta

# Test tarif
tarif = Tarif.objects.first()

# Test rieltor
rieltor = MaklerProfil.objects.first()

# Muddati tugagan obuna yaratish
obuna = Obuna.objects.create(
    rieltor=rieltor,
    tarif=tarif,
    holat='faol',
    narx=tarif.narx,
    boshlanish_vaqti=timezone.now() - timedelta(days=30),
    tugash_vaqti=timezone.now() - timedelta(hours=1),  # 1 soat oldin tugagan
)

# Endi task ishga tushiring
from apps.obuna.tasks import obuna_tugash_xabarnomasi
obuna_tugash_xabarnomasi.delay()
```

### 3. Endpoint Sinash

**cURL**:
```bash
curl -X GET "http://localhost:8000/api/makler/rieltor/obuna-holati/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Postman/Insomnia**:
- Method: GET
- URL: `http://localhost:8000/api/makler/rieltor/obuna-holati/`
- Headers: `Authorization: Bearer YOUR_TOKEN_HERE`

## 📊 Monitoring

### Celery Loglarni Ko'rish

Celery worker/beat terminallaridagi loglarni kuzating:

```
[INFO] [Obuna Tugash] Xabar yuborildi: obuna_id=5 rieltor=123456789 tarif=Oylik obuna
[INFO] [Bepul Muddat Tugash] Xabar yuborildi: rieltor_id=3 telegram_id=987654321
[INFO] [Obuna Tugash Task] Umumiy: obuna xabarlari=2, bepul muddat xabarlari=1
```

### Django Admin Orqali Kuzatish

1. Admin panelga kiring: `/admin/`
2. **Periodic tasks** (django-celery-beat) bo'limida vazifalar holatini ko'ring
3. **Obunalar** bo'limida obuna holatlarini tekshiring

## 🔧 Sozlamalar

### Eslatma Kunini O'zgartirish

`config/celery.py` da:
```python
'remind-expiring-subscriptions': {
    'task': 'apps.obuna.tasks.obuna_tugashidan_oldin_eslatma',
    'schedule': crontab(hour=9, minute=0),
    'kwargs': {'kunlar': 5},  # 5 kun oldin eslatma
},
```

### Xabarnoma Vaqtini O'zgartirish

```python
# Har kuni 08:30 da
'schedule': crontab(hour=8, minute=30),

# Har 2 soatda
'schedule': crontab(minute=0, hour='*/2'),

# Haftada bir marta (dushanba 10:00)
'schedule': crontab(hour=10, minute=0, day_of_week=1),
```

## ⚠️ Muhim Eslatmalar

1. **Redis** to'xtasa Celery ishlamaydi
2. **Celery Beat** ishlamasa davriy vazifalar ishga tushmaydi
3. **Telegram Bot Token** noto'g'ri bo'lsa xabarlar yuborilmaydi
4. **Timezone** `Asia/Tashkent` ga sozlangan (Celery Beat uchun)

## 📞 Qo'llab-quvvatlash

Muammolar yuzaga kelsa:

1. Celery loglarini tekshiring
2. Redis ishlayotganini tasdiqlang
3. `.env` fayldagi tokenlarni tekshiring
4. Django loglarini ko'ring (`logs/telegram_auth.log`)

---

**Yaratilgan sana**: 2026-07-06  
**Versiya**: 1.0.0
