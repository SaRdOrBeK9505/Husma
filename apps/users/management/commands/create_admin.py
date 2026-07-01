"""
Admin user yaratish uchun custom command.
Username va parol bilan admin user yaratadi.
"""
from django.core.management.base import BaseCommand
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = 'Admin user yaratish (username va parol bilan)'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--password', type=str, help='Admin parol')

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')

        # Agar argument berilmagan bo'lsa, interaktiv ravishda so'raymiz
        if not username:
            username = input("Username: ")
        
        if not password:
            from getpass import getpass
            password = getpass("Parol: ")
            password_confirm = getpass("Parolni takrorlang: ")
            
            if password != password_confirm:
                self.stdout.write(self.style.ERROR("Parollar mos kelmadi!"))
                return

        # Username mavjudligini tekshirish
        if CustomUser.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f"Username '{username}' allaqachon mavjud!")
            )
            return

        # Admin user yaratish
        user = CustomUser.objects.create(
            username=username,
            role=CustomUser.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
            full_name=f"Admin ({username})",
            telegram_id=None,  # Admin uchun telegram_id shart emas
        )
        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Admin user muvaffaqiyatli yaratildi!\n"
                f"  Username: {username}\n"
                f"  Role: {user.role}\n"
                f"  is_staff: {user.is_staff}\n"
                f"  is_superuser: {user.is_superuser}"
            )
        )
