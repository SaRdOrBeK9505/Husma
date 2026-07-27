from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.conf import settings


def bepul_kvartira_limiti_tekshir(profil) -> dict:
    """
    Rieltorning kvartira joylashtirish limitini tekshiradi.

    Qoidalar:
    - Faol **obunasi** bor rieltor → cheksiz, limit yo'q.
    - Faqat **bepul sinov** davrida ishlayotgan rieltor →
      jami qo'shilgan kvartiralari ``BEPUL_KVARTIRA_LIMIT`` dan oshmasligi kerak.

    Returns:
        {
            "ruxsat": bool,           # True → joylashtirish mumkin
            "limit_faol": bool,       # True → bepul davr limiti ishlamoqda
            "jami": int,              # Hozirgi kvartiralar soni
            "limit": int,             # Ruxsat etilgan maksimal son
            "xabar": str,             # Foydalanuvchiga ko'rsatiladigan xabar (xato bo'lsa)
        }
    """
    limit = getattr(settings, 'BEPUL_KVARTIRA_LIMIT', 3)

    # Faol obuna bor → cheksiz
    if profil.obuna_faol:
        return {
            "ruxsat": True,
            "limit_faol": False,
            "jami": 0,
            "limit": limit,
            "xabar": "",
        }

    # Bepul sinov davri — limitni tekshiramiz
    jami = profil.user.kvartiralar.count()
    ruxsat = jami < limit

    return {
        "ruxsat": ruxsat,
        "limit_faol": True,
        "jami": jami,
        "limit": limit,
        "xabar": (
            f"Bepul sinov davrida faqat {limit} ta kvartira joylashtirish mumkin. "
            f"Cheksiz joylashtirish uchun obuna oling."
        ) if not ruxsat else "",
    }


class IsAdmin(BasePermission):
    message = 'Faqat adminlar uchun'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsRieltor(BasePermission):
    message = 'Faqat rieltorlar uchun'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'makler'
        )


class IsVerifiedRieltor(BasePermission):
    """
    Rieltor ishlashi mumkin bo'lgan holat:
    - Bepul sinov muddati (7 kun) ichida, YOKI
    - Faol obunasi bor (keyinchalik qo'shiladi)
    """
    message = 'Kirish uchun bepul sinov muddati tugagan. Obuna oling.'

    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.role == 'makler'):
            return False
        try:
            return request.user.rieltor_profil.faol
        except Exception:
            return False


class IsUser(BasePermission):
    message = 'Faqat foydalanuvchilar uchun'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'user'
        )


class IsAdminOrRieltor(BasePermission):
    message = 'Faqat admin yoki rieltorlar uchun'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ['admin', 'makler']
        )



class IsUserOrRieltor(BasePermission):
    message = 'Faqat foydalanuvchilar yoki rieltorlar uchun'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ['user', 'makler']
        )


class IsAdminOrActiveRieltor(BasePermission):
    """
    Kvartira (va shunga o'xshash) resurslarni BOSHQARISH uchun ruxsat.

    Mantiq:
    - Admin — har doim ruxsat (moderatsiya/qo'llab-quvvatlash uchun).
    - Rieltor (makler):
        * O'qish (GET/HEAD/OPTIONS) — role='makler' bo'lishi kifoya
          (o'z e'lonlari ro'yxatini ko'ra oladi).
        * Yozish (POST/PUT/PATCH/DELETE) — QO'SHIMCHA ravishda rieltor
          profili "faol" bo'lishi shart:
            - Admin bloklamagan (verify_holat != rejected), VA
            - Bepul sinov muddati ichida YOKI faol obunasi bor.
    - Boshqa rollar — rad etiladi.

    Bu sinf `IsAdminOrRieltor` o'rnini bosadi va bloklangan / muddati tugagan
    rieltorlarning yangi e'lon qo'shishi yoki tahrirlashini to'sadi.
    """
    message = 'Faqat admin yoki faol rieltorlar uchun.'

    # Rieltor faol emasligining aniq sabablari uchun xabarlar
    MSG_BLOCKED = 'Profilingiz admin tomonidan bloklangan. Qo\'llab-quvvatlashga murojaat qiling.'
    MSG_INACTIVE = 'Bepul sinov muddati tugagan yoki faol obunangiz yo\'q. Obuna oling.'
    MSG_NO_PROFILE = 'Rieltor profili topilmadi.'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        # Admin — cheklovsiz
        if user.role == 'admin':
            return True

        # Faqat rieltorlar davom etadi
        if user.role != 'makler':
            return False

        # O'qish amallari — role kifoya (queryset baribir o'z e'lonlari bilan cheklangan)
        if request.method in SAFE_METHODS:
            return True

        # Yozish amallari — rieltor "faol" bo'lishi shart
        profil = getattr(user, 'rieltor_profil', None)
        if profil is None:
            self.message = self.MSG_NO_PROFILE
            return False

        if profil.bloklangan:
            self.message = self.MSG_BLOCKED
            return False

        if not profil.faol:
            self.message = self.MSG_INACTIVE
            return False

        return True


# Backward compatibility uchun alias'lar
IsMakler = IsRieltor
IsVerifiedMakler = IsVerifiedRieltor
IsAdminOrMakler = IsAdminOrRieltor