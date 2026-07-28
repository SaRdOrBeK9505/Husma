"""
apps/kvartira/mixins.py

Rieltor kvartira endpointlari uchun qayta ishlatiladigan logging mixin.
Har bir so'rov/javob haqida tuzilgan ma'lumotni logs/kvartira_requests.log ga yozadi.

Xavfsizlik:
  - request.data ichidagi barcha ImageField/FileField qiymatlari baza64/binary
    sifatida EMAS, faqat "fayl_nomi (hajm MB)" ko'rinishida yoziladi.
  - Kvartira endpointida parol/token kabi maxfiy maydonlar yo'q,
    shuning uchun qo'shimcha filtrlash talab etilmaydi.
"""

import json
import logging

from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger('apps.kvartira.requests')

# Loglarda ko'rsatmaslik kerak bo'lgan maxfiy maydon nomlari
# (ehtiyot chorasi sifatida — bu endpointda aslida ular bo'lmaydi)
_MAXFIY_MAYDONLAR = frozenset({'password', 'token', 'secret', 'access_token', 'refresh_token'})


def _foydalanuvchi_malumot(user) -> str:
    """Request user dan insoniy o'qiladigan satr qaytaradi."""
    if user is None or not user.is_authenticated:
        return 'Anonim'
    user_id = getattr(user, 'id', '?')
    full_name = getattr(user, 'full_name', None) or ''
    telegram_id = getattr(user, 'telegram_id', None)
    parts = [f"id={user_id}"]
    if full_name:
        parts.append(f'full_name="{full_name}"')
    if telegram_id:
        parts.append(f"telegram_id={telegram_id}")
    return ', '.join(parts)


def _request_data_sanitize(data: dict) -> dict:
    """
    request.data lug'atini log uchun tozalaydi:
      - UploadedFile ob'ektlari -> "fayl_nomi (hajm MB)" satriga
      - Maxfiy maydonlar -> "***"
    """
    toza = {}
    for kalit, qiymat in data.items():
        kalit_kichik = kalit.lower()

        # Maxfiy maydonlarni yashirish
        if kalit_kichik in _MAXFIY_MAYDONLAR:
            toza[kalit] = '***'
            continue

        # Bitta fayl
        if isinstance(qiymat, UploadedFile):
            toza[kalit] = _fayl_ko_rinish(qiymat)

        # Fayl ro'yxati (rasmlar: [...])
        elif isinstance(qiymat, list):
            yangi_list = []
            for elem in qiymat:
                if isinstance(elem, UploadedFile):
                    yangi_list.append(_fayl_ko_rinish(elem))
                else:
                    yangi_list.append(elem)
            toza[kalit] = yangi_list

        else:
            toza[kalit] = qiymat

    return toza


def _fayl_ko_rinish(fayl: UploadedFile) -> str:
    """UploadedFile ni 'fayl_nomi (hajm MB)' ko'rinishiga o'tkazadi."""
    nomi = getattr(fayl, 'name', 'noma\'lum')
    hajm = getattr(fayl, 'size', None)
    if hajm is not None:
        return f"{nomi} ({hajm / (1024 * 1024):.2f}MB)"
    return nomi


def _data_json(data) -> str:
    """Ma'lumotni JSON satrga o'tkazadi; muvaffaqiyatsiz bo'lsa str() ishlatadi."""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        return str(data)


class LogRequestMixin:
    """
    Rieltor kvartira view'lari uchun logging mixin.

    Ishlatish:
        class RieltorKvartiraListCreateView(LogRequestMixin, ListCreateAPIView):
            log_action_name = "RIELTOR KVARTIRA LIST/CREATE"
            ...

    Har bir dispatch() chaqiruvida so'rov/javob ma'lumotlari avtomatik loglanadi.
    Mixin mavjud view mantig'ini o'zgartirmaydi — faqat log qo'shadi.
    """

    # Subklasslar bu atributni o'zlarining nomi bilan override qiladi
    log_action_name: str = 'RIELTOR KVARTIRA'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        self._log_request(request, response)
        return response

    def _log_request(self, request, response):
        method = request.method
        path = request.get_full_path()
        user_str = _foydalanuvchi_malumot(request.user)
        status_code = response.status_code

        # request.data ni faqat o'qish so'rovlarida ham yozamiz (GET uchun odatda bo'sh)
        raw_data = {}
        if hasattr(request, 'data'):
            try:
                raw_data = dict(request.data)
            except Exception:
                raw_data = {}

        sanitized = _request_data_sanitize(raw_data)

        separator = '=' * 50
        header = f"========== {self.log_action_name} — {method} =========="

        lines = [
            '',
            header,
            f"{'Method':<14}: {method}",
            f"{'Path':<14}: {path}",
            f"{'User':<14}: {user_str}",
            f"{'Request data':<14}: {_data_json(sanitized)}",
            f"{'Javob status':<14}: {status_code}",
        ]

        # 4xx — 400 bo'lsa serializer xatolari response.data da bo'ladi
        if 400 <= status_code < 500:
            errors = {}
            if hasattr(response, 'data') and isinstance(response.data, dict):
                errors = response.data
            lines.append(f"{'Errors':<14}: {_data_json(errors)}")

        # Muvaffaqiyatli yaratish — yaratilgan ob'ekt ID sini ko'rsat
        if status_code == 201 and hasattr(response, 'data') and isinstance(response.data, dict):
            obj_id = response.data.get('id')
            if obj_id is not None:
                lines.append(f"{'Ob\'ekt ID':<14}: {obj_id}")

        lines.append(separator)

        log_text = '\n'.join(lines)

        if status_code >= 500:
            logger.error(log_text)
        elif 400 <= status_code < 500:
            logger.warning(log_text)
        else:
            logger.info(log_text)

    # ------------------------------------------------------------------
    # Serializer xatolarini alohida (validation xato bo'lganda) log qilish
    # Bu metod view'larning perform_create / update kabi joylarida
    # call qilinmaydi — dispatch() da response orqali avtomatik ko'rinadi.
    # Lekin manual is_valid() chaqiriladigan view'lar uchun qo'shimcha
    # WARNING log yozuvchi yordamchi metod sifatida taqdim etiladi.
    # ------------------------------------------------------------------
    def _log_serializer_xato(self, serializer, label: str = ''):
        """
        serializer.is_valid() False qaytargan holatda xatolarni alohida WARNING log qiladi.
        RieltorKvartiraStatusView kabi APIView subklasslari uchun qo'lda chaqiriladi.
        """
        request = getattr(self, 'request', None)
        user_str = _foydalanuvchi_malumot(request.user if request else None)
        path = request.get_full_path() if request else '?'

        logger.warning(
            '\n'
            f"{'=' * 50}\n"
            f"SERIALIZER XATO — {label or self.log_action_name}\n"
            f"{'Path':<14}: {path}\n"
            f"{'User':<14}: {user_str}\n"
            f"{'Errors':<14}: {_data_json(serializer.errors)}\n"
            f"{'=' * 50}"
        )
