"""
Management command to create admin user from environment variables
Run: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates or updates admin user from ADMIN_EMAIL and ADMIN_PASSWORD in .env file'

    def handle(self, *args, **options):
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        admin_password = getattr(settings, 'ADMIN_PASSWORD', None)
        
        if not admin_email:
            self.stdout.write(
                self.style.ERROR('ADMIN_EMAIL not set in .env file')
            )
            return
        
        if not admin_password:
            self.stdout.write(
                self.style.ERROR('ADMIN_PASSWORD not set in .env file')
            )
            return
        
        # Check if admin user already exists
        try:
            user = User.objects.get(email=admin_email)
            # Update existing user
            user.set_password(admin_password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.is_verified = True
            user.role = 'admin'
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Admin user "{admin_email}" updated successfully!')
            )
        except User.DoesNotExist:
            # Create new admin user
            username = admin_email.split('@')[0]  # Use email prefix as username
            
            # Check if username already exists, append number if needed
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=admin_email,
                password=admin_password,
                is_staff=True,
                is_superuser=True,
                is_active=True,
                is_verified=True,
                role='admin'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Admin user "{admin_email}" created successfully!')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nAdmin credentials:')
        )
        self.stdout.write(f'  Email: {admin_email}')
        self.stdout.write(f'  Username: {user.username}')
        self.stdout.write(f'  Password: [from .env file]')

