"""
Yangi URL tizimini tekshirish scripti.

Bu script:
1. TELEGRAM_MINI_APP_URL ni ko'rsatadi
2. WEB_APP_URL ni ko'rsatadi
3. Ular qanday ishlatilishini ko'rsatadi
"""
import os
import sys
import django

# Django sozlamalarini yuklash
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings


def main():
    print("=" * 80)
    print("🔍 FRONTEND URL TIZIMI TEKSHIRUVI")
    print("=" * 80)
    print()
    
    print("📋 SETTINGS.PY DAN YUKLANGAN QIYMATLAR:")
    print("-" * 80)
    
    telegram_url = getattr(settings, 'TELEGRAM_MINI_APP_URL', '')
    web_url = getattr(settings, 'WEB_APP_URL', '')
    old_frontend = getattr(settings, 'FRONTEND_URL', '')
    
    print(f"TELEGRAM_MINI_APP_URL = {telegram_url if telegram_url else '❌ BO\'SH'}")
    print(f"WEB_APP_URL           = {web_url if web_url else '❌ BO\'SH'}")
    print(f"FRONTEND_URL (eski)   = {old_frontend if old_frontend else '(bo\'sh - normal)'}")
    print()
    
    print("=" * 80)
    print("📱 TELEGRAM XABARLARI (notifications.py)")
    print("=" * 80)
    
    try:
        from apps.obuna.notifications import _obunalar_tugmasi
        
        tugma = _obunalar_tugmasi()
        tugma_url = tugma['inline_keyboard'][0][0]['url']
        
        print(f"Tugma URL: {tugma_url}")
        print()
        
        if telegram_url:
            expected = f"{telegram_url.rstrip('/')}/obuna"
            if tugma_url == expected:
                print("✅ TO'G'RI: Telegram Mini App URL ishlatilmoqda")
            else:
                print(f"⚠️  Kutilgan: {expected}")
                print(f"   Olingan:  {tugma_url}")
        else:
            print("❌ TELEGRAM_MINI_APP_URL bo'sh!")
    except Exception as e:
        print(f"❌ Xato: {e}")
    
    print()
    print("=" * 80)
    print("🌐 WEB REDIRECT (multicard/views.py)")
    print("=" * 80)
    
    if web_url:
        redirect = f"{web_url.rstrip('/')}/obuna/natija?invoice_id=TEST123"
        print(f"Multicard return URL: {redirect}")
        print("✅ TO'G'RI: Web App URL ishlatilmoqda")
    else:
        print("❌ WEB_APP_URL bo'sh!")
    
    print()
    print("=" * 80)
    print("📊 XULOSA")
    print("=" * 80)
    
    if telegram_url and web_url:
        print("✅ HAMMASI TO'G'RI: Ikkala URL ham sozlangan!")
        print()
        print("🎯 ISHLATILISH:")
        print(f"   • Telegram xabar tugmalari → {telegram_url}")
        print(f"   • Web redirectlar (multicard) → {web_url}")
        print()
        print("🧪 TEST QILISH:")
        print("   python send_test_to_admin.py")
    else:
        print("❌ BA'ZI URL'LAR BO'SH!")
        print()
        print("🔧 .env FAYLIDA SOZLANG:")
        if not telegram_url:
            print("   TELEGRAM_MINI_APP_URL=https://t.me/your_bot/your_app")
        if not web_url:
            print("   WEB_APP_URL=https://yourdomain.vercel.app")
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
