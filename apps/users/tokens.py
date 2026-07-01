from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """
    User uchun JWT token yaratadi va custom claim'lar qo'shadi.
    
    Custom claims:
    - role: user ning roli (admin, makler, user)
    - is_staff: admin panel huquqi
    - username: username yoki telegram_id
    """
    refresh = RefreshToken.for_user(user)
    
    # Custom claims qo'shish
    refresh['role'] = user.role
    refresh['is_staff'] = user.is_staff
    refresh['username'] = user.username or str(user.telegram_id)
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
