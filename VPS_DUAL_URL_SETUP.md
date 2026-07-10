# 🚀 VPS da Dual URL Tizimini Sozlash

## 🎯 MAQSAD

Ikkita turli URL ishlatish:
1. **TELEGRAM_MINI_APP_URL** - Telegram xabarlardagi tugmalar uchun
2. **WEB_APP_URL** - Brauzer/web uchun (multicard return va h.k.)

---

## 📋 VPS DA SOZLASH

### 1️⃣ SSH orqali VPS ga kiring

```bash
ssh root@your_vps_ip
```

### 2️⃣ Loyiha direktoriyasiga o'ting

```bash
cd /var/www/Husma
```

### 3️⃣ .env faylini tahrirlang

```bash
nano .env
```

### 4️⃣ Eski FRONTEND_URL qatorlarini o'chirib, yangisini qo'shing:

**ESKI (o'chirish kerak):**
```bash
FRONTEND_URL=https://t.me/husmaestate_bot/husma_estate?startapp=obuna
FRONTEND_URL=https://husma-tes.vercel.app/
```

**YANGI (qo'shish kerak):**
```bash
# Frontend URL'lar (ikkalasi ham kerak!)
# Telegram Mini App - Telegram xabarlardagi tugmalar uchun
TELEGRAM_MINI_APP_URL=https://t.me/husmaestate_bot/husma_estate

# Web App (Vercel/Domain) - Brauzer, multicard return uchun  
WEB_APP_URL=https://husma-tes.vercel.app
```

⚠️ **MUHIM:** 
- Oxiridagi `/` ni OLIB TASHLANG - kod avtomatik qo'shadi
- `?startapp=obuna` kabi query parametrlarni HAM olib tashlang

### 5️⃣ Faylni saqlang

- `nano` da: `Ctrl+X`, keyin `Y`, keyin `Enter`
- `vim` da: `:wq` va `Enter`

### 6️⃣ Servislarni qayta ishga tushiring

```bash
sudo systemctl restart husma husma-celery husma-celerybeat nginx
```

### 7️⃣ Tekshirish

```bash
# Virtual environment ni activate qiling
source .venv/bin/activate

# URL'larni tekshiring
python check_urls.py
```

**Natija shunday ko'rinishi kerak:**

```
✅ HAMMASI TO'G'RI: Ikkala URL ham sozlangan!

🎯 ISHLATILISH:
   • Telegram xabar tugmalari → https://t.me/husmaestate_bot/husma_estate
   • Web redirectlar (multicard) → https://husma-tes.vercel.app
```

---

## 🧪 TEST QILISH

### Test 1: URL'larni tekshirish

```bash
python check_urls.py
```

### Test 2: O'zingizga test xabar yuborish

```bash
python send_test_to_admin.py
```

Telegram'da xabar kelganda:
- ✅ Tugmani bosing
- ✅ Telegram Mini App ochilishini tekshiring
- ✅ `/obuna` sahifasiga olib borishini tekshiring

### Test 3: Multicard to'lovni sinab ko'rish

1. Obuna sotib olishga harakat qiling
2. Multicard to'lov sahifasiga boring
3. To'lovni amalga oshiring
4. To'lovdan keyin web app ga (Vercel) qaytishini tekshiring

---

## 🔧 TROUBLESHOOTING

### Agar URL'lar eski bo'lib qolsa:

```bash
# 1. Celery'ni to'liq to'xtating
sudo systemctl stop husma-celery husma-celerybeat

# 2. Hamma celery processlarni kill qiling
sudo pkill -f celery

# 3. Python bytecode cache'ni tozalang
find /var/www/Husma -type d -name __pycache__ -exec rm -r {} +
find /var/www/Husma -name "*.pyc" -delete

# 4. Qayta ishga tushiring
sudo systemctl start husma husma-celery husma-celerybeat

# 5. Tekshiring
python check_urls.py
```

### Agar celery loglarni ko'rish kerak bo'lsa:

```bash
# Real-time log
sudo journalctl -u husma-celery -f

# Oxirgi 100 qator
sudo journalctl -u husma-celery -n 100
```

---

## 📊 NIMA QILINDI?

### Kod o'zgarishlari:

1. **config/settings.py** - Ikkita yangi URL qo'shildi:
   - `TELEGRAM_MINI_APP_URL` 
   - `WEB_APP_URL`
   - Backward compatibility uchun eski `FRONTEND_URL` ham qoldirildi

2. **apps/obuna/notifications.py** - Telegram xabarlar uchun:
   - `TELEGRAM_MINI_APP_URL` ishlatiladi
   - Tugma URL: `{TELEGRAM_MINI_APP_URL}/obuna`

3. **apps/obuna/multicard/views.py** - Web redirectlar uchun:
   - `WEB_APP_URL` ishlatiladi  
   - Return URL: `{WEB_APP_URL}/obuna/natija?invoice_id=...`

---

## ✅ NATIJA

### AVVAL (muammo):
- Bitta `FRONTEND_URL` ikki maqsad uchun ishlatilgan
- Telegram yoki web - bittasini tanlash kerak edi

### HOZIR (yechim):
- ✅ **Telegram xabarlari** → Telegram Mini App ochadi
- ✅ **Web redirectlar** → Vercel/domain ochadi
- ✅ Har bir maqsad uchun to'g'ri URL

---

## 📝 ESLATMA

Agar kelajakda domain o'zgarsa:

```bash
# VPS da .env ni yangilang:
nano /var/www/Husma/.env

# Kerakli URL'larni yangilang
TELEGRAM_MINI_APP_URL=https://t.me/new_bot/new_app
WEB_APP_URL=https://new-domain.com

# Restart qiling
sudo systemctl restart husma husma-celery husma-celerybeat
```

---

## 🎓 QISQA XULOSA

| URL                      | Ishlatiladi                    | Misol                                   |
|--------------------------|--------------------------------|-----------------------------------------|
| TELEGRAM_MINI_APP_URL    | Telegram xabar tugmalari       | `https://t.me/bot/app/obuna`           |
| WEB_APP_URL              | Multicard return, web linklar  | `https://domain.com/obuna/natija`      |
| FRONTEND_URL (eski)      | Fallback (ixtiyoriy)           | Agar yuqoridagilar bo'sh bo'lsa        |

**Professional yechim:** Har bir vazifa uchun to'g'ri URL! 🚀
