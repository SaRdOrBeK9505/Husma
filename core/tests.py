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
        TELEGRAM_NOTIFY_CHANNEL_ID='-1001234567890'
    )
    @patch('core.telegram_utils.requests.post')
    def test_xabar_muvaffaqiyatli_yuboriladi(self, mock_post):
        """Xabar muvaffaqiyatli yuborilganda True qaytarishi kerak"""
        # Mock response yaratish
        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True, 'result': {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Funksiyani chaqirish
        result = telegram_kanalga_yubor("Test xabar")
        
        # Natijalarni tekshirish
        self.assertTrue(result)
        
        # requests.post to'g'ri parametrlar bilan chaqirilganini tekshirish
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        # URL to'g'ri ekanini tekshirish
        self.assertIn('test_bot_token', args[0])
        
        # Payload to'g'ri ekanini tekshirish
        payload = kwargs['json']
        self.assertEqual(payload['chat_id'], '-1001234567890')
        self.assertEqual(payload['text'], 'Test xabar')
        self.assertEqual(payload['parse_mode'], 'Markdown')
    
    @override_settings(TELEGRAM_NOTIFY_CHANNEL_ID='')
    def test_channel_id_bosh_bolsa_false_qaytaradi(self):
        """TELEGRAM_NOTIFY_CHANNEL_ID bo'sh bo'lsa False qaytarishi kerak"""
        result = telegram_kanalga_yubor("Test xabar")
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='',
        TELEGRAM_NOTIFY_CHANNEL_ID='-1001234567890'
    )
    def test_bot_token_bosh_bolsa_false_qaytaradi(self):
        """TELEGRAM_BOT_TOKEN bo'sh bo'lsa False qaytarishi kerak"""
        result = telegram_kanalga_yubor("Test xabar")
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_NOTIFY_CHANNEL_ID='-1001234567890'
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
        result = telegram_kanalga_yubor("Test xabar")
        
        # Natijalarni tekshirish
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_NOTIFY_CHANNEL_ID='-1001234567890'
    )
    @patch('core.telegram_utils.requests.post')
    def test_network_xatosi(self, mock_post):
        """Network xatosi bo'lsa False qaytarishi kerak"""
        # requests.exceptions.RequestException xatosini raise qilish
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        # Funksiyani chaqirish
        result = telegram_kanalga_yubor("Test xabar")
        
        # Natijalarni tekshirish
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_NOTIFY_CHANNEL_ID='-1001234567890'
    )
    @patch('core.telegram_utils.requests.post')
    def test_timeout_xatosi(self, mock_post):
        """Timeout xatosi bo'lsa False qaytarishi kerak"""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        # Funksiyani chaqirish
        result = telegram_kanalga_yubor("Test xabar")
        
        # Natijalarni tekshirish
        self.assertFalse(result)
    
    @override_settings(
        TELEGRAM_BOT_TOKEN='test_bot_token',
        TELEGRAM_NOTIFY_CHANNEL_ID='-1001234567890'
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
        result = telegram_kanalga_yubor(xabar)
        
        # Natijalarni tekshirish
        self.assertTrue(result)
        
        # parse_mode Markdown ekanini tekshirish
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        self.assertEqual(payload['parse_mode'], 'Markdown')
