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
    location = models.CharField(max_length=200, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
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
    location = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
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


class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPES = [
        ('job_application', 'Job Application Update'),
        ('job_match', 'New Job Match'),
        ('course_enrollment', 'Course Enrollment'),
        ('message', 'New Message'),
        ('system', 'System Notification'),
        ('admin', 'Admin Announcement'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='system')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Message(models.Model):
    """In-app messaging between users"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}"


class Interview(models.Model):
    """Interview scheduling"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    application = models.ForeignKey('jobs.Application', on_delete=models.CASCADE, related_name='interviews')
    scheduled_at = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    meeting_link = models.URLField(blank=True, help_text="Zoom/Teams link for virtual interviews")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'interviews'
        ordering = ['scheduled_at']
    
    def __str__(self):
        return f"Interview for {self.application.job.job_title}"


class SavedCandidate(models.Model):
    """Saved candidates by employers"""
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_candidates', limit_choices_to={'role': 'employer'})
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_by_employers', limit_choices_to={'role': 'youth'})
    notes = models.TextField(blank=True, help_text="Employer notes about this candidate")
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_candidates'
        unique_together = [['employer', 'candidate']]
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.employer.username} saved {self.candidate.username}"


class SupportTicket(models.Model):
    """Support tickets for admin"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'role': 'admin'})
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'support_tickets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"
