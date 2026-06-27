# Celery-based Real-time Telegram Notification Tizimi

## Qilingan o'zgarishlar

### 1. Celery Task yaratildi (`apps/ariza/tasks.py`)
- `yangi_ariza_xabari_yubor` - Rieltorga yangi ariza haqida Telegram xabari yuboradi
- **Idempotent** - bir xil ariza_makler uchun bir necha marta chaqirilsa ham, faqat bitta xabar yuboriladi
- **Retry mechanism** - xato bo'lsa 3 marta qayta urinadi (har biridan keyin 1 daqiqa)
- **Real-time** - Celery orqali background'da ishlaydi (soniyalar)

### 2. Services yangilandi (`apps/ariza/services.py`)
- `_xabar_navbatiga_qosh` funksiyasi Celery task chaqirishga o'zgartirildi
- Navbat tizimi o'rniga to'g'ridan-to'g'ri Celery task ishlatiladi
- `arizani_rieltorlarga_yuborish` funksiyasiga notification qo'shildi

### 3. Model o'chirildi
- `TelegramXabarNavbati` modeli o'chirildi (Celery ishlatilgani uchun kerak emas)
- Management command o'chirildi

### 4. Idempotency va Retry
- Task ichida ArizaMakler holati tekshiriladi
- Xato bo'lsa avtomatik retry qilinadi

## Qilish kerak bo'lgan narsalar

### 1. Migration yaratish va o'tkazish

```bash
python manage.py makemigrations ariza
python manage.py migrate
```

### 2. .env faylga Telegram bot token qo'shish

```env
TELEGRAM_BOT_TOKEN=sizning_bot_tokeningiz
```

### 3. Celery Worker ishga tushirish

Agar Celery allaqachon ishlayotgan bo'lsa, qo'shimcha sozlash kerak emas.
Agar ishlamayotgan bo'lsa:

```bash
celery -A config worker -l info
```

Yoki production uchun (supervisor/systemd):
```bash
celery -A config worker -l info --concurrency=2
```

### 4. Rieltorlarga telegram_id qo'shish

Rieltor profillarida `telegram_id` maydoni bo'lishi kerak. Agar yo'q bo'lsa, quyidagini qo'shing:

```python
# apps/makler/models.py da MaklerProfil modeliga:
telegram_id = models.CharField(max_length=50, blank=True, null=True)
```

Keyin migration yaratish va o'tkazish kerak.

## Qachon notification yuboriladi?

- **Yangi ariza yaratilganda:** ✅ Ha, yuboriladi (real-time, soniyalar)
- **Rieltor profil tahrirlanganda:** ❌ Yo'q, yuborilmaydi (`xabar_yubor=False` default)
- **Yangi rieltor yaratilganda:** ❌ Yo'q, yuborilmaydi (`xabar_yubor=False` default)

## Qanday ishlaydi?

1. Yangi ariza yaratilganda
2. `arizani_rieltorlarga_yuborish` chaqiriladi
3. Har bir rieltor uchun `ArizaMakler` yaratiladi
4. `_xabar_navbatiga_qosh` chaqiriladi
5. Celery task (`yangi_ariza_xabari_yubor.delay()`) background'da ishga tushadi
6. Task ArizaMaklerni topadi, holatni tekshiradi
7. Telegram API orqali xabar yuboradi
8. ArizaMakler holatini "korildi" deb belgilaydi

## Xabar matni namunasi

```
🔔 Yangi ariza kelgan!

🏠 Mulk turi: Kvartira
📍 Hudud: Toshkent shahar, Yunusobod tumani
💰 Narx: 100,000 - 200,000 so'm
📞 Tel: 998901234567
📝 Izoh: 3 xonali, markazda
```

## Afzalliklari

- ✅ **Real-time** - soniyalar ichida xabar yetkazib beriladi
- ✅ **Idempotent** - dublikat xabarlar yo'q
- ✅ **Retry mechanism** - xato bo'lsa avtomatik qayta urinadi
- ✅ **Scalable** - Celery workerlar bilan osongina oshiriladi
- ✅ **Professional** - ishlab chiqarish uchun mos keladi
- ✅ **No cron job needed** - Celery allaqachon ishlayapti

## Monitoring

Celery monitoring uchun Flower ishlatishingiz mumkin:

```bash
pip install flower
celery -A config flower
```

Keyin http://localhost:5555 da monitoring panel bo'ladi.
