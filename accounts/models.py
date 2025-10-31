from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string


class User(AbstractUser):
    """Custom User model with role support"""
    ROLE_CHOICES = [
        ('youth', 'Job Seeker / Youth'),
        ('employer', 'Employer'),
        ('institution', 'Training Institution'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='youth')
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class EmailVerification(models.Model):
    """Email verification codes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'email_verifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} - {self.code}"
    
    @staticmethod
    def generate_code():
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        """Check if verification code has expired"""
        return timezone.now() > self.expires_at
    
    def verify(self):
        """Mark verification as complete"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()


class JobSeekerProfile(models.Model):
    """Profile for Job Seekers / Youth"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='job_seeker_profile')
    education_level = models.CharField(max_length=50, blank=True)
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    interests = models.TextField(blank=True, help_text="Career interests")
    bio = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_seeker_profiles'
    
    def __str__(self):
        return f"{self.user.username} - Job Seeker Profile"


class EmployerProfile(models.Model):
    """Profile for Employers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    company_description = models.TextField(blank=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employer_profiles'
    
    def __str__(self):
        return f"{self.company_name} - {self.user.username}"


class InstitutionProfile(models.Model):
    """Profile for Training Institutions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='institution_profile')
    institution_name = models.CharField(max_length=200)
    institution_type = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'institution_profiles'
    
    def __str__(self):
        return f"{self.institution_name} - {self.user.username}"
