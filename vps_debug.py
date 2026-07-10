"""
VPS da debug qilish scripti - yangi TELEGRAM_MINI_APP_URL va WEB_APP_URL tekshirish

Bu scriptni VPS da ishga tushiring:
    cd /path/to/Husma
    source .venv/bin/activate
    python vps_debug.py
"""
import os
import sys
import django

# Django sozlamalarini yuklash
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

# Admin telegram ID
ADMIN_TELEGRAM_ID = 7634681769


def check_env_file():
    """".env faylini to'g'ridan-to'g'ri o'qish"""
    print("=" * 80)
    print("📄 1. .ENV FAYLI TEKSHIRUVI")
    print("=" * 80)
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    print(f"📍 .env fayl yo'li: {env_path}")
    print(f"📍 .env fayl mavjudmi? {os.path.exists(env_path)}")
    print()
    
    if not os.path.exists(env_path):
        print("❌ .env fayl topilmadi!")
        return None
    
    env_values = {}
    print("📋 .env faylidan o'qilgan qiymatlar:")
    print("-" * 80)
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if key in ['TELEGRAM_MINI_APP_URL', 'WEB_APP_URL', 'FRONTEND_URL', 'TELEGRAM_BOT_TOKEN', 'DEBUG']:
                    if key == 'TELEGRAM_BOT_TOKEN':
                        print(f"   {key} = {value[:30]}...")
                    else:
                        print(f"   {key} = {value}")
                    env_values[key] = value
    
    print()
    return env_values


def check_django_settings():
    """Django settings.py ga yuklangan qiymatlar"""
    print("=" * 80)
    print("⚙️  2. DJANGO SETTINGS TEKSHIRUVI")
    print("=" * 80)
    
    print("📋 settings.py ga yuklangan qiymatlar:")
    print("-" * 80)
    print(f"   TELEGRAM_MINI_APP_URL = '{settings.TELEGRAM_MINI_APP_URL}'")
    print(f"   WEB_APP_URL = '{settings.WEB_APP_URL}'")
    print(f"   FRONTEND_URL = '{settings.FRONTEND_URL}' (eski, backward compatibility)")
    print(f"   DEBUG = {settings.DEBUG}")
    print(f"   TELEGRAM_BOT_TOKEN = {settings.TELEGRAM_BOT_TOKEN[:30]}..." if settings.TELEGRAM_BOT_TOKEN else "   TELEGRAM_BOT_TOKEN = (bo'sh)")
    print()


def check_notification_function():
    """notifications.py dan qanday URL yaratilayotganini tekshirish"""
    print("=" * 80)
    print("🔍 3. NOTIFICATION FUNKSIYASI (Telegram tugma) TEKSHIRUVI")
    print("=" * 80)
    
    try:
        from apps.obuna.notifications import _obunalar_tugmasi
        
        print("✅ notifications.py modulini import qildik")
        print()
        
        # Tugma yaratish
        tugma = _obunalar_tugmasi()
        tugma_url = tugma['inline_keyboard'][0][0]['url']
        tugma_text = tugma['inline_keyboard'][0][0]['text']
        
        print("📦 _obunalar_tugmasi() funksiyasi qaytargan qiymat:")
        print("-" * 80)
        print(f"   Tugma matni: {tugma_text}")
        print(f"   Tugma URL: {tugma_url}")
        print()
        
        # Kutilgan URL
        expected = f"{settings.TELEGRAM_MINI_APP_URL.rstrip('/')}/obuna" if settings.TELEGRAM_MINI_APP_URL else "(TELEGRAM_MINI_APP_URL bo'sh)"
        
        print(f"🎯 Kutilgan URL: {expected}")
        print(f"📤 Haqiqiy URL:  {tugma_url}")
        print()
        
        if tugma_url == expected:
            print("✅ TO'G'RI: Telegram tugma URL to'g'ri yaratilmoqda!")
        else:
            print("❌ XATO: URL'lar mos kelmayapti!")
        
        return tugma_url
        
    except Exception as e:
        print(f"❌ Xato: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_real_notification():
    """Real obuna xabarini test qilish - ADMIN ga yuboriladi"""
    print()
    print("=" * 80)
    print("🧪 4. REAL TEST XABAR (faqat sizga yuboriladi)")
    print("=" * 80)
    
    print(f"\n📱 Admin Telegram ID: {ADMIN_TELEGRAM_ID}")
    print("Bu xabar faqat sizga yuboriladi, mijozlarga emas!\n")
    
    response = input(f"Sizga test xabar yuborishni xohlaysizmi? (ha/yo'q): ").strip().lower()
    
    if response not in ['ha', 'yes', 'y']:
        print("Test o'tkazib yuborildi.")
        return
    
    try:
        from apps.users.otp_service import telegram_xabar_yuborish
        from apps.obuna.notifications import _obunalar_tugmasi
        
        matn = (
            f"🧪 <b>VPS DEBUG TEST - Yangi URL tizimi</b>\n\n"
            f"Bu xabar VPS dan yuborildi.\n\n"
            f"📊 <b>Settings:</b>\n"
            f"├ TELEGRAM_MINI_APP_URL:\n"
            f"│  <code>{settings.TELEGRAM_MINI_APP_URL}</code>\n"
            f"├ WEB_APP_URL:\n"
            f"│  <code>{settings.WEB_APP_URL}</code>\n"
            f"└ FRONTEND_URL (eski):\n"
            f"   <code>{settings.FRONTEND_URL}</code>\n\n"
            f"🔽 Tugmani bosib, to'g'ri sahifaga olib borishini tekshiring!"
        )
        
        tugma = _obunalar_tugmasi()
        
        print("\n📤 Xabar yuborilmoqda...")
        print(f"   Chat ID: {ADMIN_TELEGRAM_ID}")
        print(f"   Tugma URL: {tugma['inline_keyboard'][0][0]['url']}")
        print()
        
        success = telegram_xabar_yuborish(ADMIN_TELEGRAM_ID, matn, reply_markup=tugma)
        
        if success:
            print("✅ Test xabar muvaffaqiyatli yuborildi!")
            print("\n📱 Telegram'ni tekshiring va tugmani bosib ko'ring!")
        else:
            print("❌ Xabar yuborishda xatolik!")
            
    except Exception as e:
        print(f"❌ Xato: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Asosiy funksiya"""
    print("\n")
    print("🔍 VPS DEBUG SCRIPTI")
    print("Bu script sizga nima uchun eski URL ketayotganini aniqlashda yordam beradi")
    print("\n")
    
    # 1. .env faylini tekshirish
    env_values = check_env_file()
    
    # 2. Django settings tekshirish
    check_django_settings()
    
    # 3. Taqqoslash
    if env_values:
        print("=" * 80)
        print("⚖️  TAQQOSLASH")
        print("=" * 80)
        
        env_telegram = env_values.get('TELEGRAM_MINI_APP_URL', '')
        env_web = env_values.get('WEB_APP_URL', '')
        env_frontend = env_values.get('FRONTEND_URL', '')
        
        print("📋 .env faylida:")
        print(f"   TELEGRAM_MINI_APP_URL = {env_telegram if env_telegram else '(bo\'sh)'}")
        print(f"   WEB_APP_URL = {env_web if env_web else '(bo\'sh)'}")
        print(f"   FRONTEND_URL = {env_frontend if env_frontend else '(bo\'sh)'}")
        print()
        
        print("📋 Django settings da:")
        print(f"   TELEGRAM_MINI_APP_URL = {settings.TELEGRAM_MINI_APP_URL if settings.TELEGRAM_MINI_APP_URL else '(bo\'sh)'}")
        print(f"   WEB_APP_URL = {settings.WEB_APP_URL if settings.WEB_APP_URL else '(bo\'sh)'}")
        print(f"   FRONTEND_URL = {settings.FRONTEND_URL if settings.FRONTEND_URL else '(bo\'sh)'}")
        print()
        
        # Telegram URL check
        if env_telegram and settings.TELEGRAM_MINI_APP_URL:
            if env_telegram == settings.TELEGRAM_MINI_APP_URL:
                print("✅ TELEGRAM_MINI_APP_URL: .env va settings bir xil!")
            else:
                print("❌ TELEGRAM_MINI_APP_URL: Farq bor - server restart kerak!")
        elif not env_telegram:
            print("⚠️  TELEGRAM_MINI_APP_URL .env da yo'q")
        
        # Web URL check
        if env_web and settings.WEB_APP_URL:
            if env_web == settings.WEB_APP_URL:
                print("✅ WEB_APP_URL: .env va settings bir xil!")
            else:
                print("❌ WEB_APP_URL: Farq bor - server restart kerak!")
        elif not env_web:
            print("⚠️  WEB_APP_URL .env da yo'q")
        
        print()
    
    # 4. Notification funksiyasini tekshirish
    notification_url = check_notification_function()
    
    # 5. Real test
    test_real_notification()
    
    # 6. Xulosa
    print()
    print("=" * 80)
    print("📋 XULOSA")
    print("=" * 80)
    
    if settings.TELEGRAM_MINI_APP_URL and settings.WEB_APP_URL:
        print(f"✅ TELEGRAM_MINI_APP_URL: {settings.TELEGRAM_MINI_APP_URL}")
        print(f"✅ WEB_APP_URL: {settings.WEB_APP_URL}")
        print()
        print("🎯 YANGI URL TIZIMI FAOL!")
        print("   - Telegram tugmalari → TELEGRAM_MINI_APP_URL")
        print("   - Multicard return → WEB_APP_URL")
    elif settings.FRONTEND_URL:
        print(f"⚠️  ESKI TIZIM: Faqat FRONTEND_URL ishlatilmoqda")
        print(f"   FRONTEND_URL: {settings.FRONTEND_URL}")
        print()
        print("💡 TAVSIYA: Yangi URL tizimiga o'ting:")
        print("   1. .env ga qo'shing:")
        print("      TELEGRAM_MINI_APP_URL=https://t.me/husmaestate_bot/husma_estate")
        print("      WEB_APP_URL=https://husma-tes.vercel.app")
        print("   2. Restart qiling:")
        print("      sudo systemctl restart husma husma-celery husma-celerybeat")
    else:
        print("❌ HECH QANDAY URL SOZLANMAGAN!")
        print()
        print("🔧 .env ga qo'shing:")
        print("   TELEGRAM_MINI_APP_URL=https://t.me/husmaestate_bot/husma_estate")
        print("   WEB_APP_URL=https://husma-tes.vercel.app")
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
