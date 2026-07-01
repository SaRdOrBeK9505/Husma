"""
Ariza app testlari — kanal notification tizimi.
"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

from apps.users.models import CustomUser
from apps.ariza.models import Ariza
from apps.hudud.models import Hudud, Viloyat, MulkTuri
from apps.ariza.tasks import kanalga_yangi_ariza_xabari_yubor


class ArizaKanalNotificationTestCase(TestCase):
    """Ariza yaratilganda kanalga xabar yuborish testlari"""
    
    def setUp(self):
        """Test uchun kerakli ma'lumotlarni tayyorlash"""
        # Viloyat va hudud yaratish
        self.viloyat = Viloyat.objects.create(nomi="Toshkent")
        self.hudud = Hudud.objects.create(
            nomi="Chilonzor",
            viloyat=self.viloyat
        )
        
        # Mulk turi yaratish
        self.mulk_turi = MulkTuri.objects.create(nomi="Kvartira")
        
        # User yaratish
        self.user = CustomUser.objects.create(
            telegram_id=123456789,
            username="test_user",
            full_name="Test User",
            role=CustomUser.Role.USER,
        )
    
    @patch('core.telegram_utils.telegram_kanalga_yubor')
    def test_yangi_ariza_kanalga_xabar_yuboriladi(self, mock_telegram):
        """Yangi ariza yaratilganda kanalga xabar yuborilishi kerak"""
        mock_telegram.return_value = True
        
        # Ariza yaratish
        ariza = Ariza.objects.create(
            user=self.user,
            mulk_turi=self.mulk_turi,
            hudud=self.hudud,
            viloyat=self.viloyat,
            ariza_turi=Ariza.ArizaTuri.IJARA,
            xonalar_soni=Ariza.XonalarSoni.IKKI,
            narx_min=1000000,
            narx_max=2000000,
            telefon="+998901234567",
            holat=Ariza.Holat.YANGI,
        )
        
        # Task'ni chaqirish
        result = kanalga_yangi_ariza_xabari_yubor(ariza.id)
        
        # Natijalarni tekshirish
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], "Kanalga xabar muvaffaqiyatli yuborildi")
        
        # telegram_kanalga_yubor 1 marta chaqirilganini tekshirish
        self.assertEqual(mock_telegram.call_count, 1)
        
        # channel_type='ariza' bilan chaqirilganini tekshirish
        args, kwargs = mock_telegram.call_args
        self.assertEqual(kwargs.get('channel_type'), 'ariza')
        
        # Xabar matnini tekshirish
        xabar = args[0]
        self.assertIn("Yangi ariza tushdi", xabar)
        self.assertIn("Kvartira", xabar)
        self.assertIn("Chilonzor", xabar)
        self.assertIn("1,000,000 - 2,000,000", xabar)
        self.assertIn("+998901234567", xabar)
    
    @patch('core.telegram_utils.telegram_kanalga_yubor')
    def test_korilmoqda_ariza_xabar_yuborilmaydi(self, mock_telegram):
        """Ko'rilmoqda holatidagi ariza uchun xabar yuborilmasligi kerak"""
        mock_telegram.return_value = True
        
        # Ko'rilmoqda holatidagi ariza yaratish
        ariza = Ariza.objects.create(
            user=self.user,
            mulk_turi=self.mulk_turi,
            hudud=self.hudud,
            viloyat=self.viloyat,
            ariza_turi=Ariza.ArizaTuri.IJARA,
            xonalar_soni=Ariza.XonalarSoni.IKKI,
            narx_min=1000000,
            narx_max=2000000,
            telefon="+998901234567",
            holat=Ariza.Holat.KORILMOQDA,
        )
        
        # Task'ni chaqirish
        result = kanalga_yangi_ariza_xabari_yubor(ariza.id)
        
        # Natijalarni tekshirish
        self.assertFalse(result['success'])
        self.assertIn("holatida", result['message'].lower())
        
        # telegram_kanalga_yubor chaqirilmaganini tekshirish
        self.assertEqual(mock_telegram.call_count, 0)
    
    @patch('core.telegram_utils.telegram_kanalga_yubor')
    def test_telegram_xatosi_qayta_urinish(self, mock_telegram):
        """Telegram xatosi bo'lsa qayta urinish mexanizmi ishlashi kerak"""
        mock_telegram.return_value = False
        
        # Ariza yaratish
        ariza = Ariza.objects.create(
            user=self.user,
            mulk_turi=self.mulk_turi,
            hudud=self.hudud,
            viloyat=self.viloyat,
            ariza_turi=Ariza.ArizaTuri.IJARA,
            xonalar_soni=Ariza.XonalarSoni.IKKI,
            narx_min=1000000,
            narx_max=2000000,
            telefon="+998901234567",
            holat=Ariza.Holat.YANGI,
        )
        
        # Task'ni chaqirish
        result = kanalga_yangi_ariza_xabari_yubor(ariza.id)
        
        # Natijalarni tekshirish
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], "Kanalga xabar yuborilmadi")
        
        # telegram_kanalga_yubor chaqirilganini tekshirish
        self.assertTrue(mock_telegram.called)
    
    @patch('core.telegram_utils.telegram_kanalga_yubor')
    def test_telefonsiz_ariza_xabar_yuboriladi(self, mock_telegram):
        """Telefon ko'rsatilmagan ariza uchun ham xabar yuborilishi kerak"""
        mock_telegram.return_value = True
        
        # Telefonsiz ariza yaratish
        ariza = Ariza.objects.create(
            user=self.user,
            mulk_turi=self.mulk_turi,
            hudud=self.hudud,
            viloyat=self.viloyat,
            ariza_turi=Ariza.ArizaTuri.SOTIB_OLISH,
            xonalar_soni=Ariza.XonalarSoni.UCH,
            narx_min=5000000,
            narx_max=7000000,
            telefon=None,  # Telefon yo'q
            holat=Ariza.Holat.YANGI,
        )
        
        # Task'ni chaqirish
        result = kanalga_yangi_ariza_xabari_yubor(ariza.id)
        
        # Natijalarni tekshirish
        self.assertTrue(result['success'])
        
        # Xabar matnini tekshirish
        args, kwargs = mock_telegram.call_args
        xabar = args[0]
        self.assertIn("Ko'rsatilmagan", xabar)
