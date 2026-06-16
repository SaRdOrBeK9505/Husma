from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserChangeForm(forms.ModelForm):
    """
    Admin panelda foydalanuvchini tahrirlash formasi.
    'yangi_parol' — ixtiyoriy. To'ldirilsa, parol o'rnatiladi (hash qilinadi).
    Bo'sh qoldirilsa, eski parol o'zgarmaydi.
    """
    yangi_parol = forms.CharField(
        label="Yangi parol",
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'new-password'}),
        help_text=(
            "Rieltor uchun yangi parol. To'ldirsangiz, parol shu qiymatga "
            "o'rnatiladi. Bo'sh qoldirsangiz, eski parol o'zgarmaydi."
        ),
    )

    class Meta:
        model = CustomUser
        fields = '__all__'

    def save(self, commit=True):
        user = super().save(commit=False)
        yangi_parol = self.cleaned_data.get('yangi_parol')
        if yangi_parol:
            user.set_password(yangi_parol)
        if commit:
            user.save()
            self.save_m2m()
        return user


class CustomUserCreationForm(forms.ModelForm):
    """Admin panelda yangi foydalanuvchi yaratish formasi."""
    yangi_parol = forms.CharField(
        label="Parol",
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'new-password'}),
        help_text="Rieltor/admin uchun parol (username bilan kirish uchun).",
    )

    class Meta:
        model = CustomUser
        fields = ('telegram_id', 'username', 'full_name', 'phone', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        yangi_parol = self.cleaned_data.get('yangi_parol')
        if yangi_parol:
            user.set_password(yangi_parol)
        else:
            user.set_unusable_password()
        if commit:
            user.save()
        return user


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = [
        'id', 'username', 'full_name', 'telegram_id',
        'telegram_username', 'role', 'is_active', 'created_at',
    ]
    list_filter = ['role', 'is_active']
    search_fields = ['telegram_id', 'username', 'full_name', 'telegram_username', 'phone']
    ordering = ['-created_at']

    fieldsets = (
        ('Kirish ma\'lumotlari', {
            'fields': ('telegram_id', 'username', 'yangi_parol'),
            'description': "Rieltor username va parol bilan kiradi. "
                           "Parolni o'zgartirish uchun 'Yangi parol'ni to'ldiring.",
        }),
        ('Profil', {'fields': ('full_name', 'telegram_username', 'phone', 'role')}),
        ('Huquqlar', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('telegram_id', 'username', 'yangi_parol', 'full_name', 'phone', 'role'),
        }),
    )
