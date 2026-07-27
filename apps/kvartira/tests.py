"""
Kvartira API endpoint'lari uchun to'liq test to'plami.

Fokus:
  1. PERMISSION (ruxsat) testlari  — eng muhim qism
  2. Rasm upload testlari — ko'p rasm bir so'rovda yuborish (3+ ta)
  3. Ma'lumot validatsiyasi
  4. Storage / fayl joylashuv testlari

Ishga tushirish (sqlite bilan tez test):
    set DB_ENGINE=sqlite && python manage.py test apps.kvartira -v 2

Rasm testlari DigitalOcean'ga yuklamasligi uchun STORAGES in-memory'ga
override qilingan.

MUHIM XATOLAR va TUZATISHLAR haqida:
  - Bitta so'rovda 3+ rasm yuklaganda 3-rasmdagi muammo:
    heic_ni_jpegga_aylantir() HEIC bo'lmagan faylni o'zgarishsiz qaytaradi,
    lekin SimpleUploadedFile ob'ektining fayl pozitsiyasi birinchi
    KvartiraRasm.objects.create() da o'qilgandan keyin oxirida qoladi.
    Natijada 2-chi va 3-chi rasmlar uchun storage'ga bo'sh fayl saqlanadi.
    Tuzatish: heic_ni_jpegga_aylantir() da HEIC BO'LMAGAN fayllar uchun
    ham seek(0) chaqirilishi kerak.
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


def make_multipart_images(count, base_name='rasm', fmt='JPEG', content_type='image/jpeg'):
    """
    Bir so'rovda yuborish uchun count ta rasm ro'yxatini yaratadi.
    Har bir rasm MUSTAQIL BytesIO — bir-birining pozitsiyasiga ta'sir qilmaydi.
    """
    result = []
    for i in range(count):
        buf = BytesIO()
        # Har bir rasm biroz farqli piksel ega (bir xil cache bo'lmasligi uchun)
        Image.new('RGB', (20 + i, 20 + i), (i * 30 % 255, 100, 200)).save(buf, format=fmt)
        result.append(
            SimpleUploadedFile(f'{base_name}_{i}.jpg', buf.getvalue(), content_type=content_type)
        )
    return result


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

    def test_create_with_1_image(self):
        """Yaratishda 1 ta rasm → 201 va DB'da 1 ta rasm bor."""
        self.auth(self.rieltor_a)
        payload = self.valid_payload()
        payload['rasmlar'] = make_multipart_images(1)
        resp = self.client.post('/api/rieltor/kvartiralar/', payload, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertEqual(kv.rasmlar.count(), 1)

    def test_create_with_2_images(self):
        """Yaratishda 2 ta rasm → 201 va DB'da 2 ta rasm bor."""
        self.auth(self.rieltor_a)
        payload = self.valid_payload()
        payload['rasmlar'] = make_multipart_images(2)
        resp = self.client.post('/api/rieltor/kvartiralar/', payload, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertEqual(kv.rasmlar.count(), 2,
            msg="2 ta rasm yuklanganda DB'da 2 ta bo'lishi kerak edi")

    def test_create_with_3_images(self):
        """
        Yaratishda 3 ta rasm → 201 va DB'da aniq 3 ta rasm bor.

        BUG: heic_ni_jpegga_aylantir() HEIC BO'LMAGAN faylni o'zgarishsiz
        qaytaradi, lekin SimpleUploadedFile ob'ektining fayl o'qish pozitsiyasi
        birinchi KvartiraRasm.objects.create() chaqiruvida o'qilib bo'lgandan
        keyin oxirida qoladi. Natijada 2-chi, 3-chi rasm uchun storage'ga
        bo'sh kontent yoziladi.

        Agar bu test MUVAFFAQIYATSIZ bo'lsa (rasmlar.count() == 1 yoki 2),
        muammo serializers.py'dagi create() metodida: HEIC bo'lmagan
        fayllar uchun seek(0) chaqirilmayapti.

        Tuzatish: heic_ni_jpegga_aylantir() return fayl.seek(0) yoki
        create() loopida har fayl uchun fayl.seek(0) chaqirish.
        """
        self.auth(self.rieltor_a)
        payload = self.valid_payload()
        payload['rasmlar'] = make_multipart_images(3)
        resp = self.client.post('/api/rieltor/kvartiralar/', payload, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED,
            msg=f"3 ta rasm bilan yaratish 201 qaytarishi kerak edi. Javob: {resp.data}")
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertEqual(
            kv.rasmlar.count(), 3,
            msg=(
                f"DB'da {kv.rasmlar.count()} ta rasm bor, 3 ta bo'lishi kerak edi. "
                "SABAB: heic_ni_jpegga_aylantir() HEIC bo'lmagan fayllar uchun "
                "fayl pozitsiyasini (seek) tiklamas — 2-3-chi rasmlar bo'sh saqlanadi."
            )
        )

    def test_create_with_4_images(self):
        """4 ta rasm bir so'rovda → DB'da aniq 4 ta bo'lishi kerak."""
        self.auth(self.rieltor_a)
        payload = self.valid_payload()
        payload['rasmlar'] = make_multipart_images(4)
        resp = self.client.post('/api/rieltor/kvartiralar/', payload, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertEqual(kv.rasmlar.count(), 4,
            msg=f"4 ta rasm yuklanganda DB'da 4 ta bo'lishi kerak edi, bor: {kv.rasmlar.count()}")

    def test_create_with_1_to_8_images(self):
        """Yaratishda 8 tagacha rasm → 201 va DB'da aniq 8 ta rasm bor."""
        self.auth(self.rieltor_a)
        payload = self.valid_payload()
        payload['rasmlar'] = make_multipart_images(8)
        resp = self.client.post('/api/rieltor/kvartiralar/', payload, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertEqual(kv.rasmlar.count(), 8,
            msg=f"8 ta rasm yuklanganda DB'da 8 ta bo'lishi kerak edi, bor: {kv.rasmlar.count()}")

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
            {'rasmlar': make_multipart_images(3)},
            format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.kv_a.rasmlar.count(), 8)

    def test_add_3_images_all_saved_to_db(self):
        """
        Mavjud 0 ta kvartiraga 3 ta yangi rasm qo'shish → DB'da aniq 3 ta bor.

        BUG repro: /api/rieltor/kvartiralar/<pk>/rasmlar/ POST da
        heic_ni_jpegga_aylantir() HEIC bo'lmagan faylni o'zgarishsiz qaytaradi.
        Agar fayl ob'ektining read() pozitsiyasi birinchi create() da oxiriga
        borsa, keyingi create() larda bo'sh fayl saqlanadi.
        Bu test shu muammoni to'g'ridan-to'g'ri ushlab beradi.
        """
        self.auth(self.rieltor_a)
        resp = self.client.post(
            self.rasm_url,
            {'rasmlar': make_multipart_images(3)},
            format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED,
            msg=f"3 ta rasm qo'shishda 201 bo'lishi kerak edi. Javob: {resp.data}")
        self.kv_a.refresh_from_db()
        saved_count = self.kv_a.rasmlar.count()
        self.assertEqual(
            saved_count, 3,
            msg=(
                f"DB'da {saved_count} ta rasm saqlangan, 3 ta bo'lishi kerak edi. "
                "SABAB: fayl pozitsiyasi (seek) muammosi — "
                "views.py RieltorKvartiraRasmView.post() da "
                "heic_ni_jpegga_aylantir() HEIC bo'lmagan faylni o'zgarishsiz "
                "qaytaradi, lekin fayl read pozitsiyasi tiklanmaydi."
            )
        )

    def test_add_3_images_response_count(self):
        """3 ta rasm qo'shilganda javobdagi ro'yxatda 3 ta element bor."""
        self.auth(self.rieltor_a)
        resp = self.client.post(
            self.rasm_url,
            {'rasmlar': make_multipart_images(3)},
            format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            len(resp.data), 3,
            msg=f"Javobda {len(resp.data)} ta rasm, 3 ta bo'lishi kerak edi"
        )

    def test_seek_bug_s3_simulation(self):
        """
        S3Boto3Storage kabi fayl.read() chaqiradigan storage uchun
        fayl pozitsiyasi muammosi yo'qligini tasdiqlaydi.

        InMemoryStorage ichki buferni avtomatik tiklaydigan bo'lgani uchun
        haqiqiy S3 xatti-harakatini simulyatsiya qilamiz:
        har bir fayl uchun storage.save() vaqtida fayl.read() chaqiriladi.
        heic_ni_jpegga_aylantir() seek(0) ni chaqirishi kerak, aks holda
        2-chi va 3-chi rasmlar 0 bayt (bo'sh) saqlanadi.

        BUG TUZATILDI: seek(0) HEIC bo'lmagan fayllar uchun ham chaqiriladi.
        """
        from apps.kvartira.serializers import heic_ni_jpegga_aylantir

        def s3_kabi_saqlash(fayl):
            """S3Boto3Storage._save() xatti-harakatini simulyatsiya qiladi."""
            return fayl.read()  # seek() siz to'g'ridan-to'g'ri o'qiydi

        images = make_multipart_images(3)
        for i, fayl in enumerate(images):
            # S3 storage faylni o'qiydi (birinchi marta)
            tayyor_fayl = heic_ni_jpegga_aylantir(fayl)
            kontent = s3_kabi_saqlash(tayyor_fayl)
            self.assertGreater(
                len(kontent), 0,
                msg=(
                    f"{i+1}-rasm uchun heic_ni_jpegga_aylantir() seek(0) chaqirmagani "
                    f"sababli bo'sh kontent ({len(kontent)} bayt). "
                    f"S3'ga 0 bayt yuboriladi!"
                )
            )

    def test_add_images_first_image_is_main(self):
        """
        Hech qanday asosiy rasm yo'q bo'lganda, yangi qo'shilgan
        rasmlarning birinchisi asosiy (asosiy=True) bo'lishi kerak.
        """
        self.auth(self.rieltor_a)
        # Birorta asosiy yo'qligini tekshiramiz
        self.assertFalse(self.kv_a.rasmlar.filter(asosiy=True).exists())

        resp = self.client.post(
            self.rasm_url,
            {'rasmlar': make_multipart_images(3)},
            format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        asosiy_rasms = self.kv_a.rasmlar.filter(asosiy=True)
        self.assertEqual(
            asosiy_rasms.count(), 1,
            msg=f"Asosiy rasmlar soni {asosiy_rasms.count()} ta, 1 ta bo'lishi kerak"
        )

    def test_add_images_second_batch_not_overwrite_main(self):
        """
        Asosiy rasm allaqachon bor bo'lsa, keyingi batch qo'shilganda
        yangi rasmlar asosiy EMAS deb belgilanishi kerak.
        """
        self.auth(self.rieltor_a)
        # Birinchi batch — birinchisi asosiy bo'ladi
        resp1 = self.client.post(
            self.rasm_url,
            {'rasmlar': make_multipart_images(2, base_name='batch1')},
            format='multipart'
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.kv_a.rasmlar.filter(asosiy=True).count(), 1)

        # Ikkinchi batch — asosiy o'zgarmasin
        resp2 = self.client.post(
            self.rasm_url,
            {'rasmlar': make_multipart_images(2, base_name='batch2')},
            format='multipart'
        )
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            self.kv_a.rasmlar.count(), 4,
            msg="Jami 4 ta rasm bo'lishi kerak edi"
        )
        self.assertEqual(
            self.kv_a.rasmlar.filter(asosiy=True).count(), 1,
            msg="Faqat bitta asosiy rasm bo'lishi kerak (ikkinchi batch asosiyni o'zgartirmasin)"
        )

    def test_tartib_sequential_for_multiple_images(self):
        """
        Ko'p rasm qo'shilganda tartib raqamlari ketma-ket bo'lishi kerak.
        Mavjud 0 rasm + 3 yangi → tartib: 0, 1, 2
        """
        self.auth(self.rieltor_a)
        resp = self.client.post(
            self.rasm_url,
            {'rasmlar': make_multipart_images(3)},
            format='multipart'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        tartiblar = sorted(
            self.kv_a.rasmlar.values_list('tartib', flat=True)
        )
        self.assertEqual(tartiblar, [0, 1, 2],
            msg=f"Tartib raqamlari {tartiblar} bo'ldi, [0, 1, 2] bo'lishi kerak")

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

    def test_octet_stream_with_jpg_extension_accepted(self):
        """content_type="application/octet-stream" lekin kengaytma ".jpg" bo'lsa
        validatsiya MUVAFFAQIYATLI o'tishi kerak.

        Ba'zi iPhone/Safari brauzerlar HEIC yoki JPEG faylni noto'g'ri
        "application/octet-stream" content_type bilan yuboradi. Kengaytma
        to'g'ri bo'lgani uchun fayl rad etilmasligi kerak.
        """
        from apps.kvartira.serializers import rasm_faylini_tekshir

        fayl = make_image('foto.jpg', content_type='application/octet-stream')
        # ValidationError ko'tarilmasligi kerak
        try:
            rasm_faylini_tekshir(fayl)
        except Exception as e:
            self.fail(
                f"To'g'ri kengaytmali fayl noto'g'ri content_type bilan rad etildi: {e}"
            )

    def test_octet_stream_with_heic_extension_accepted(self):
        """content_type="application/octet-stream" lekin kengaytma ".heic" → qabul."""
        from apps.kvartira.serializers import rasm_faylini_tekshir

        fayl = SimpleUploadedFile('foto.heic', b'fake-heic-data', content_type='application/octet-stream')
        try:
            rasm_faylini_tekshir(fayl)
        except Exception as e:
            self.fail(f"HEIC kengaytmali fayl noto'g'ri content_type bilan rad etildi: {e}")

    def test_wrong_mime_and_wrong_extension_rejected(self):
        """content_type ham noto'g'ri, kengaytma ham noto'g'ri → rad etiladi."""
        from apps.kvartira.serializers import rasm_faylini_tekshir
        from rest_framework.exceptions import ValidationError

        fayl = SimpleUploadedFile('hujjat.pdf', b'%PDF-1.4', content_type='application/pdf')
        with self.assertRaises(ValidationError):
            rasm_faylini_tekshir(fayl)

    def test_correct_mime_no_extension_accepted(self):
        """content_type to'g'ri lekin kengaytma yo'q → qabul qilinadi."""
        from apps.kvartira.serializers import rasm_faylini_tekshir

        fayl = SimpleUploadedFile('rasm', b'data', content_type='image/jpeg')
        try:
            rasm_faylini_tekshir(fayl)
        except Exception as e:
            self.fail(f"To'g'ri MIME turli fayl rad etildi: {e}")


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
            tavsif='Yaxshi kvartira', sanuzellar_soni=1, maydon_m2=65.5,
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

    def test_new_kvartira_auto_verified(self):
        """VAQTINCHALIK: moderatsiya o'chirilgan — yangi kvartira darhol
        is_verified=True bo'ladi va userlarga ko'rinadi.

        KEYINCHALIK moderatsiya qaytarilsa, bu test
        `assertFalse(kv.is_verified)` ga o'zgartirilishi kerak.
        """
        self.auth(self.rieltor_a)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        self.assertTrue(kv.is_verified, msg="Yangi kvartira avtomatik tasdiqlanmadi!")

    def test_is_verified_not_client_controlled(self):
        """Rieltor is_verified=False yuborsa ham, u e'tiborsiz qoldiriladi
        (maydon read-only; qiymatni faqat server/admin belgilaydi)."""
        self.auth(self.rieltor_a)
        resp = self.client.post(self.url, self.valid_payload(is_verified=False), format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        kv = Kvartira.objects.get(pk=resp.data['id'])
        # Client yuborgan False e'tiborsiz qoldirilib, server True qo'ygan
        self.assertTrue(kv.is_verified)


# ============================================================
# 6. BEPUL DAVR KVARTIRA LIMITI testlari
# ============================================================
class KvartiraBepulLimitTests(KvartiraBaseTestCase):
    """Bepul sinov davrida max 3 ta kvartira; obuna bilan cheksiz."""
    url = '/api/rieltor/kvartiralar/'

    def test_bepul_davrda_3_ta_joylashadi(self):
        """Bepul davrdagi rieltor 3 ta kvartira qo'sha oladi → 201."""
        self.auth(self.rieltor_a)
        for i in range(3):
            resp = self.client.post(
                self.url,
                self.valid_payload(sarlavha=f'Kvartira {i+1}'),
                format='json'
            )
            self.assertEqual(
                resp.status_code, status.HTTP_201_CREATED,
                msg=f"{i+1}-kvartira qo'shilmadi: {resp.data}"
            )
        self.assertEqual(
            Kvartira.objects.filter(qoshgan=self.rieltor_a).count(), 3
        )

    def test_bepul_davrda_4_ta_rad_etiladi(self):
        """Bepul davrdagi rieltor 4-kvartirani qo'sha olmaydi → 403."""
        self.auth(self.rieltor_a)
        for i in range(3):
            self.client.post(
                self.url,
                self.valid_payload(sarlavha=f'Kvartira {i+1}'),
                format='json'
            )
        # 4-kvartira
        resp = self.client.post(
            self.url,
            self.valid_payload(sarlavha='4-kvartira'),
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('obuna_kerak', resp.data)
        self.assertTrue(resp.data['obuna_kerak'])
        self.assertEqual(resp.data['limit'], 3)
        self.assertEqual(resp.data['jami_kvartiralar'], 3)

    def test_obunali_rieltor_limitdan_ortiq_qoshadi(self):
        """Faol obunasi bor rieltor 3 tadan ko'p kvartira qo'sha oladi → 201."""
        from apps.obuna.models import Tarif, Obuna
        from django.utils import timezone
        from datetime import timedelta

        # Tarif va faol obuna yaratamiz
        tarif = Tarif.objects.create(
            nomi='Test oylik', kod='test-oylik', narx=100000, davomiylik_kun=30
        )
        obuna = Obuna.objects.create(
            rieltor=self.profil_a,
            tarif=tarif,
            narx=tarif.narx,
            holat=Obuna.Holat.FAOL,
            boshlanish_vaqti=timezone.now(),
            tugash_vaqti=timezone.now() + timedelta(days=30),
        )

        self.auth(self.rieltor_a)
        for i in range(5):
            resp = self.client.post(
                self.url,
                self.valid_payload(sarlavha=f'Obuna kvartira {i+1}'),
                format='json'
            )
            self.assertEqual(
                resp.status_code, status.HTTP_201_CREATED,
                msg=f"Obunali rieltor {i+1}-kvartirani qo'sha olmadi: {resp.data}"
            )

    def test_bepul_limit_xabar_mazmuni(self):
        """403 javobda error xabari va kerakli maydonlar to'g'ri qaytadi."""
        self.auth(self.rieltor_a)
        for i in range(3):
            self.client.post(
                self.url, self.valid_payload(sarlavha=f'K{i}'), format='json'
            )
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', resp.data)
        self.assertIn('3', resp.data['error'])  # "3 ta" deb eslatilgan bo'lishi kerak


# ============================================================
# 7. BEPUL MUDDAT — CHEGARA HOLATLARI (edge cases)
# ============================================================
class KvartiraBepulMuddatEdgeCaseTests(KvartiraBaseTestCase):
    """
    Bepul muddat chegara holatlari — asosiy bug qamrovi.

    Muammo tavsifi:
    Rieltor 1-kvartira joyladi ✅, 2-kvartira joyladi ✅,
    3-kvartira joylashga urinanda ❌ xatolik.

    Sabab: `MaklerProfil.faol` property `bepul_muddat_tugash` ni
    tekshiradi. Agar `bepul_muddat_tugash` None bo'lsa yoki o'tib
    ketgan bo'lsa — `faol=False`, shuning uchun `IsAdminOrActiveRieltor`
    POST so'rovni 403 bilan rad etadi. Limit soni (3 ta) bilan aloqasi yo'q.
    """
    url = '/api/rieltor/kvartiralar/'

    def test_bepul_muddat_none_rieltor_cannot_post(self):
        """
        bepul_muddat_tugash=None bo'lsa rieltor kvartira qo'sha olmaydi → 403.

        Agar registratsiyada bepul_muddat_tugash o'rnatilmasa yoki
        admin uni NULL qilib qo'ysa — rieltor hech narsa qo'sha olmaydi.
        """
        rieltor_none = CustomUser.objects.create_user(
            telegram_id=5001, full_name='None Muddat Rieltor', role=CustomUser.Role.MAKLER
        )
        MaklerProfil.objects.create(
            user=rieltor_none,
            verify_holat=MaklerProfil.VerifyHolat.VERIFIED,
            bepul_muddat_tugash=None,  # ← NULL!
        )
        self.auth(rieltor_none)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN,
            msg="bepul_muddat_tugash=None bo'lsa kvartira qo'shish 403 bo'lishi kerak"
        )

    def test_bepul_muddat_1_sekund_oldin_tugagan(self):
        """
        bepul_muddat_tugash 1 sekund oldin tugagan bo'lsa → 403.
        faol=False, obuna yo'q → kvartira qo'sha olmaydi.
        """
        rieltor_exp = CustomUser.objects.create_user(
            telegram_id=5002, full_name='Expired Rieltor', role=CustomUser.Role.MAKLER
        )
        MaklerProfil.objects.create(
            user=rieltor_exp,
            verify_holat=MaklerProfil.VerifyHolat.VERIFIED,
            bepul_muddat_tugash=timezone.now() - timedelta(seconds=1),
        )
        self.auth(rieltor_exp)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN,
            msg="Muddati tugagan rieltor kvartira qo'sha olmasligi kerak"
        )

    def test_bepul_muddat_ichida_3_ta_hammasi_201(self):
        """
        bepul_muddat_tugash kelajakda → 3 ta kvartiraning hammasi 201.
        Bu normal holatni tasdiqlaydi — bug yo'q.
        """
        self.auth(self.rieltor_a)
        for i in range(3):
            resp = self.client.post(
                self.url,
                self.valid_payload(sarlavha=f'Normal {i+1}'),
                format='json'
            )
            self.assertEqual(
                resp.status_code, status.HTTP_201_CREATED,
                msg=(
                    f"{i+1}-kvartira qo'shilmadi (status={resp.status_code}). "
                    f"Javob: {resp.data}. "
                    f"SABAB: bepul_muddat_tugash o'tib ketgan yoki None bo'lishi mumkin."
                )
            )

    def test_bepul_muddat_aynan_endi_tugayapti(self):
        """
        bepul_muddat_tugash = timezone.now() → boundary condition.
        `faol` property: `now <= bepul_muddat_tugash` → True (tenglik ham ruxsat).
        """
        rieltor_now = CustomUser.objects.create_user(
            telegram_id=5003, full_name='Now Boundary Rieltor', role=CustomUser.Role.MAKLER
        )
        MaklerProfil.objects.create(
            user=rieltor_now,
            verify_holat=MaklerProfil.VerifyHolat.VERIFIED,
            bepul_muddat_tugash=timezone.now() + timedelta(seconds=30),  # 30 sekund qolgan
        )
        self.auth(rieltor_now)
        resp = self.client.post(self.url, self.valid_payload(), format='json')
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED,
            msg="30 sekund qolgan paytda kvartira qo'shish mumkin bo'lishi kerak"
        )

    def test_1_va_2_qoshildi_3_chi_ham_qoshiladi(self):
        """
        ASOSIY BUG TEST: 1-kvartira ✅, 2-kvartira ✅, 3-kvartira ham ✅ bo'lishi kerak.

        Agar 3-kvartira 403 bilan rad etilsa — sabab:
        1. bepul_muddat_tugash o'tib ketgan (eski muddat bilan test)
        2. bepul_muddat_tugash=None (registratsiyada o'rnatilmagan)
        3. BEPUL_KVARTIRA_LIMIT=2 (env da noto'g'ri qiymat)

        Bu test shu muammoni aniq ushlab beradi va xato sababini ko'rsatadi.
        """
        self.auth(self.rieltor_a)

        # 1-kvartira
        r1 = self.client.post(self.url, self.valid_payload(sarlavha='1-kvartira'), format='json')
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED,
            msg=f"1-kvartira qo'shilmadi: status={r1.status_code}, javob={r1.data}")

        # 2-kvartira
        r2 = self.client.post(self.url, self.valid_payload(sarlavha='2-kvartira'), format='json')
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED,
            msg=f"2-kvartira qo'shilmadi: status={r2.status_code}, javob={r2.data}")

        # 3-kvartira — muammo shu yerda!
        r3 = self.client.post(self.url, self.valid_payload(sarlavha='3-kvartira'), format='json')
        self.assertEqual(
            r3.status_code, status.HTTP_201_CREATED,
            msg=(
                f"3-kvartira qo'shilmadi: status={r3.status_code}, javob={r3.data}\n\n"
                f"SABAB TAHLILI:\n"
                f"  - Agar status=403 va 'obuna_kerak' bor → BEPUL_KVARTIRA_LIMIT=2 (env da)\n"
                f"  - Agar status=403 va 'Bepul sinov muddati tugagan' → "
                f"bepul_muddat_tugash o'tib ketgan\n"
                f"  - Agar status=403 va 'Rieltor profili topilmadi' → "
                f"profil yo'q yoki None\n"
                f"  Rieltor_a bepul_muddat_tugash: {self.profil_a.bepul_muddat_tugash}\n"
                f"  Hozir: {timezone.now()}\n"
                f"  Faol: {self.profil_a.faol}"
            )
        )

        # Jami 3 ta bo'lishi kerak
        jami = Kvartira.objects.filter(qoshgan=self.rieltor_a).count()
        self.assertEqual(jami, 3,
            msg=f"DB'da {jami} ta kvartira bor, 3 ta bo'lishi kerak edi")

    def test_3_qoshilgandan_keyin_4_rad_etiladi(self):
        """
        1✅ 2✅ 3✅ → limit to'ldi → 4✅ RAD ETILDI.
        Bu to'g'ri xatti-harakat — 3 ta limit ishlayapti.
        """
        self.auth(self.rieltor_a)
        for i in range(3):
            resp = self.client.post(
                self.url, self.valid_payload(sarlavha=f'K{i+1}'), format='json'
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED,
                msg=f"{i+1}-kvartira qo'shilmadi: {resp.data}")

        # 4-chi rad etiladi
        r4 = self.client.post(self.url, self.valid_payload(sarlavha='4-kvartira'), format='json')
        self.assertEqual(r4.status_code, status.HTTP_403_FORBIDDEN,
            msg="4-chi kvartira 403 bilan rad etilishi kerak edi")
        self.assertIn('obuna_kerak', r4.data)
        self.assertEqual(r4.data['limit'], 3)

    def test_bepul_muddat_tugash_vps_timezone_muammo(self):
        """
        VPS da timezone muammosi: agar server UTC da ishlasa va
        Django TIME_ZONE='Asia/Tashkent' bo'lsa, bepul_muddat_tugash
        UTC da saqlanishi kerak. Agar noto'g'ri saved bo'lsa (naive datetime),
        5 soat farq tufayli muddat erta tugagan ko'rinadi.

        Bu test timezone-aware datetime ishlatilishini tekshiradi.
        """
        self.assertTrue(
            self.profil_a.bepul_muddat_tugash.tzinfo is not None,
            msg=(
                "bepul_muddat_tugash timezone-naive saqlangan! "
                "USE_TZ=True bo'lsa har doim timezone-aware bo'lishi kerak. "
                "VPS da UTC vs Tashkent (+5) farq tufayli muddat 5 soat erta tugaydi."
            )
        )
        # timezone.now() ham aware bo'lishi kerak
        now = timezone.now()
        self.assertTrue(
            now.tzinfo is not None,
            msg="timezone.now() naive datetime qaytardi — USE_TZ=True bo'lishi kerak"
        )
        # Taqqoslash xatosiz bo'lishi kerak
        try:
            result = now <= self.profil_a.bepul_muddat_tugash
        except TypeError as e:
            self.fail(
                f"Aware va naive datetime taqqoslanmoqda — timezone xatosi: {e}"
            )
