from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        """Called when Django starts"""
        # Auto-create admin user after migrations
        post_migrate.connect(self.create_admin_user, sender=self)
    
    def create_admin_user(self, sender, **kwargs):
        """Create admin user from .env file if it doesn't exist"""
        from django.contrib.auth import get_user_model
        from django.conf import settings
        
        User = get_user_model()
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        admin_password = getattr(settings, 'ADMIN_PASSWORD', None)
        
        if admin_email and admin_password:
            try:
                user = User.objects.get(email=admin_email)
                # Update existing admin user
                if not user.is_staff or not user.is_superuser:
                    user.set_password(admin_password)
                    user.is_staff = True
                    user.is_superuser = True
                    user.is_active = True
                    user.is_verified = True
                    user.role = 'admin'
                    user.save()
            except User.DoesNotExist:
                # Create new admin user
                username = admin_email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                User.objects.create_user(
                    username=username,
                    email=admin_email,
                    password=admin_password,
                    is_staff=True,
                    is_superuser=True,
                    is_active=True,
                    is_verified=True,
                    role='admin'
                )
