# Birinchi Oy Tarif Sistimi

## Qisqacha Tavsif

Rieltorlar uchun dinamik tarif tizimi - birinchi obuna uchun aktsiya narxi, keyingi oylar uchun oddiy narx.

## Tariflar

### 1. Birinchi Oy (Aktsiya)
- **Kod:** `birinchi_oy`
- **Narx:** 99,000 so'm
- **Davomiylik:** 30 kun
- **Izoh:** Yangi rieltorlar uchun birinchi oy aktsiya narxi

### 2. Oylik (Oddiy)
- **Kod:** `oylik`
- **Narx:** 199,000 so'm
- **Davomiylik:** 30 kun
- **Izoh:** Davomiy oylik obuna narxi

## Qanday Ishlaydi

### 1. Tarif Ro'yxati (TarifListView)

**API:** `GET /api/tariflar/`

**Login qilmagan foydalanuvchi:**
```json
[
  {
    "id": 1,
    "nomi": "Birinchi oy (aktsiya)",
    "kod": "birinchi_oy",
    "narx": 99000,
    "davomiylik_kun": 30,
    "izoh": "Yangi rieltorlar uchun birinchi oy aktsiya narxi",
    "tartib": 1
  },
  {
    "id": 2,
    "nomi": "Oylik obuna",
    "kod": "oylik",
    "narx": 199000,
    "davomiylik_kun": 30,
    "izoh": "Davomiy oylik obuna narxi",
    "tartib": 2
  }
]
```

**Login qilgan rieltor (birinchi obuna):**
```json
[
  {
    "id": 1,
    "nomi": "Birinchi oy (aktsiya)",
    "kod": "birinchi_oy",
    "narx": 99000,
    "davomiylik_kun": 30,
    "izoh": "Yangi rieltorlar uchun birinchi oy aktsiya narxi",
    "tartib": 1,
    "birinchi_oy_bormi": true
  }
]
```

**Login qilgan rieltor (oldin obuna qilgan):**
```json
[
  {
    "id": 2,
    "nomi": "Oylik obuna",
    "kod": "oylik",
    "narx": 199000,
    "davomiylik_kun": 30,
    "izoh": "Davomiy oylik obuna narxi",
    "tartib": 2,
    "birinchi_oy_bormi": false
  }
]
```

### 2. Obuna Sotib Olish (ObunaSotibOlishView)

**API:** `POST /api/obuna/sotib-ol/`

**Variant 1: tarif_id bilan (aniq tarif tanlash)**
```json
{
  "tarif_id": 1,
  "provayder": "payme"
}
```

**Variant 2: tarif_id sizsiz (avtomatik tanlash)**
```json
{
  "provayder": "payme"
}
```

**Javob (birinchi obuna):**
```json
{
  "message": "Obuna yaratildi. To'lovni amalga oshiring.",
  "obuna_id": 123,
  "tolov_id": 456,
  "summa": 99000,
  "provayder": "payme",
  "tolov_url": "https://pay.me/...",
  "birinchi_oy_bormi": true
}
```

**Javob (oldin obuna qilgan):**
```json
{
  "message": "Obuna yaratildi. To'lovni amalga oshiring.",
  "obuna_id": 124,
  "tolov_id": 457,
  "summa": 199000,
  "provayder": "payme",
  "tolov_url": "https://pay.me/...",
  "birinchi_oy_bormi": false
}
```

## Logika

### TarifListView Logikasi

1. Foydalanuvchi login qilganmi?
   - Yo'q → Barcha tariflarni qaytarish
   - Ha → Davom etish

2. Rieltorning oldin obunasi bormi?
   - `Obuna.holat IN [FAOL, TUGAGAN]`
   - Yo'q → `birinchi_oy` tarifini qaytarish
   - Ha → `oylik` tarifini qaytarish

### ObunaSotibOlishView Logikasi

1. `tarif_id` keldimi?
   - Ha → Shu tarifni ishlatish
   - Yo'q → Davom etish

2. Rieltorning oldin obunasi bormi?
   - Yo'q → `birinchi_oy` tarifini tanlash
   - Ha → `oylik` tarifini tanlash

3. Obuna va Tolov yaratish
4. `birinchi_oy_bormi` flag qo'shish (tarif.kod == 'birinchi_oy')

## Migration

**Migration fayli:** `apps/obuna/migrations/0004_add_birinchi_oy_tarif.py`

**Migration o'tkazish:**
```bash
python manage.py migrate obuna
```

**Migration orqali qo'shiladigan tariflar:**
1. Birinchi oy (aktsiya) - 99,000 so'm
2. Oylik obuna - 199,000 so'm

## Frontend Integratsiya

### Tariflarni ko'rsatish

```javascript
// Tariflarni olish
const response = await fetch('/api/tariflar/');
const tariflar = await response.json();

// Agar rieltor bo'lsa, bitta tarif keladi
if (tariflar.length === 1) {
  const tarif = tariflar[0];
  console.log('Narx:', tarif.narx);
  console.log('Birinchi oy:', tarif.birinchi_oy_bormi);
}
```

### Obuna sotib olish

```javascript
// Avtomatik tarif tanlash (tavsiya qilinadi)
const response = await fetch('/api/obuna/sotib-ol/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify({
    provayder: 'payme',
  }),
});

const data = await response.json();
console.log('Summa:', data.summa);
console.log('Birinchi oy:', data.birinchi_oy_bormi);
console.log('To\'lov URL:', data.tolov_url);
```

## Admin Panel

Tariflarni admin panel orqali boshqarish mumkin:
- Tarif narxini o'zgartirish
- Tarifni aktiv/deaktiv qilish
- Yangi tariflar qo'shish

## Xavfsizlik

- `tarif_id` validatsiya qilinadi
- Faqat `is_active=True` bo'lgan tariflar ko'rsatiladi
- Rieltor faqat o'zi uchun mos tarifni ko'radi
- Admin panel to'liq CRUD imkoniyatini beradi

## Monitoring

Loglarda quyidagilarni ko'rish mumkin:
- Obuna yaratilganda
- To'lov muvaffaqiyatli bo'lganda
- Tarif tanlanganda

## Afzalliklari

✅ **Avtomatik** - rieltor uchun mos tarifni avtomatik tanlaydi
✅ **Flexible** - tarif_id bilan aniq tarif ham tanlash mumkin
✅ **Scalable** - yangi tariflar qo'shish oson
✅ **Admin-friendly** - admin panel orqali boshqariladi
✅ **User-friendly** - foydalanuvchi uchun tushunarli

## Kelajak O'zgarishlar

- Choraklik/yillik tariflar qo'shish
- Loyihalik tariflar
- Referal tizimi
- Bonus tizimi
