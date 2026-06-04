from rest_framework.permissions import BasePermission


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


# Backward compatibility uchun alias'lar
IsMakler = IsRieltor
IsVerifiedMakler = IsVerifiedRieltor
IsAdminOrMakler = IsAdminOrRieltor