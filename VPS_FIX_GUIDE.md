# 🚀 VPS da Telegram Tugmalarini Tuzatish - Aniq Qo'llanma

## 🎯 MUAMMO
`.env` faylini yangilab, `systemctl restart husma husma-celery husma-celerybeat nginx` qilgansiz, lekin hali ham eski URL bilan xabar ketmoqda.

---

## 📋 ANIQ YECHIM - Qadamma-Qadam

### 1️⃣ VPS ga SSH qiling

```bash
ssh your_user@your_vps_ip
```

### 2️⃣ Loyiha direktoriyasiga o'ting

```bash
cd /path/to/Husma
# Masalan: cd /home/ubuntu/Husma
# Yoki: cd /var/www/Husma
```

### 3️⃣ Virtual environment ni activate qiling

```bash
source .venv/bin/activate
# Yoki agar boshqa nom bo'lsa: source venv/bin/activate
```

### 4️⃣ Debug scriptini ishga tushiring

```bash
python vps_debug.py
```

Bu script:
- ✅ `.env` faylini tekshiradi
- ✅ Django settings ni tekshiradi
- ✅ Ular bir xilligini taqqoslaydi
- ✅ Notification funksiyasi qanday URL yaratayotganini ko'rsatadi
- ✅ Sizga test xabar yuboradi (agar xohlasangiz)

### 5️⃣ Script natijasini o'qing

**Agar "MUAMMO TOPILDI" ko'rsatsa:**

#### A) `.env` va settings turlicha bo'lsa:

```bash
# 1. Celery processlarini to'liq to'xtating
sudo systemctl stop husma-celery husma-celerybeat

# 2. Hamma celery processlar to'xtaganini tekshiring
ps aux | grep celery

# 3. Agar hali ishlab turgan celery bo'lsa, to'xtating:
sudo pkill -f celery

# 4. Qayta ishga tushiring
sudo systemctl start husma-celery husma-celerybeat

# 5. Status tekshiring
sudo systemctl status husma-celery
sudo systemctl status husma-celerybeat
```

#### B) Celery loglarini tekshiring:

```bash
# Celery worker logini ko'rish (real-time)
sudo journalctl -u husma-celery -f

# Oxirgi 50 qatorni ko'rish
sudo journalctl -u husma-celery -n 50
```

**Loglarda nimani qidirish kerak:**
- ✅ `FRONTEND_URL` qiymati to'g'ri ko'rinishimi?
- ❌ ImportError yoki boshqa xatolar bormi?
- ✅ Worker qayta yuklanganligi haqida xabar bormi?

### 6️⃣ Agar hali ham ishlamasa - Serverni reboot qiling

```bash
# Bu 100% yordam beradi, lekin bir necha daqiqa downtime bo'ladi
sudo reboot
```

Reboot dan keyin:

```bash
# SSH ga qayta kiring
ssh your_user@your_vps_ip

# Servislar statusini tekshiring
sudo systemctl status husma
sudo systemctl status husma-celery
sudo systemctl status husma-celerybeat

# Debug scriptni qayta ishga tushiring
cd /path/to/Husma
source .venv/bin/activate
python vps_debug.py
```

---

## 🔍 AGAR HALI HAM ISHLAMASA - Chuqurroq debugging

### Celery konfiguratsiyasini tekshirish

```bash
cd /path/to/Husma
source .venv/bin/activate

# Django shell'ga kiring
python manage.py shell
```

Shell ichida:

```python
from django.conf import settings
print("FRONTEND_URL:", settings.FRONTEND_URL)

from apps.obuna.notifications import _obunalar_tugmasi
tugma = _obunalar_tugmasi()
print("Tugma URL:", tugma['inline_keyboard'][0][0]['url'])

exit()
```

**Natija:**
- Agar to'g'ri URL ko'rsatsa: Muammo Celery worker da
- Agar eski URL ko'rsatsa: Muammo settings.py yoki .env da

### Systemd service fayllarini tekshirish

```bash
# husma-celery service faylini ko'rish
sudo cat /etc/systemd/system/husma-celery.service

# Ichida WorkingDirectory va Environment to'g'rimi?
# Masalan:
#   WorkingDirectory=/path/to/Husma
#   EnvironmentFile=/path/to/Husma/.env
```

Agar service fayl noto'g'ri bo'lsa, tuzating va reload qiling:

```bash
sudo systemctl daemon-reload
sudo systemctl restart husma-celery husma-celerybeat
```

---

## 🎯 ESKI XABARLARNI YANGILASH (Message ID bilan)

Agar yangi xabarlar to'g'ri URL bilan ketyapti bo'lsa, lekin eski xabarlarni ham yangilashni xohlasangiz:

### Usul 1: Har bir foydalanuvchiga yangi xabar yuborish (TAVSIYA ETILADI)

```bash
cd /path/to/Husma
source .venv/bin/activate
python edit_message_buttons.py
# '2' ni tanlang - Barcha rieltorlarga yangi xabar
```

Bu:
- ✅ Har bir foydalanuvchiga yangi tugma bilan xabar yuboradi
- ✅ 100% ishonchli
- ❌ Eski xabarlar o'zgarmaydi (yangi xabar qo'shiladi)

### Usul 2: Eski xabarlarni tahrirlash (agar message_id ma'lum bo'lsa)

Bu faqat oxirgi 48 soat ichida yuborilgan va message_id ma'lum bo'lgan xabarlar uchun ishlaydi.

```bash
python edit_message_buttons.py
# '1' ni tanlang
# Chat ID va Message ID kiriting
```

---

## ✅ TEKSHIRISH

Hammasi to'g'ri ishlayotganini tekshirish uchun:

```bash
cd /path/to/Husma
source .venv/bin/activate

# Sizga test xabar yuborish
python send_test_to_admin.py
```

Telegram'da xabar kelganda tugmani bosing va to'g'ri URL ga olib borishini tekshiring.

---

## 📊 DIAGNOSTIKA NATIJALARI

### ✅ Agar debug script "TO'G'RI" desa:

1. Yangi xabarlar to'g'ri URL bilan yuboriladi
2. Eski xabarlar o'zgarmaydi (Telegram cheklovi)
3. Eski xabarlarni yangilash uchun yuqoridagi "Usul 1" dan foydalaning

### ❌ Agar debug script "XATO" desa:

1. `.env` faylini tekshiring
2. Servislarni to'liq to'xtating va qayta ishga tushiring
3. Agar yordam bermasa, serverni reboot qiling
4. Hali ham ishlamasa, systemd service fayllarini tekshiring

---

## 🆘 YORDAM KERAK BO'LSA

Debug script natijalarini va celery loglarini ko'rsating:

```bash
# Debug natijasi
python vps_debug.py > debug_output.txt

# Celery log
sudo journalctl -u husma-celery -n 100 > celery_log.txt

# Fayllarni download qilib ko'ring
cat debug_output.txt
cat celery_log.txt
```

---

## 🎓 KELAJAK UCHUN

Keyingi safar bunday muammolar bo'lmasligi uchun:

1. **Message ID'larni DB ga saqlang** - Xabar yuborilganda message_id ni saqlash
2. **Environment o'zgaruvchisi monitoring** - settings.FRONTEND_URL ni log qilish
3. **Test xabarlar** - Production ga deploy qilgandan keyin test xabar yuborish

---

## 📌 MUHIM ESLATMA

**Eski xabarlarni tahrirlash Telegram'ning cheklovi:**
- Bot faqat o'zi yuborgan xabarlarni tahrirlashi mumkin
- Message ID kerak
- 48 soatdan eski xabarlar uchun ba'zi cheklovlar bor

**Eng yaxshi yechim:** Yangi xabar yuborish - har doim ishlaydi!
