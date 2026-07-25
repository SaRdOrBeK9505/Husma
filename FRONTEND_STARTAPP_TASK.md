# Frontend topshirig'i: Telegram `startapp=obuna` bo'yicha obuna sahifasiga o'tish

> Bu faylni to'liq nusxalab, frontend loyihangizdagi AI'ga (Claude) bering.
> Pastdagi "AI UCHUN TOPSHIRIQ" qismi to'g'ridan-to'g'ri prompt sifatida ishlaydi.

---

## Kontekst (nima uchun kerak)

Telegram bot xabarlaridagi **"📦 Obunalar sahifasiga o'tish"** tugmasi Mini App'ni
quyidagi URL bilan ochadi:

```
https://husma-projects.vercel.app?startapp=obuna
```

Bu tugma Mini App'ni to'g'ri (autentifikatsiya bilan) ochadi, LEKIN hozircha
faqat **bosh sahifa** ochilyapti. Bizga kerak: agar `startapp` (ya'ni Telegram
`start_param`) qiymati `obuna` bo'lsa, ilova avtomatik ravishda **obuna sahifasiga**
o'tsin.

Backend allaqachon to'g'ri ishlayapti va tugmani to'g'ri yuboryapti. Qolgan ish
faqat frontendda: `start_param` ni o'qib, tegishli sahifaga yo'naltirish.

---

## AI UCHUN TOPSHIRIQ (shu qismni Claude'ga bering)

Men Telegram Mini App frontendi ustida ishlayapman. Telegram bot ilovani
`?startapp=obuna` parametri bilan ochadi. Menga quyidagini qilib ber:

**Maqsad:** Ilova ishga tushganda Telegram `start_param` qiymatini o'qi. Agar u
`obuna` bo'lsa, foydalanuvchini obuna (subscriptions) sahifasiga yo'naltir.
Agar `start_param` bo'sh yoki boshqa qiymat bo'lsa, hech narsa qilma (odatdagi
bosh sahifa qolsin).

**Qoidalar:**

1. `start_param` ni quyidagi tartibda, birinchi topilganini ol:
   - `window.Telegram.WebApp.initDataUnsafe.start_param`
   - URL query'dagi `tgWebAppStartParam` (`new URLSearchParams(window.location.search)`)
   - URL query'dagi `startapp`
2. Yo'naltirishni ilova ilk marta yuklanganda, autentifikatsiya/init
   tugagandan keyin bir marta bajar (cheksiz redirect bo'lmasin).
3. `window.Telegram.WebApp.ready()` ni chaqir (agar hali chaqirilmagan bo'lsa),
   shundan keyin `start_param` ni o'qi.
4. Obuna sahifasi route'i loyihada qanday bo'lsa (masalan `/obuna`,
   `/subscription`, `/subscriptions`), o'shanga yo'naltir. Route nomini
   loyihadagi mavjud routing'ga qarab aniqla.
5. Loyiha qaysi framework/router ishlatsa (React Router, Next.js router,
   Vue Router, SvelteKit, oddiy JS va h.k.), o'shanga mos usulda yoz.
6. `initDataUnsafe.start_param` faqat Telegram ichida ishlaydi; oddiy
   brauzerda `undefined` bo'lishi normal — kod xatolik bermasin (guard qo'y).

**Universal mantiq (framework tanlashdan qat'i nazar shu ishlashi kerak):**

```js
function getTelegramStartParam() {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg && typeof tg.ready === "function") {
    tg.ready();
  }
  const fromTg = tg && tg.initDataUnsafe && tg.initDataUnsafe.start_param;
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("tgWebAppStartParam") || params.get("startapp");
  return fromTg || fromQuery || null;
}

// Ilova init bo'lgach BIR MARTA chaqir:
const startParam = getTelegramStartParam();
if (startParam === "obuna") {
  // TODO: loyihadagi router bilan obuna sahifasiga o'tkaz
  // Misol (React Router):   navigate("/obuna");
  // Misol (Next.js):        router.push("/obuna");
  // Misol (Vue Router):     router.push("/obuna");
  // Misol (oddiy JS):       window.location.replace("/obuna");
}
```

Iltimos, yuqoridagi mantiqni loyihamning haqiqiy routing tuzilishiga moslab,
to'g'ri joyga (App/entry komponenti yoki root layout init qismiga) qo'shib ber.
Obuna sahifasining aniq route nomini loyihadagi mavjud sahifalardan aniqla.

---

## Test qilish

1. Backend serverni qayta ishga tushiring (`.env` ga `MINI_APP_WEB_URL` qo'shilgan).
2. Telegram'da bot xabaridagi "📦 Obunalar sahifasiga o'tish" tugmasini bosing.
3. Kutilgan natija: ilova to'g'ri (o'z tilingizda, rieltor paneli ma'lumotlari
   bilan) ochiladi VA to'g'ridan-to'g'ri obuna sahifasi ko'rinadi.
4. Bot ichidagi oddiy "Open" tugmasi esa avvalgidek bosh sahifani ochadi
   (chunki unda `startapp` yo'q) — bu to'g'ri xatti-harakat.
