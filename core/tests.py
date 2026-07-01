"""
Core utils testlari — Telegram kanalga xabar yuborish.
"""
from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
import requests

from core.telegram_utils import telegram_kanalga_yubor


class TelegramUtilsTestCase(TestCase):
    """Telegram kanalga xabar yuborish funksiyasi testlari"""
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_RIELTOR_CHANNEL_ID='-1001234567890',
    )
    @patch('core.telegram_utils.requests.post')
    def test_xabar_rieltor_kanaliga_yuboriladi(self, mock_post):
        """Rieltor kanaliga xabar muvaffaqiyatli yuborilganda True qaytarishi kerak"""
        # Mock response yaratish
        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True, 'result': {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Funksiyani chaqirish
        result = telegram_kanalga_yubor("Test xabar", channel_type='rieltor')
        
        # Natijalarni tekshirish
        self.assertTrue(result)
        
        # requests.post to'g'ri parametrlar bilan chaqirilganini tekshirish
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        # URL to'g'ri ekanini tekshirish
        self.assertIn('test_bot_token', args[0])
        
        # Payload to'g'ri ekanini tekshirish
        payload = kwargs['json']
        self.assertEqual(payload['chat_id'], '-1001234567890')  # Rieltor channel
        self.assertEqual(payload['text'], 'Test xabar')
        self.assertEqual(payload['parse_mode'], 'Markdown')
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_ARIZA_CHANNEL_ID='-1009876543210',
    )
    @patch('core.telegram_utils.requests.post')
    def test_xabar_ariza_kanaliga_yuboriladi(self, mock_post):
        """Ariza kanaliga xabar muvaffaqiyatli yuborilganda True qaytarishi kerak"""
        # Mock response yaratish
        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True, 'result': {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Funksiyani chaqirish
        result = telegram_kanalga_yubor("Test xabar", channel_type='ariza')
        
        # Natijalarni tekshirish
        self.assertTrue(result)
        
        # Payload to'g'ri ekanini tekshirish
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        self.assertEqual(payload['chat_id'], '-1009876543210')  # Ariza channel
    
    @override_settings(TELEGRAM_RIELTOR_CHANNEL_ID='')
    def test_kanal_id_bosh_bolsa_false_qaytaradi(self):
        """Kanal ID bo'sh bo'lsa False qaytarishi kerak"""
        result = telegram_kanalga_yubor("Test xabar", channel_type='rieltor')
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='',
        TELEGRAM_ARIZA_CHANNEL_ID='-1001234567890'
    )
    def test_bot_token_bosh_bolsa_false_qaytaradi(self):
        """TELEGRAM_BOT_TOKEN bo'sh bo'lsa False qaytarishi kerak"""
        result = telegram_kanalga_yubor("Test xabar", channel_type='ariza')
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_RIELTOR_CHANNEL_ID='-1001234567890'
    )
    @patch('core.telegram_utils.requests.post')
    def test_telegram_api_xatosi(self, mock_post):
        """Telegram API xato qaytarganda False qaytarishi kerak"""
        # Mock response yaratish
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ok': False,
            'error_code': 400,
            'description': 'Bad Request'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Funksiyani chaqirish
        result = telegram_kanalga_yubor("Test xabar", channel_type='rieltor')
        
        # Natijalarni tekshirish
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_ARIZA_CHANNEL_ID='-1001234567890'
    )
    @patch('core.telegram_utils.requests.post')
    def test_network_xatosi(self, mock_post):
        """Network xatosi bo'lsa False qaytarishi kerak"""
        # requests.exceptions.RequestException xatosini raise qilish
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        # Funksiyani chaqirish
        result = telegram_kanalga_yubor("Test xabar", channel_type='ariza')
        
        # Natijalarni tekshirish
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_RIELTOR_CHANNEL_ID='-1001234567890'
    )
    @patch('core.telegram_utils.requests.post')
    def test_timeout_xatosi(self, mock_post):
        """Timeout xatosi bo'lsa False qaytarishi kerak"""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        # Funksiyani chaqirish
        result = telegram_kanalga_yubor("Test xabar", channel_type='rieltor')
        
        # Natijalarni tekshirish
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_ARIZA_CHANNEL_ID='-1001234567890'
    )
    @patch('core.telegram_utils.requests.post')
    def test_markdown_formatlash(self, mock_post):
        """Markdown formatdagi xabar yuborilishi kerak"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True, 'result': {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Markdown formatdagi xabar
        xabar = "🆕 *Yangi ariza*\n\n📍 Hudud: _Chilonzor_"
        result = telegram_kanalga_yubor(xabar, channel_type='ariza')
        
        # Natijalarni tekshirish
        self.assertTrue(result)
        
        # parse_mode Markdown ekanini tekshirish
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        self.assertEqual(payload['parse_mode'], 'Markdown')
