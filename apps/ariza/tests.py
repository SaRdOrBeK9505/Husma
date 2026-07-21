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


# ============================================================
# PAGINATSIYA testlari — User va Rieltor ariza ro'yxatlari
# ============================================================
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.tokens import get_tokens_for_user
from apps.makler.models import MaklerProfil
from apps.ariza.models import ArizaMakler


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
)
class ArizaPaginationTestCase(APITestCase):
    """User va Rieltor ariza ro'yxatlarida paginatsiya ishlashini tekshiradi."""

    @classmethod
    def setUpTestData(cls):
        cls.viloyat = Viloyat.objects.create(nomi='Toshkent shahar')
        cls.hudud = Hudud.objects.create(nomi='Chilonzor', viloyat=cls.viloyat)
        cls.mulk_turi = MulkTuri.objects.create(nomi='Kvartira')

        # Oddiy user — 25 ta arizaga ega
        cls.user = CustomUser.objects.create(
            telegram_id=5001, full_name='Ariza User', role=CustomUser.Role.USER
        )
        # Rieltor (faol)
        cls.rieltor_user = CustomUser.objects.create(
            telegram_id=5002, full_name='Ariza Rieltor', role=CustomUser.Role.MAKLER
        )
        cls.rieltor_profil = MaklerProfil.objects.create(
            user=cls.rieltor_user,
            verify_holat=MaklerProfil.VerifyHolat.VERIFIED,
            bepul_muddat_tugash=timezone.now() + timedelta(days=7),
        )

        # 25 ta ariza yaratamiz va har birini rieltorga biriktiramiz
        for i in range(25):
            ariza = Ariza.objects.create(
                user=cls.user, mulk_turi=cls.mulk_turi, hudud=cls.hudud,
                viloyat=cls.viloyat, ariza_turi=Ariza.ArizaTuri.IJARA,
                xonalar_soni=Ariza.XonalarSoni.IKKI,
                narx_min=1000000, narx_max=2000000, holat=Ariza.Holat.YANGI,
            )
            ArizaMakler.objects.create(ariza=ariza, rieltor=cls.rieltor_profil)

    def auth(self, user):
        token = get_tokens_for_user(user)['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_user_arizalar_paginated(self):
        """User o'z arizalari — birinchi sahifada 20 ta (default page_size)."""
        self.auth(self.user)
        resp = self.client.get('/api/arizalar/mening/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['jami_soni'], 25)
        self.assertEqual(len(resp.data['arizalar']), 20)
        self.assertEqual(resp.data['jami_sahifa'], 2)
        self.assertIsNotNone(resp.data['keyingi'])

    def test_user_arizalar_second_page(self):
        """Ikkinchi sahifada qolgan 5 ta ariza."""
        self.auth(self.user)
        resp = self.client.get('/api/arizalar/mening/?page=2')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['arizalar']), 5)
        self.assertIsNone(resp.data['keyingi'])
        self.assertIsNotNone(resp.data['oldingi'])

    def test_user_arizalar_custom_page_size(self):
        """page_size query param ishlaydi."""
        self.auth(self.user)
        resp = self.client.get('/api/arizalar/mening/?page_size=10')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['arizalar']), 10)
        self.assertEqual(resp.data['jami_sahifa'], 3)

    def test_rieltor_arizalar_paginated(self):
        """Rieltor unga biriktirilgan arizalarni sahifalab ko'radi."""
        self.auth(self.rieltor_user)
        resp = self.client.get('/api/rieltor/arizalar/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['jami_soni'], 25)
        self.assertEqual(len(resp.data['arizalar']), 20)
        self.assertEqual(resp.data['jami_sahifa'], 2)

    def test_rieltor_arizalar_no_duplicates_across_pages(self):
        """JOIN tufayli takroriy ariza chiqmasligini tekshiradi (id'lar unikal)."""
        self.auth(self.rieltor_user)
        p1 = self.client.get('/api/rieltor/arizalar/?page=1')
        p2 = self.client.get('/api/rieltor/arizalar/?page=2')
        ids_p1 = {a['id'] for a in p1.data['arizalar']}
        ids_p2 = {a['id'] for a in p2.data['arizalar']}
        self.assertEqual(len(ids_p1 & ids_p2), 0)
        self.assertEqual(len(ids_p1) + len(ids_p2), 25)

    def test_user_holat_filter_with_pagination(self):
        """holat filtri paginatsiya bilan birga ishlaydi."""
        self.auth(self.user)
        resp = self.client.get('/api/arizalar/mening/?holat=yopilgan')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['jami_soni'], 0)
