# Multicard To'lov Oqimi - Frontend Qo'llanma

## To'lov Jarayoni

Multicard bilan to'lov jarayoni quyidagi qadamlardan iborat:

### 1. Obuna Yaratish va Invoice Yaratish

**Frontend → Backend API:**

```
POST /api/obuna/sotib-olish/
Headers: Authorization: Bearer <JWT_TOKEN>
Body: {
  "tarif_id": 1,
  "provayder": "multicard"
}
```

**Backend Javobi:**

```json
{
  "obuna_id": 42,
  "checkout_url": "https://dev-checkout.multicard.uz/checkout/...",
  "invoice_id": "42",
  "uuid": "f6339f31-...",
  "amount": 99000
}
```

### 2. Foydalanuvchini To'lov Sahifasiga Yo'naltirish

Frontend `checkout_url` ga foydalanuvchini yo'naltiradi:

```javascript
// Frontend misoli
window.location.href = response.checkout_url;
```

### 3. To'lov Natijasi (Callback - Server-to-Server)

Multicard to'lov natijasini **backend ga** yuboradi (frontendga emas):

```
POST /api/obuna/multicard/callback/
Headers: X-Signature emas, body ichida "sign" maydoni
Body: {
  "store_id": 6,
  "amount": 20000,
  "invoice_id": "42",
  "billing_id": "20241214242009869794410864028760",
  "payment_time": "2026-06-20 14:36:31",
  "phone": "998901234567",
  "card_pan": "860030******5959",
  "ps": "uzcard",
  "card_token": "6225f3c93f7a880142782fa4",
  "uuid": "e60d8ebc-b9fe-11ef-b159-005056b4367d",
  "receipt_url": "https://dev-checkout.multicard.uz/check/...",
  "sign": "553b4292b0f1d8e0e18e6daeb3af3761"
}
```

**Backend javobi:** Har doim HTTP 200 bilan `{"success": true}` yoki `{"success": false, "message": "..."}`

### 4. Foydalanuvchi Qaytishi (Return URL)

Foydalanuvchi to'lov sahifasidan qaytganda Multicard uni backend ga yo'naltiradi:

```
GET /api/obuna/multicard/return/?invoice_id=42
```

**Backend javobi:** Frontendga redirect qiladi:

```
HTTP 302 Redirect
Location: https://yourdomain.com/obuna/natija?invoice_id=42
```

### 5. Frontend - Natijani Ko'rsatish

Frontend foydalanuvchini natija sahifasiga yo'naltiradi:

```javascript
// Frontend misoli
// URL: /obuna/natija?invoice_id=42

// Obuna holatini tekshirish
GET /api/obuna/mening/
Headers: Authorization: Bearer <JWT_TOKEN>

// Javob:
{
  "id": 42,
  "holat": "faol",  // yoki "kutilmoqda", "bekor"
  "tugash_vaqti": "2026-07-20T14:36:31+05:00",
  "tarif": {
    "nomi": "Oylik obuna",
    "narx": 99000
  }
}
```

## URL Lar Ro'yxati

| URL | Method | Maqsad | Qachon ishlatiladi |
|-----|--------|--------|-------------------|
| `/api/obuna/sotib-olish/` | POST | Obuna yaratish va invoice olish | Frontend to'lovni boshlashda |
| `/api/obuna/multicard/callback/` | POST | To'lov natijasini qabul qilish | Multicard server-to-server (backend) |
| `/api/obuna/multicard/return/` | GET | Foydalanuvchi qaytishi | Foydalanuvchi to'lovdan keyin |
| `/api/obuna/mening/` | GET | Mening obunam holati | Frontend natijani ko'rsatishda |
| `/api/obuna/tarix/` | GET | Obuna tarixi | Frontend tarixni ko'rsatishda |

## Frontend Implementatsiya Misoli

```javascript
// 1. Obuna sotib olish
async function purchaseSubscription(tarifId) {
  const response = await fetch('/api/obuna/sotib-olish/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getJWTToken()}`
    },
    body: JSON.stringify({
      tarif_id: tarifId,
      provayder: 'multicard'
    })
  });

  const data = await response.json();
  
  // Foydalanuvchini Multicard to'lov sahifasiga yo'naltirish
  if (data.checkout_url) {
    window.location.href = data.checkout_url;
  }
}

// 2. Natija sahifasida obuna holatini tekshirish
async function checkSubscriptionStatus() {
  const urlParams = new URLSearchParams(window.location.search);
  const invoiceId = urlParams.get('invoice_id');
  
  const response = await fetch('/api/obuna/mening/', {
    headers: {
      'Authorization': `Bearer ${getJWTToken()}`
    }
  });

  const data = await response.json();
  
  // Holatga qarab UI ko'rsatish
  if (data.holat === 'faol') {
    showSuccessMessage(data);
  } else if (data.holat === 'kutilmoqda') {
    showPendingMessage();
  } else {
    showErrorMessage();
  }
}

// 3. Polling (ixtiyoriy) - agar holat hali "kutilmoqda" bo'lsa
async function pollSubscriptionStatus(maxAttempts = 10) {
  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch('/api/obuna/mening/', {
      headers: {
        'Authorization': `Bearer ${getJWTToken()}`
      }
    });
    
    const data = await response.json();
    
    if (data.holat !== 'kutilmoqda') {
      return data;
    }
    
    // 3 soniya kutish
    await new Promise(resolve => setTimeout(resolve, 3000));
  }
  
  return null; // Timeout
}
```

## Muhim Eslatmalar

1. **Callback URL** faqat backend uchun, frontend bevosita murojaat qilmaydi
2. **Return URL** foydalanuvchini frontendga yo'naltirish uchun
3. **Sign tekshiruvi** MD5 formatida backendda amalga oshiriladi
4. **Idempotentlik** - bir xil UUID bilan qayta kelgan so'rovlar qayta ishlanmaydi
5. **Timeout** - 30 daqiqadan keyin "kutilmoqda" obunalar avtomatik bekor qilinadi

## Xatolarni Qayta Ishlash

```javascript
try {
  const data = await purchaseSubscription(tarifId);
} catch (error) {
  if (error.response?.status === 400) {
    // Noto'g'ri ma'lumot
    showError("Ma'lumotlarni tekshiring");
  } else if (error.response?.status === 401) {
    // Token eskirgan
    redirectToLogin();
  } else {
    // Server xatosi
    showError("Xatolik yuz berdi. Iltimos qayta urinib ko'ring");
  }
}
```

## Test Rejimi

Test rejimida quyidagi URL lar ishlatiladi:
- Multicard Base URL: `https://dev-mesh.multicard.uz`
- Callback URL: `https://yourdomain.com/api/obuna/multicard/callback/`
- Return URL: `https://yourdomain.com/api/obuna/multicard/return/`

Prodga chiqishda `.env` faylda `MULTICARD_TEST_MODE=False` qo'yiladi va `MULTICARD_BASE_URL` o'zgaradi.
