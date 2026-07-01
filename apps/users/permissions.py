from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Faqat admin roleiga ega yoki is_staff=True foydalanuvchilarga ruxsat.
    Admin panel endpointlari uchun ishlatiladi.
    """
    message = "Sizda admin huquqi yo'q."

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and (request.user.role == 'admin' or request.user.is_staff)
        )


class IsStaffUser(BasePermission):
    """
    is_staff=True bo'lgan foydalanuvchilarga ruxsat.
    Django admin panel uchun standart permission.
    """
    message = "Sizda staff huquqi yo'q."

    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_staff
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Admin uchun to'liq huquq, boshqalar faqat o'qiy oladi.
    Public API endpointlari uchun.
    """
    def has_permission(self, request, view):
        # GET, HEAD, OPTIONS - hamma uchun
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # POST, PUT, PATCH, DELETE - faqat admin
        return (
            request.user 
            and request.user.is_authenticated 
            and (request.user.role == 'admin' or request.user.is_staff)
        )
