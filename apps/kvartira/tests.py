"""
Kvartira API endpoint'lari uchun to'liq test to'plami.

Fokus:
  1. PERMISSION (ruxsat) testlari  — eng muhim qism
  2. Rasm upload testlari
  3. Ma'lumot validatsiyasi

Ishga tushirish (sqlite bilan tez test):
    set DB_ENGINE=sqlite && python manage.py test apps.kvartira -v 2

Rasm testlari DigitalOcean'ga yuklamasligi uchun STORAGES in-memory'ga
override qilingan.
"""
from io import BytesIO

from django.test import override_settings
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from PIL import Image

from apps.users.models import CustomUser
from apps.users.tokens import get_tokens_for_user
from apps.makler.models import MaklerProfil
from apps.hudud.models import Viloyat, Hudud, MulkTuri
from apps.kvartira.models import Kvartira, KvartiraRasm


# --- Rasm testlari lokal xotirada ishlashi uchun storage override ---
TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

# Celery tasklari testda sinxron ishlashi uchun (Redis'ga ulanmasin).
# MaklerProfil yaratilganda signal Celery task chaqiradi — eager rejimda
# u to'g'ridan-to'g'ri ishlaydi va Telegram xatosi try/except bilan yutiladi.
CELERY_EAGER = dict(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=False)


def make_image(name='test.jpg', size_kb=None, fmt='JPEG', content_type='image/jpeg'):
    """Test uchun haqiqiy (kichik) rasm fayl yaratadi."""
    buf = BytesIO()
    Image.new('RGB', (20, 20), 'blue').save(buf, format=fmt)
    data = buf.getvalue()
    if size_kb:
        # Fayl hajmini sun'iy ravishda oshirish (katta fayl testi uchun)
        data = data + (b'\x00' * (size_kb * 1024))
    return SimpleUploadedFile(name, data, content_type=content_type)


def make_fake_pdf(name='hujjat.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4 fake pdf content', content_type='application/pdf')


@override_settings(STORAGES=TEST_STORAGES, **CELERY_EAGER)
class KvartiraBaseTestCase(APITestCase):
    """Umumiy setup: userlar, rieltorlar, hudud/viloyat/mulk turi."""

    @classmethod
    def setUpTestData(cls):
        cls.viloyat = Viloyat.objects.create(nomi='Toshkent shahar')
        cls.hudud = Hudud.objects.create(nomi='Chilonzor', viloyat=cls.viloyat)
        cls.mulk_turi = MulkTuri.objects.create(kod='kvartira', nomi='Kvartira')

        # Oddiy foydalanuvchi (rieltor emas)
        cls.oddiy_user = CustomUser.objects.create_user(
            telegram_id=1001, full_name='Oddiy User', role=CustomUser.Role.USER
        )

        # Rieltor A (faol, bepul muddat ichida)
        cls.rieltor_a = CustomUser.objects.create_user(
            telegram_id=2001, full_name='Rieltor A', role=CustomUser.Role.MAKLER
        )
        cls.profil_a = MaklerProfil.objects.create(
            user=cls.rieltor_a,
            verify_holat=MaklerProfil.VerifyHolat.VERIFIED,
            bepul_muddat_tugash=timezone.now() + timedelta(days=7),
        )

        # Rieltor B (faol) — cross-owner testlari uchun
        cls.rieltor_b = CustomUser.objects.create_user(
            telegram_id=2002, full_name='Rieltor B', role=CustomUser.Role.MAKLER
        )
        cls.profil_b = MaklerProfil.objects.create(
            user=cls.rieltor_b,
            verify_holat=MaklerProfil.VerifyHolat.VERIFIED,
            bepul_muddat_tugash=timezone.now() + timedelta(days=7),
        )

        # Bloklangan rieltor (admin rejected qilgan)
        cls.rieltor_blok = CustomUser.objects.create_user(
            telegram_id=2003, full_name='Bloklangan Rieltor', role=CustomUser.Role.MAKLER
        )
        cls.profil_blok = MaklerProfil.objects.create(
            user=cls.rieltor_blok,
            verify_holat=MaklerProfil.VerifyHolat.REJECTED,
            bepul_muddat_tugash=timezone.now() + timedelta(days=7),
        )

        # Obunasi tugagan rieltor (bepul muddat o'tgan, obuna yo'q)
        cls.rieltor_tugagan = CustomUser.objects.create_user(
            telegram_id=2004, full_name='Muddati Tugagan Rieltor', role=CustomUser.Role.MAKLER
        )
        cls.profil_tugagan = MaklerProfil.objects.create(
            user=cls.rieltor_tugagan,
            verify_holat=MaklerProfil.VerifyHolat.VERIFIED,
            bepul_muddat_tugash=timezone.now() - timedelta(days=1),
        )

    def auth(self, user):
        """Berilgan user JWT tokeni bilan clientni autentifikatsiya qiladi."""
        token = get_tokens_for_user(user)['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def logout(self):
        self.client.credentials()

    def valid_payload(self, **overrides):
        data = {
            'hudud': self.hudud.id,
            'viloyat': self.viloyat.id,
            'mulk_turi': self.mulk_turi.id,
            'sarlavha': 'Chilonzorda 2 xonali kvartira',
            'ariza_turi': Kvartira.ArizaTuri.IJARA,
            'narx': 3000000,
            'valyuta': Kvartira.Valyuta.UZS,
            'xonalar_soni': '2',
        }
        data.update(overrides)
        return data

    def create_kvartira(self, owner, **overrides):
        defaults = dict(
            qoshgan=owner, hudud=self.hudud, viloyat=self.viloyat,
            mulk_turi=self.mulk_turi, sarlavha='Test kvartira',
            ariza_turi=Kvartira.ArizaTuri.SOTISH, narx=100000000,
            valyuta=Kvartira.Valyuta.UZS, xonalar_soni='3',
            holat=Kvartira.Holat.ACTIVE, is_verified=True,
        )
        defaults.update(overrides)
        return Kvartira.objects.create(**defaults)


# ============================================================
# 1. PERMISSION — KVARTIRA YARATISH (POST)
# ============================================================
class KvartiraCreatePermissionTests(KvartiraBaseTestCase):
    url = '/api/rieltor/kvartiralar/'

    def test_unauthenticated_create_401(self):
        """Login qilinmagan holda kvartira qo'shish → 401."""
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_create_403(self):
        """Oddiy foydalanuvchi kvartira qo'sha olmaydi → 403."""
        self.auth(self.oddiy_user)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_rieltor_create_201(self):
        """Faol rieltor kvartira qo'shadi → 201 va DB'ga saqlanadi."""
        self.auth(self.rieltor_a)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Kvartira.objects.filter(qoshgan=self.rieltor_a, sarlavha='Chilonzorda 2 xonali kvartira').exists()
        )

    def test_blocked_rieltor_create(self):
        """Bloklangan (rejected) rieltor kvartira qo'sha olmasligi kerak."""
        self.auth(self.rieltor_blok)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        # Kutilgan: 403. Haqiqiy holatni test aniqlaydi.
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN,
            msg=f"Bloklangan rieltor kvartira qo'sha oldi! status={resp.status_code}"
        )

    def test_expired_rieltor_create(self):
        """Bepul muddati tugagan, obunasiz rieltor kvartira qo'sha olmasligi kerak."""
        self.auth(self.rieltor_tugagan)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN,
            msg=f"Muddati tugagan rieltor kvartira qo'sha oldi! status={resp.status_code}"
        )


# ============================================================
# 2. PERMISSION — CROSS-OWNER TAHRIRLASH / O'CHIRISH
# ============================================================
class KvartiraOwnershipTests(KvartiraBaseTestCase):

    def setUp(self):
        self.kv_a = self.create_kvartira(self.rieltor_a, sarlavha='A kvartirasi')

    def detail_url(self, pk):
        return f'/api/rieltor/kvartiralar/{pk}/'

    def test_owner_can_update(self):
        """Rieltor o'z kvartirasini tahrirlaydi → 200."""
        self.auth(self.rieltor_a)
        resp = self.client.patch(self.detail_url(self.kv_a.pk), {'narx': 5000000}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.kv_a.refresh_from_db()
        self.assertEqual(self.kv_a.narx, 5000000)

    def test_owner_can_delete(self):
        """Rieltor o'z kvartirasini o'chiradi → 204."""
        self.auth(self.rieltor_a)
        resp = self.client.delete(self.detail_url(self.kv_a.pk))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Kvartira.objects.filter(pk=self.kv_a.pk).exists())

    def test_other_rieltor_cannot_update(self):
        """Boshqa rieltor birovning kvartirasini tahrirlay olmaydi → 404/403."""
        self.auth(self.rieltor_b)
        resp = self.client.patch(self.detail_url(self.kv_a.pk), {'narx': 999}, format='json')
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.kv_a.refresh_from_db()
        self.assertNotEqual(self.kv_a.narx, 999)

    def test_other_rieltor_cannot_delete(self):
        """Boshqa rieltor birovning kvartirasini o'chira olmaydi → 404/403."""
        self.auth(self.rieltor_b)
        resp = self.client.delete(self.detail_url(self.kv_a.pk))
        self.assertIn(resp.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))
        self.assertTrue(Kvartira.objects.filter(pk=self.kv_a.pk).exists())

    def test_regular_user_cannot_access_detail(self):
        """Oddiy user rieltor detail endpointiga kira olmaydi → 403."""
        self.auth(self.oddiy_user)
        resp = self.client.patch(self.detail_url(self.kv_a.pk), {'narx': 1}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_change_other_rieltor(self):
        """Boshqa rieltor birovning kvartira statusini o'zgartira olmaydi → 404."""
        self.auth(self.rieltor_b)
        resp = self.client.patch(
            f'/api/rieltor/kvartiralar/{self.kv_a.pk}/status/',
            {'holat': Kvartira.Holat.ARCHIVED}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================
# 3. PUBLIC endpointlar
# ============================================================
class KvartiraPublicTests(KvartiraBaseTestCase):

    def test_public_list_no_auth(self):
        """Public ro'yxat login talab qilmaydi → 200, faqat verified+active ko'rinadi."""
        self.create_kvartira(self.rieltor_a, is_verified=True, holat=Kvartira.Holat.ACTIVE)
        self.create_kvartira(self.rieltor_a, is_verified=False)  # ko'rinmasligi kerak
        resp = self.client.get('/api/kvartiralar/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_public_detail_unverified_404(self):
        """Tasdiqlanmagan kvartira public detailda ko'rinmaydi → 404."""
        kv = self.create_kvartira(self.rieltor_a, is_verified=False)
        resp = self.client.get(f'/api/kvartiralar/{kv.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_jami_qavat_exact(self):
        """Qavatlik (jami_qavat) aniq qiymat bo'yicha filtrlanadi."""
        self.create_kvartira(self.rieltor_a, jami_qavat=9, sarlavha='9 qavatli')
        self.create_kvartira(self.rieltor_a, jami_qavat=16, sarlavha='16 qavatli')
        resp = self.client.get('/api/kvartiralar/?jami_qavat=9')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['jami_qavat'], 9)

    def test_filter_jami_qavat_range(self):
        """Qavatlik diapazon bo'yicha filtrlanadi (jami_qavat_max)."""
        self.create_kvartira(self.rieltor_a, jami_qavat=5)
        self.create_kvartira(self.rieltor_a, jami_qavat=9)
        self.create_kvartira(self.rieltor_a, jami_qavat=16)
        resp = self.client.get('/api/kvartiralar/?jami_qavat_max=9')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 2)

    def test_filter_narx_range(self):
        """Narx diapazoni bo'yicha filtrlanadi."""
        self.create_kvartira(self.rieltor_a, narx=100000000)
        self.create_kvartira(self.rieltor_a, narx=300000000)
        self.create_kvartira(self.rieltor_a, narx=500000000)
        resp = self.client.get('/api/kvartiralar/?narx_min=200000000&narx_max=400000000')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_filter_mulk_turi_and_xonalar(self):
        """Turlar (mulk_turi) va Xonalar (xonalar_soni) filtri ishlaydi."""
        self.create_kvartira(self.rieltor_a, xonalar_soni='2')
        self.create_kvartira(self.rieltor_a, xonalar_soni='3')
        resp = self.client.get(f'/api/kvartiralar/?mulk_turi={self.mulk_turi.id}&xonalar_soni=2')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['xonalar_soni'], '2')


# ============================================================
# 4. RASM UPLOAD testlari
# ============================================================
class KvartiraRasmTests(KvartiraBaseTestCase):

    def setUp(self):
        self.kv_a = self.create_kvartira(self.rieltor_a)
        self.rasm_url = f'/api/rieltor/kvartiralar/{self.kv_a.pk}/rasmlar/'

    def test_create_with_1_to_8_images(self):
        """Yaratishda 8 tagacha rasm → 201."""
        self.auth(self.rieltor_a)
        payload = self.valid_payload()
        payload['rasmlar'] = [make_image(f'r{i}.jpg') for i in range(8)]
        resp = self.client.post('/api/rieltor/kvartiralar/', payload, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertEqual(kv.rasmlar.count(), 8)

    def test_create_with_9_images_rejected(self):
        """9 ta rasm → xatolik ('8 ta' xabari bilan)."""
        self.auth(self.rieltor_a)
        payload = self.valid_payload()
        payload['rasmlar'] = [make_image(f'r{i}.jpg') for i in range(9)]
        resp = self.client.post('/api/rieltor/kvartiralar/', payload, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('8', str(resp.data))

    def test_add_images_over_limit(self):
        """Mavjud rasmlar + yangi > 8 → xatolik."""
        self.auth(self.rieltor_a)
        for i in range(6):
            KvartiraRasm.objects.create(kvartira=self.kv_a, rasm=make_image(f'e{i}.jpg'))
        resp = self.client.post(
            self.rasm_url,
            {'rasmlar': [make_image(f'n{i}.jpg') for i in range(3)]},
            format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('8', str(resp.data))

    def test_add_up_to_8_ok(self):
        """Mavjud 5 + yangi 3 = 8 → 201."""
        self.auth(self.rieltor_a)
        for i in range(5):
            KvartiraRasm.objects.create(kvartira=self.kv_a, rasm=make_image(f'e{i}.jpg'))
        resp = self.client.post(
            self.rasm_url,
            {'rasmlar': [make_image(f'n{i}.jpg') for i in range(3)]},
            format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.kv_a.rasmlar.count(), 8)

    def test_pdf_rejected(self):
        """PDF fayl rasm sifatida rad etiladi → 400."""
        self.auth(self.rieltor_a)
        resp = self.client.post(
            self.rasm_url, {'rasmlar': [make_fake_pdf()]}, format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_large_file_no_size_limit(self):
        """20MB+ fayl uchun hajm cheklovi bor-yo'qligini tekshiradi.

        Storage'ga bormasdan, serializer validatsiya darajasida tekshiramiz
        (Windows'da InMemoryStorage katta faylni tozalashda muammo beradi).
        Agar validatsiya o'tsa — app darajasida fayl hajmi limiti YO'Q (finding).
        """
        from apps.kvartira.serializers import KvartiraRasmYuklashSerializer
        big = make_image('big.jpg', size_kb=20 * 1024)  # ~20MB
        serializer = KvartiraRasmYuklashSerializer(data={'rasmlar': [big]})
        valid = serializer.is_valid()
        self.assertFalse(
            valid,
            msg="20MB fayl validatsiyadan o'tdi! Fayl hajmi limiti yo'q — "
                "har qanday hajmdagi rasm qabul qilinadi (xavfsizlik/resurs muammosi)."
        )

    def test_uploaded_url_points_to_cdn(self):
        """Haqiqiy S3 (DigitalOcean) storage yuklangan rasm uchun CDN domenli
        URL berishi kerak: https://husma-media.fra1.cdn.digitaloceanspaces.com/...

        InMemoryStorage override'dan chetlab o'tib, sozlangan haqiqiy S3
        storage backendni to'g'ridan-to'g'ri tekshiramiz (fayl yuklamasdan).
        """
        from django.core.files.storage import storages as dj_storages
        # override_settings(STORAGES=...) faol bo'lgani uchun to'g'ridan-to'g'ri
        # sozlangan S3 backendni yaratamiz (AWS_LOCATION='media' avtomatik qo'shiladi).
        from storages.backends.s3boto3 import S3Boto3Storage
        storage = S3Boto3Storage()
        url = storage.url('kvartiralar/2026/07/test.jpg')
        self.assertIn(
            'husma-media.fra1.cdn.digitaloceanspaces.com', url,
            msg=f"Storage URL kutilgan CDN domeniga ishora qilmayapti: {url}"
        )

    def test_add_image_to_other_rieltor_kvartira(self):
        """Boshqa rieltorning kvartirasiga rasm qo'shish → 404."""
        self.auth(self.rieltor_b)
        resp = self.client.post(
            self.rasm_url, {'rasmlar': [make_image('x.jpg')]}, format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_image_other_rieltor(self):
        """Boshqa rieltorning rasmini o'chirish → 404."""
        rasm = KvartiraRasm.objects.create(kvartira=self.kv_a, rasm=make_image('d.jpg'))
        self.auth(self.rieltor_b)
        resp = self.client.delete(f'{self.rasm_url}{rasm.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_delete_image(self):
        """Rieltor o'z rasmini o'chiradi → 204."""
        rasm = KvartiraRasm.objects.create(kvartira=self.kv_a, rasm=make_image('d.jpg'))
        self.auth(self.rieltor_a)
        resp = self.client.delete(f'{self.rasm_url}{rasm.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_add_image_unauthenticated(self):
        """Login qilinmagan holda rasm qo'shish → 401."""
        resp = self.client.post(
            self.rasm_url, {'rasmlar': [make_image('x.jpg')]}, format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================
# 5. MA'LUMOT VALIDATSIYASI
# ============================================================
class KvartiraValidationTests(KvartiraBaseTestCase):
    url = '/api/rieltor/kvartiralar/'

    def test_missing_required_fields(self):
        """Majburiy maydonlar bo'sh → 400 (narx, sarlavha, ariza_turi, xonalar_soni)."""
        self.auth(self.rieltor_a)
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ('sarlavha', 'ariza_turi', 'narx', 'xonalar_soni'):
            self.assertIn(field, resp.data, msg=f"'{field}' majburiy bo'lishi kerak edi")

    def test_invalid_price_type(self):
        """Narxga matn kiritilsa → 400."""
        self.auth(self.rieltor_a)
        resp = self.client.post(self.url, self.valid_payload(narx='juda-qimmat'), format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('narx', resp.data)

    def test_invalid_choice(self):
        """Noto'g'ri xonalar_soni choice → 400."""
        self.auth(self.rieltor_a)
        resp = self.client.post(self.url, self.valid_payload(xonalar_soni='99'), format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('xonalar_soni', resp.data)

    def test_valid_full_payload(self):
        """Barcha maydonlar to'g'ri → 201."""
        self.auth(self.rieltor_a)
        payload = self.valid_payload(
            tavsif='Yaxshi kvartira', hammom_soni=1, maydon_m2=65.5,
            qavat=3, jami_qavat=9, remont_holati=Kvartira.RemontHolati.YEVRO,
            mebel=True, manzil='Chilonzor 5-kvartal', telefon='+998901234567',
        )
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_qoshgan_is_readonly(self):
        """qoshgan maydoni foydalanuvchi tomonidan o'zgartirib bo'lmaydi (owner=request.user)."""
        self.auth(self.rieltor_a)
        payload = self.valid_payload(qoshgan=self.rieltor_b.id)
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertEqual(kv.qoshgan_id, self.rieltor_a.id)

    def test_is_verified_readonly(self):
        """is_verified foydalanuvchi tomonidan o'rnatib bo'lmaydi (moderatsiya admin ishi)."""
        self.auth(self.rieltor_a)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertFalse(kv.is_verified, msg="Yangi kvartira avtomatik verified bo'lib qoldi!")
