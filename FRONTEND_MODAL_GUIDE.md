# Telegram Mini App - Modal Oyna Strategiyasi

## 🎯 Vazifa

Rieltor obunasi tugaganda yoki tugashiga yaqin bo'lganda Telegram Mini App'da modal oyna ko'rsatish.

## ✅ Tavsiya Qilingan Yechim

**Frontend o'zi modal'ni display qiladi**, backend **faqat status ma'lumotini taqdim etadi**.

### Nima uchun bu yechim yaxshi?

1. ✅ **Offline Support** - Frontend cache'dan ishlashi mumkin
2. ✅ **Telegram UI Guidelines** - Telegram WebApp API bilan to'liq integratsiya
3. ✅ **User Experience** - Tezkor, flicker yo'q
4. ✅ **Flexibility** - Frontend dizaynni osongina o'zgartirishi mumkin
5. ✅ **Performance** - Backend'dan HTML render qilish kerak emas

## 🔗 Backend API

### Endpoint
```
GET /api/makler/rieltor/obuna-holati/
```

### Authentication
```
Authorization: Bearer {telegram_auth_token}
```

### Response Format

```json
{
  "faol": false,
  "bloklangan": false,
  "bepul_muddat_tugash": null,
  "bepul_muddat_qolgan_kunlar": null,
  "obuna_faol": false,
  "obuna_tugash": null,
  "obuna_qolgan_kunlar": null,
  "obuna_tarif_nomi": null,
  "modal_korinsin": true,
  "modal_xabar": "Obunangiz muddati tugadi. Xizmatdan foydalanishni davom ettirish uchun obuna sotib oling.",
  "modal_turi": "obuna_tugadi"
}
```

### Modal Turlari

| Tur | Holat | Rang | Prioritet |
|-----|-------|------|-----------|
| `bloklangan` | Admin bloklagan | 🔴 Qizil | 1 (Eng yuqori) |
| `obuna_tugadi` | Obuna muddati tugagan | 🔴 Qizil | 2 |
| `bepul_tugadi` | Bepul muddat tugagan | 🔴 Qizil | 2 |
| `eslatma` | 3 kun yoki kamroq qolgan | 🟡 Sariq | 3 |
| `yoq` | Hammasi yaxshi | - | - |

## 💻 Frontend Implementatsiya

### 1. React Implementation

```jsx
import { useState, useEffect } from 'react';
import { useTelegram } from './hooks/useTelegram';

// API Service
async function fetchSubscriptionStatus(token) {
  const response = await fetch('/api/makler/rieltor/obuna-holati/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch subscription status');
  }
  
  return response.json();
}

// Modal Component
function SubscriptionModal({ status, onClose, onSubscribe }) {
  if (!status.modal_korinsin) return null;
  
  const modalConfig = {
    'bloklangan': {
      title: '⛔ Profil Bloklangan',
      buttonText: 'Qo\'llab-quvvatlash',
      buttonColor: 'bg-red-600',
      bgColor: 'bg-red-50'
    },
    'obuna_tugadi': {
      title: '🔔 Obuna Tugadi',
      buttonText: 'Obuna Sotib Olish',
      buttonColor: 'bg-blue-600',
      bgColor: 'bg-blue-50'
    },
    'bepul_tugadi': {
      title: '🎁 Bepul Muddat Tugadi',
      buttonText: 'Obuna Sotib Olish',
      buttonColor: 'bg-blue-600',
      bgColor: 'bg-blue-50'
    },
    'eslatma': {
      title: '⏰ Eslatma',
      buttonText: 'Obuna Yangilash',
      buttonColor: 'bg-yellow-600',
      bgColor: 'bg-yellow-50'
    }
  };
  
  const config = modalConfig[status.modal_turi] || {};
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className={`${config.bgColor} rounded-2xl p-6 max-w-sm w-full shadow-xl`}>
        <h2 className="text-xl font-bold mb-3">{config.title}</h2>
        <p className="text-gray-700 mb-6">{status.modal_xabar}</p>
        
        <div className="flex gap-3">
          {status.modal_turi !== 'bloklangan' && (
            <button
              onClick={onClose}
              className="flex-1 py-2 px-4 bg-gray-200 rounded-lg font-medium"
            >
              Keyinroq
            </button>
          )}
          
          <button
            onClick={onSubscribe}
            className={`flex-1 py-2 px-4 ${config.buttonColor} text-white rounded-lg font-medium`}
          >
            {config.buttonText}
          </button>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [subStatus, setSubStatus] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const { webApp, user } = useTelegram();
  
  // Check subscription status on mount
  useEffect(() => {
    checkSubscriptionStatus();
  }, []);
  
  async function checkSubscriptionStatus() {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('auth_token');
      const status = await fetchSubscriptionStatus(token);
      
      setSubStatus(status);
      setShowModal(status.modal_korinsin);
      
      // Cache for 5 minutes
      localStorage.setItem('sub_status', JSON.stringify({
        data: status,
        timestamp: Date.now()
      }));
      
    } catch (error) {
      console.error('Subscription status error:', error);
    } finally {
      setIsLoading(false);
    }
  }
  
  function handleSubscribe() {
    // Navigate to tariffs page
    webApp.openLink('https://yourapp.com/tarifs');
  }
  
  function handleCloseModal() {
    setShowModal(false);
    
    // If not active, close the app
    if (subStatus && !subStatus.faol) {
      webApp.close();
    }
  }
  
  // Access control for applications
  const canViewApplications = subStatus?.faol && !subStatus?.bloklangan;
  
  return (
    <div className="min-h-screen bg-gray-50">
      {isLoading ? (
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {/* Main Content */}
          <main>
            {canViewApplications ? (
              <ApplicationsList />
            ) : (
              <AccessDeniedScreen />
            )}
          </main>
          
          {/* Subscription Modal */}
          <SubscriptionModal
            status={subStatus}
            onClose={handleCloseModal}
            onSubscribe={handleSubscribe}
          />
        </>
      )}
    </div>
  );
}

export default App;
```

### 2. Vue 3 Implementation

```vue
<template>
  <div class="min-h-screen bg-gray-50">
    <div v-if="isLoading" class="flex items-center justify-center h-screen">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
    
    <main v-else>
      <ApplicationsList v-if="canViewApplications" />
      <AccessDeniedScreen v-else />
    </main>
    
    <SubscriptionModal
      v-if="subStatus"
      :status="subStatus"
      :show="showModal"
      @close="handleCloseModal"
      @subscribe="handleSubscribe"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useTelegram } from './composables/useTelegram';

const subStatus = ref(null);
const showModal = ref(false);
const isLoading = ref(true);
const { webApp } = useTelegram();

const canViewApplications = computed(() => {
  return subStatus.value?.faol && !subStatus.value?.bloklangan;
});

async function checkSubscriptionStatus() {
  try {
    isLoading.value = true;
    const token = localStorage.getItem('auth_token');
    
    const response = await fetch('/api/makler/rieltor/obuna-holati/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const status = await response.json();
    subStatus.value = status;
    showModal.value = status.modal_korinsin;
    
    // Cache for 5 minutes
    localStorage.setItem('sub_status', JSON.stringify({
      data: status,
      timestamp: Date.now()
    }));
    
  } catch (error) {
    console.error('Subscription status error:', error);
  } finally {
    isLoading.value = false;
  }
}

function handleSubscribe() {
  webApp.openLink('https://yourapp.com/tarifs');
}

function handleCloseModal() {
  showModal.value = false;
  
  if (subStatus.value && !subStatus.value.faol) {
    webApp.close();
  }
}

onMounted(() => {
  checkSubscriptionStatus();
});
</script>
```

### 3. Vanilla JavaScript Implementation

```javascript
// Telegram WebApp Setup
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// State
let subscriptionStatus = null;

// API Call
async function fetchSubscriptionStatus() {
  const token = localStorage.getItem('auth_token');
  
  try {
    const response = await fetch('/api/makler/rieltor/obuna-holati/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) throw new Error('API request failed');
    
    const data = await response.json();
    subscriptionStatus = data;
    
    // Show modal if needed
    if (data.modal_korinsin) {
      showSubscriptionModal(data);
    }
    
    // Update UI based on status
    updateUIAccessControl(data);
    
  } catch (error) {
    console.error('Error fetching subscription status:', error);
    showErrorMessage('Obuna holatini yuklashda xatolik');
  }
}

// Modal HTML Generator
function createModalHTML(status) {
  const configs = {
    'bloklangan': {
      title: '⛔ Profil Bloklangan',
      buttonText: 'Qo\'llab-quvvatlash',
      buttonClass: 'btn-danger',
      canDismiss: false
    },
    'obuna_tugadi': {
      title: '🔔 Obuna Tugadi',
      buttonText: 'Obuna Sotib Olish',
      buttonClass: 'btn-primary',
      canDismiss: true
    },
    'bepul_tugadi': {
      title: '🎁 Bepul Muddat Tugadi',
      buttonText: 'Obuna Sotib Olish',
      buttonClass: 'btn-primary',
      canDismiss: true
    },
    'eslatma': {
      title: '⏰ Eslatma',
      buttonText: 'Obuna Yangilash',
      buttonClass: 'btn-warning',
      canDismiss: true
    }
  };
  
  const config = configs[status.modal_turi];
  
  return `
    <div class="modal-overlay" id="subscriptionModal">
      <div class="modal-content">
        <h2>${config.title}</h2>
        <p>${status.modal_xabar}</p>
        <div class="modal-actions">
          ${config.canDismiss ? '<button class="btn btn-secondary" onclick="closeModal()">Keyinroq</button>' : ''}
          <button class="btn ${config.buttonClass}" onclick="handleSubscribe()">${config.buttonText}</button>
        </div>
      </div>
    </div>
  `;
}

// Show Modal
function showSubscriptionModal(status) {
  const modalHTML = createModalHTML(status);
  document.body.insertAdjacentHTML('beforeend', modalHTML);
}

// Close Modal
function closeModal() {
  const modal = document.getElementById('subscriptionModal');
  if (modal) {
    modal.remove();
    
    // If not active, close app
    if (subscriptionStatus && !subscriptionStatus.faol) {
      tg.close();
    }
  }
}

// Subscribe Action
function handleSubscribe() {
  tg.openLink('https://yourapp.com/tarifs');
}

// UI Access Control
function updateUIAccessControl(status) {
  const canView = status.faol && !status.bloklangan;
  
  const applicationsSection = document.getElementById('applications');
  const deniedSection = document.getElementById('accessDenied');
  
  if (canView) {
    applicationsSection.style.display = 'block';
    deniedSection.style.display = 'none';
  } else {
    applicationsSection.style.display = 'none';
    deniedSection.style.display = 'block';
  }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  fetchSubscriptionStatus();
});

// Refresh on visibility change (tab switch)
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    fetchSubscriptionStatus();
  }
});
```

## 📱 Telegram WebApp Best Practices

### 1. Main Button (Bottom Button)

```javascript
// Set main button for subscription
if (!subscriptionStatus.faol) {
  tg.MainButton.text = "OBUNA SOTIB OLISH";
  tg.MainButton.color = "#0088cc";
  tg.MainButton.show();
  
  tg.MainButton.onClick(() => {
    tg.openLink('https://yourapp.com/tarifs');
  });
}
```

### 2. Back Button

```javascript
// Show back button
tg.BackButton.show();

tg.BackButton.onClick(() => {
  // Navigate back or close app
  if (!subscriptionStatus.faol) {
    tg.close();
  } else {
    window.history.back();
  }
});
```

### 3. Haptic Feedback

```javascript
// Warning vibration for expired subscription
if (subscriptionStatus.modal_turi === 'obuna_tugadi') {
  tg.HapticFeedback.notificationOccurred('warning');
}

// Success vibration after subscription
tg.HapticFeedback.notificationOccurred('success');
```

### 4. Theme Integration

```javascript
// Use Telegram theme colors
const themeParams = tg.themeParams;

document.documentElement.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
document.documentElement.style.setProperty('--tg-theme-text-color', themeParams.text_color);
document.documentElement.style.setProperty('--tg-theme-button-color', themeParams.button_color);
```

## 🎨 CSS Styling

```css
/* Modal Overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

/* Modal Content */
.modal-content {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Modal Title */
.modal-content h2 {
  font-size: 1.25rem;
  font-weight: bold;
  margin-bottom: 0.75rem;
  color: #1f2937;
}

/* Modal Message */
.modal-content p {
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 1.5rem;
}

/* Modal Actions */
.modal-actions {
  display: flex;
  gap: 0.75rem;
}

.modal-actions button {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

/* Button Variants */
.btn-primary {
  background: #0088cc;
  color: white;
}

.btn-primary:active {
  background: #006ba3;
}

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}
```

## 🔄 Caching Strategy

```javascript
// Cache duration (5 minutes)
const CACHE_DURATION = 5 * 60 * 1000;

async function fetchSubscriptionStatus() {
  // Check cache first
  const cached = localStorage.getItem('sub_status');
  
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    
    // Use cache if not expired
    if (Date.now() - timestamp < CACHE_DURATION) {
      return data;
    }
  }
  
  // Fetch from API
  const response = await fetch('/api/makler/rieltor/obuna-holati/', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const data = await response.json();
  
  // Update cache
  localStorage.setItem('sub_status', JSON.stringify({
    data,
    timestamp: Date.now()
  }));
  
  return data;
}

// Clear cache on subscription update
function clearSubscriptionCache() {
  localStorage.removeItem('sub_status');
}
```

## 🧪 Testing

### 1. Test Different States

Backend'dan turli holatlarni test qiling:

```bash
# Django shell
python manage.py shell

# Test: Obuna tugagan
from apps.makler.models import MaklerProfil
rieltor = MaklerProfil.objects.first()
rieltor.bepul_muddat_tugash = timezone.now() - timedelta(days=1)
rieltor.save()

# Frontend'da /api/makler/rieltor/obuna-holati/ ni chaqiring
```

### 2. Mock Data (Development)

```javascript
// Mock data for development
const MOCK_STATUS = {
  faol: false,
  bloklangan: false,
  modal_korinsin: true,
  modal_xabar: "Test: Obunangiz muddati tugadi",
  modal_turi: "obuna_tugadi"
};

// Use mock in dev mode
const isDev = import.meta.env.DEV;
const status = isDev ? MOCK_STATUS : await fetchSubscriptionStatus();
```

## 📞 Support

Savollar bo'lsa:
- Backend API: `OBUNA_XABARNOMA_README.md`
- Telegram Bot: `.env` faylni tekshiring
- Frontend: Browser console loglarini ko'ring

---

**Yaratilgan**: 2026-07-06  
**Muallif**: Kiro AI Assistant
