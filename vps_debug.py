"""
VPS da debug qilish scripti - nima uchun eski URL ketayotganini topish

Bu scriptni VPS da ishga tushiring:
    cd /path/to/Husma
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
        print("   Loyiha root direktoriyasida .env yarating")
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
                
                if key in ['FRONTEND_URL', 'TELEGRAM_BOT_TOKEN', 'DEBUG']:
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
    print(f"   FRONTEND_URL = '{settings.FRONTEND_URL}'")
    print(f"   DEBUG = {settings.DEBUG}")
    print(f"   TELEGRAM_BOT_TOKEN = {settings.TELEGRAM_BOT_TOKEN[:30]}..." if settings.TELEGRAM_BOT_TOKEN else "   TELEGRAM_BOT_TOKEN = (bo'sh)")
    print()


def check_notification_function():
    """notifications.py dan qanday URL yaratilayotganini tekshirish"""
    print("=" * 80)
    print("🔍 3. NOTIFICATION FUNKSIYASI TEKSHIRUVI")
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
        expected = f"{settings.FRONTEND_URL.rstrip('/')}/obuna" if settings.FRONTEND_URL else "(FRONTEND_URL bo'sh)"
        
        print(f"🎯 Kutilgan URL: {expected}")
        print(f"📤 Haqiqiy URL:  {tugma_url}")
        print()
        
        if tugma_url == expected:
            print("✅ TO'G'RI: URL mos keladi!")
        else:
            print("❌ XATO: URL'lar mos kelmayapti!")
            print()
            print("🔧 MUAMMO TOPILDI:")
            print("   notifications.py funksiyasi noto'g'ri URL qaytarayapti.")
            print("   Ehtimol settings.FRONTEND_URL eski qiymatda.")
        
        return tugma_url
        
    except Exception as e:
        print(f"❌ Xato: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_real_notification():
    """Real obuna xabarini test qilish"""
    print()
    print("=" * 80)
    print("🧪 4. REAL XABAR TEST (sizga yuboriladi)")
    print("=" * 80)
    
    ADMIN_ID = 7634681769
    
    response = input(f"\nSizga (TG ID: {ADMIN_ID}) test xabar yuborishni xohlaysizmi? (ha/yo'q): ").strip().lower()
    
    if response not in ['ha', 'yes', 'y']:
        print("Test o'tkazib yuborildi.")
        return
    
    try:
        from apps.users.otp_service import telegram_xabar_yuborish
        from apps.obuna.notifications import _obunalar_tugmasi
        
        matn = (
            f"🧪 <b>VPS DEBUG TEST</b>\n\n"
            f"Bu xabar VPS dan yuborildi.\n\n"
            f"📊 Settings:\n"
            f"└ FRONTEND_URL: <code>{settings.FRONTEND_URL}</code>\n\n"
            f"🔽 Tugmani bosib, to'g'ri sahifaga olib borishini tekshiring!"
        )
        
        tugma = _obunalar_tugmasi()
        
        print("\n📤 Xabar yuborilmoqda...")
        print(f"   Chat ID: {ADMIN_ID}")
        print(f"   Tugma URL: {tugma['inline_keyboard'][0][0]['url']}")
        print()
        
        success = telegram_xabar_yuborish(ADMIN_ID, matn, reply_markup=tugma)
        
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
        
        env_frontend = env_values.get('FRONTEND_URL', '')
        settings_frontend = settings.FRONTEND_URL
        
        print(f".env fayli:        {env_frontend if env_frontend else '(bo\'sh)'}")
        print(f"Django settings:   {settings_frontend if settings_frontend else '(bo\'sh)'}")
        print()
        
        if env_frontend and settings_frontend:
            if env_frontend == settings_frontend:
                print("✅ .env va settings bir xil - YAXSHI!")
            else:
                print("❌ MUAMMO TOPILDI: .env va settings turlicha!")
                print("\n🔧 YECHIM:")
                print("   1. Servislarni qayta restart qiling:")
                print("      sudo systemctl restart husma husma-celery husma-celerybeat")
                print("   2. Agar yordam bermasa, serverni to'liq reboot qiling:")
                print("      sudo reboot")
        elif not env_frontend:
            print("❌ MUAMMO: .env faylida FRONTEND_URL yo'q!")
        elif not settings_frontend:
            print("❌ MUAMMO: settings.py ga FRONTEND_URL yuklanmagan!")
        
        print()
    
    # 4. Notification funksiyasini tekshirish
    notification_url = check_notification_function()
    
    # 5. Real test
    test_real_notification()
    
    # 6. Xulosa
    print()
    print("=" * 80)
    print("📋 XULOSA VA TAVSIYALAR")
    print("=" * 80)
    
    if settings.FRONTEND_URL:
        print(f"✅ FRONTEND_URL yuklangan: {settings.FRONTEND_URL}")
        
        if notification_url and notification_url.startswith(settings.FRONTEND_URL):
            print("✅ Notification funksiyasi to'g'ri URL yaratyapti")
            print()
            print("🎯 AGAR HALI HAM ESKI URL KETSA:")
            print("   1. Celery worker loglarini tekshiring:")
            print("      sudo journalctl -u husma-celery -f")
            print("   2. Celery worker o'zini qayta yuklagan bo'lishi kerak")
            print("   3. Agar celery eski kod bilan ishlayotgan bo'lsa:")
            print("      sudo systemctl stop husma-celery husma-celerybeat")
            print("      ps aux | grep celery  # hamma celery processlarini to'xtating")
            print("      sudo systemctl start husma-celery husma-celerybeat")
        else:
            print("❌ Notification funksiyasi noto'g'ri URL yaratyapti")
            print("   Kod qayta yuklanmagan bo'lishi mumkin")
    else:
        print("❌ FRONTEND_URL bo'sh yoki yuklanmagan!")
        print()
        print("🔧 YECHIM:")
        print("   1. .env faylida FRONTEND_URL ni to'ldiring")
        print("   2. Servislarni restart qiling")
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
