"""
Obuna va Payme integratsiyasi uchun avtomatik testlar.

Telegram xabar yuborish mock qilingan — testlar tashqi tarmoqqa chiqmaydi.
"""
import base64
import json
from unittest import mock

from django.test import TestCase, Client, override_settings
from django.utils import timezone
from datetime import timedelta

from apps.users.models import CustomUser
from apps.makler.models import MaklerProfil
from apps.obuna.models import Tarif, Obuna, Tolov, PaymeTransaction


def _rieltor(telegram_id=111, username='r1', bepul_kun=-1):
    """Bepul muddati tugagan (default) rieltor yaratadi."""
    user = CustomUser.objects.create(
        telegram_id=telegram_id, username=username,
        full_name='Test Rieltor', role=CustomUser.Role.MAKLER,
    )
    profil = MaklerProfil.objects.create(
        user=user,
        verify_holat=MaklerProfil.VerifyHolat.VERIFIED,
        bepul_muddat_tugash=timezone.now() + timedelta(days=bepul_kun),
    )
    return profil


# Telegram chaqiruvini barcha testlarda neytrallashtiramiz
@mock.patch('apps.obuna.notifications.telegram_xabar_yuborish', return_value=True)
class FaolPropertyTest(TestCase):

    def test_bepul_muddat_ichida_faol(self, _):
        profil = _rieltor(bepul_kun=5)  # bepul muddat hali bor
        self.assertTrue(profil.faol)
        self.assertFalse(profil.obuna_faol)

    def test_bepul_tugagan_obuna_yoq_faol_emas(self, _):
        profil = _rieltor(bepul_kun=-1)
        self.assertFalse(profil.faol)

    def test_obuna_faollashsa_faol(self, _):
        profil = _rieltor(bepul_kun=-1)
        tarif = Tarif.objects.create(nomi='Oylik', kod='oylik', narx=99000, davomiylik_kun=30)
        obuna = Obuna.objects.create(rieltor=profil, tarif=tarif, narx=tarif.narx)
        obuna.faollashtirish()

        profil.refresh_from_db()
        self.assertTrue(profil.obuna_faol)
        self.assertTrue(profil.faol)
        self.assertIsNotNone(profil.obuna_tugash)

    def test_bloklangan_rieltor_faol_emas(self, _):
        profil = _rieltor(bepul_kun=5)  # bepul muddat bor
        self.assertTrue(profil.faol)
        profil.verify_holat = MaklerProfil.VerifyHolat.REJECTED
        profil.save()
        profil.refresh_from_db()
        self.assertTrue(profil.bloklangan)
        self.assertFalse(profil.faol)  # blok hammadan ustun

    def test_obuna_stacking(self, _):
        """Yangi obuna mavjud obuna tugashidan boshlanadi."""
        profil = _rieltor(bepul_kun=-1)
        tarif = Tarif.objects.create(nomi='Oylik', kod='oylik', narx=99000, davomiylik_kun=30)

        o1 = Obuna.objects.create(rieltor=profil, tarif=tarif, narx=tarif.narx)
        o1.faollashtirish()
        o1.refresh_from_db()

        o2 = Obuna.objects.create(rieltor=profil, tarif=tarif, narx=tarif.narx)
        o2.faollashtirish()
        o2.refresh_from_db()

        # 2-obuna 1-obuna tugashidan boshlanishi kerak
        self.assertEqual(o2.boshlanish_vaqti, o1.tugash_vaqti)


class TolovTest(TestCase):

    @mock.patch('apps.obuna.notifications.telegram_xabar_yuborish', return_value=True)
    def test_tolov_tasdiqlansa_obuna_faollashadi(self, _):
        profil = _rieltor(bepul_kun=-1)
        tarif = Tarif.objects.create(nomi='Oylik', kod='oylik', narx=99000, davomiylik_kun=30)
        obuna = Obuna.objects.create(rieltor=profil, tarif=tarif, narx=tarif.narx)
        tolov = Tolov.objects.create(obuna=obuna, summa=tarif.narx)

        tolov.muvaffaqiyatli_deb_belgilash()
        obuna.refresh_from_db()

        self.assertEqual(tolov.holat, Tolov.Holat.MUVAFFAQIYATLI)
        self.assertEqual(obuna.holat, Obuna.Holat.FAOL)
        self.assertTrue(obuna.faolmi)


@override_settings(PAYME_KEY='test_key', ALLOWED_HOSTS=['testserver'])
@mock.patch('apps.obuna.notifications.telegram_xabar_yuborish', return_value=True)
class PaymeWebhookTest(TestCase):
    URL = '/api/obuna/payme/webhook/'

    def setUp(self):
        self.client = Client()
        self.profil = _rieltor(bepul_kun=-1)
        self.tarif = Tarif.objects.create(nomi='Oylik', kod='oylik', narx=99000, davomiylik_kun=30)
        self.obuna = Obuna.objects.create(rieltor=self.profil, tarif=self.tarif, narx=self.tarif.narx)
        self.amount = self.tarif.narx * 100
        self.auth = 'Basic ' + base64.b64encode(b'Paycom:test_key').decode()

    def _call(self, method, params, auth=None):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        return self.client.post(
            self.URL, data=body, content_type='application/json',
            HTTP_AUTHORIZATION=auth if auth is not None else self.auth,
        ).json()

    def test_auth_xato(self, _):
        bad = 'Basic ' + base64.b64encode(b'Paycom:wrong').decode()
        resp = self._call("CheckPerformTransaction",
                          {"amount": self.amount, "account": {"obuna_id": self.obuna.id}},
                          auth=bad)
        self.assertEqual(resp['error']['code'], -32504)

    def test_check_perform_ok(self, _):
        resp = self._call("CheckPerformTransaction",
                          {"amount": self.amount, "account": {"obuna_id": self.obuna.id}})
        self.assertTrue(resp['result']['allow'])

    def test_notogri_summa(self, _):
        resp = self._call("CheckPerformTransaction",
                          {"amount": 123, "account": {"obuna_id": self.obuna.id}})
        self.assertEqual(resp['error']['code'], -31001)

    def test_account_topilmadi(self, _):
        resp = self._call("CheckPerformTransaction",
                          {"amount": self.amount, "account": {"obuna_id": 999999}})
        self.assertEqual(resp['error']['code'], -31050)

    def test_toliq_oqim_create_perform(self, _):
        # Create
        r1 = self._call("CreateTransaction",
                       {"id": "txn1", "time": 1, "amount": self.amount,
                        "account": {"obuna_id": self.obuna.id}})
        self.assertEqual(r1['result']['state'], 1)

        # Create idempotent — bir xil javob
        r1b = self._call("CreateTransaction",
                        {"id": "txn1", "time": 1, "amount": self.amount,
                         "account": {"obuna_id": self.obuna.id}})
        self.assertEqual(r1b['result']['transaction'], r1['result']['transaction'])

        # Perform
        r2 = self._call("PerformTransaction", {"id": "txn1"})
        self.assertEqual(r2['result']['state'], 2)

        self.obuna.refresh_from_db()
        self.profil.refresh_from_db()
        self.assertEqual(self.obuna.holat, Obuna.Holat.FAOL)
        self.assertTrue(self.profil.faol)

        # Perform idempotent
        r2b = self._call("PerformTransaction", {"id": "txn1"})
        self.assertEqual(r2b['result']['state'], 2)

    def test_cancel_perform_qilingach(self, _):
        self._call("CreateTransaction",
                  {"id": "txn2", "time": 1, "amount": self.amount,
                   "account": {"obuna_id": self.obuna.id}})
        self._call("PerformTransaction", {"id": "txn2"})
        resp = self._call("CancelTransaction", {"id": "txn2", "reason": 5})

        self.assertEqual(resp['result']['state'], -2)
        self.obuna.refresh_from_db()
        self.profil.refresh_from_db()
        self.assertEqual(self.obuna.holat, Obuna.Holat.BEKOR)
        self.assertFalse(self.profil.faol)

    def test_check_transaction(self, _):
        self._call("CreateTransaction",
                  {"id": "txn3", "time": 1, "amount": self.amount,
                   "account": {"obuna_id": self.obuna.id}})
        resp = self._call("CheckTransaction", {"id": "txn3"})
        self.assertEqual(resp['result']['state'], 1)

    def test_method_topilmadi(self, _):
        resp = self._call("NomalumMetod", {})
        self.assertEqual(resp['error']['code'], -32601)
