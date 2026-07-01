from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import CustomUser


class CustomUserChangeForm(forms.ModelForm):
    """
    Admin panelda foydalanuvchini tahrirlash formasi.
    'yangi_parol' — ixtiyoriy. To'ldirilsa, parol o'rnatiladi (hash qilinadi).
    Bo'sh qoldirilsa, eski parol o'zgarmaydi.
    """
    password = ReadOnlyPasswordHashField(
        label="Parol",
        help_text=(
            "Xom parol bu yerda ko'rinmaydi. Parolni o'zgartirish uchun "
            "quyidagi 'Yangi parol' maydonidan foydalaning."
        ),
    )
    
    yangi_parol = forms.CharField(
        label="Yangi parol",
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=(
            "Admin/rieltor uchun yangi parol. To'ldirsangiz, parol shu qiymatga "
            "o'rnatiladi (hash qilinadi). Bo'sh qoldirsangiz, eski parol o'zgarmaydi."
        ),
    )
    
    yangi_parol_confirm = forms.CharField(
        label="Yangi parolni tasdiqlash",
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text="Yuqoridagi parolni qaytadan kiriting.",
    )

    class Meta:
        model = CustomUser
        fields = '__all__'

    def clean_yangi_parol_confirm(self):
        yangi_parol = self.cleaned_data.get('yangi_parol')
        yangi_parol_confirm = self.cleaned_data.get('yangi_parol_confirm')
        
        # Agar yangi parol kiritilgan bo'lsa, tasdiqlash ham bo'lishi kerak
        if yangi_parol and yangi_parol != yangi_parol_confirm:
            raise forms.ValidationError("Parollar mos kelmaydi!")
        
        return yangi_parol_confirm

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
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=(
            "Admin uchun parol MAJBURIY. "
            "Telegram foydalanuvchi uchun ixtiyoriy (Telegram orqali kiradi)."
        ),
    )
    
    yangi_parol_confirm = forms.CharField(
        label="Parolni tasdiqlash",
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text="Yuqoridagi parolni qaytadan kiriting.",
    )

    class Meta:
        model = CustomUser
        fields = ('telegram_id', 'username', 'full_name', 'phone', 'role', 'is_staff', 'is_superuser')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        username = cleaned_data.get('username')
        yangi_parol = cleaned_data.get('yangi_parol')
        yangi_parol_confirm = cleaned_data.get('yangi_parol_confirm')
        
        # Admin uchun username va parol majburiy
        if role == CustomUser.Role.ADMIN or cleaned_data.get('is_staff'):
            if not username:
                raise forms.ValidationError("Admin uchun username majburiy!")
            if not yangi_parol:
                raise forms.ValidationError("Admin uchun parol majburiy!")
        
        # Agar parol kiritilgan bo'lsa, tasdiqlash ham bo'lishi kerak
        if yangi_parol and yangi_parol != yangi_parol_confirm:
            raise forms.ValidationError("Parollar mos kelmaydi!")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        yangi_parol = self.cleaned_data.get('yangi_parol')
        if yangi_parol:
            user.set_password(yangi_parol)
        else:
            # Agar parol kiritilmagan bo'lsa, unusable qilamiz
            user.set_unusable_password()
        if commit:
            user.save()
        return user


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    CustomUser uchun Django admin konfiguratsiyasi.
    Admin yaratish, parol o'zgartirish va foydalanuvchi boshqarish imkoniyati.
    """
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = [
        'id', 'username', 'full_name', 'telegram_id',
        'telegram_username', 'role', 'is_staff', 'is_active', 'created_at',
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['telegram_id', 'username', 'full_name', 'telegram_username', 'phone']
    ordering = ['-created_at']
    
    # Tahrirlash formasidagi maydonlar
    fieldsets = (
        ('Kirish ma\'lumotlari', {
            'fields': ('telegram_id', 'username', 'password'),
            'description': (
                "<strong>Diqqat:</strong> Parol hash qilingan holda saqlanadi va "
                "bu yerda ko'rinmaydi. Parolni o'zgartirish uchun quyidagi "
                "'Yangi parol' maydonlaridan foydalaning."
            ),
        }),
        ('Parolni o\'zgartirish', {
            'fields': ('yangi_parol', 'yangi_parol_confirm'),
            'classes': ('collapse',),  # Boshlang'ich holatda yopiq
            'description': (
                "Foydalanuvchining parolini o'zgartirish uchun yangi parolni "
                "kiriting va tasdiqlang. Bo'sh qoldirsangiz, eski parol saqlanadi."
            ),
        }),
        ('Profil', {
            'fields': ('full_name', 'telegram_username', 'phone', 'role')
        }),
        ('Huquqlar va ruxsatlar', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': (
                "<ul>"
                "<li><strong>is_active:</strong> Foydalanuvchi tizimga kira oladimi?</li>"
                "<li><strong>is_staff:</strong> Django admin paneliga kirish huquqi</li>"
                "<li><strong>is_superuser:</strong> Barcha huquqlar (super admin)</li>"
                "</ul>"
            ),
        }),
        ('Muhim sanalar', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Yangi foydalanuvchi yaratish formasidagi maydonlar
    add_fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'phone'),
            'description': (
                "<strong>Admin yaratish:</strong> Username va parol majburiy.<br>"
                "<strong>Telegram foydalanuvchi yaratish:</strong> Telegram ID majburiy."
            ),
        }),
        ('Telegram', {
            'classes': ('wide',),
            'fields': ('telegram_id', 'telegram_username'),
            'description': "Telegram orqali kiradigan foydalanuvchilar uchun to'ldiring.",
        }),
        ('Parol', {
            'classes': ('wide',),
            'fields': ('yangi_parol', 'yangi_parol_confirm'),
            'description': (
                "<strong style='color: red;'>Admin uchun parol MAJBURIY!</strong><br>"
                "Telegram foydalanuvchilari uchun ixtiyoriy (ular Telegram orqali kiradi)."
            ),
        }),
        ('Rol va huquqlar', {
            'classes': ('wide',),
            'fields': ('role', 'is_staff', 'is_superuser', 'is_active'),
            'description': (
                "<ul>"
                "<li><strong>admin:</strong> Tizim administratori (is_staff=True bo'lishi kerak)</li>"
                "<li><strong>makler:</strong> Ko'chmas mulk rieltori</li>"
                "<li><strong>user:</strong> Oddiy Telegram foydalanuvchi</li>"
                "</ul>"
            ),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        """
        Tahrirlash vaqtida password maydonini read-only qilamiz.
        Yangi parol o'rnatish uchun 'yangi_parol' maydoni ishlatiladi.
        """
        if obj:  # Tahrirlash
            return self.readonly_fields + ('password',)
        return self.readonly_fields
