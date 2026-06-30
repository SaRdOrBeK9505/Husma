from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    def create_user(self, telegram_id=None, password=None, **extra_fields):
        # Admin (superuser) telegram_id'siz ham yaratilishi mumkin —
        # u username/parol bilan kiradi. Oddiy foydalanuvchi uchun
        # telegram_id majburiy.
        user = self.model(telegram_id=telegram_id, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, telegram_id=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo\'lishi kerak')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo\'lishi kerak')
        if not password:
            raise ValueError('Superuser uchun parol majburiy')

        return self.create_user(telegram_id, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MAKLER = 'makler', 'Rieltor'
        USER = 'user', 'Foydalanuvchi'

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

    # Rieltor uchun — username/parol login
    username = models.CharField(max_length=150, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'telegram_id'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return f"{self.full_name or self.telegram_username or self.telegram_id}"


class OTPKode(models.Model):
    """
    Rieltor ro'yxatdan o'tish OTP kodi.
    Register paytida vaqtinchalik saqlanadi, verify qilinganidan keyin o'chiriladi.
    """
    telegram_id = models.BigIntegerField()
    kode = models.CharField(max_length=6)
    # Registratsiya ma'lumotlarini JSON sifatida saqlab turamiz
    # (verify qilinganida foydalaniladi)
    register_data = models.JSONField(default=dict)
    yaratilgan_vaqt = models.DateTimeField(auto_now_add=True)
    amal_qilish_vaqti = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.amal_qilish_vaqti = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    @property
    def muddati_otganmi(self):
        return timezone.now() > self.amal_qilish_vaqti

    class Meta:
        verbose_name = 'OTP Kode'
        verbose_name_plural = 'OTP Kodlar'

    def __str__(self):
        return f"{self.telegram_id} — {self.kode}"