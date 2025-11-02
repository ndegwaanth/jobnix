from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Job(models.Model):
    """Job posting model with all required fields"""
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('apprenticeship', 'Apprenticeship'),
        ('freelance', 'Freelance'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ]
    
    SOURCE_CHOICES = [
        ('brightermonday', 'BrighterMonday'),
        ('linkedin', 'LinkedIn'),
        ('company_site', 'Company Website'),
        ('jobnix', 'JobNix'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('expired', 'Expired'),
    ]
    
    # Basic Information
    job_title = models.CharField(max_length=200, db_index=True)
    company_name = models.CharField(max_length=200)
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs', limit_choices_to={'role': 'employer'})
    
    # Location
    location = models.CharField(max_length=200, help_text="City/town and optionally remote/on-site/hybrid")
    is_remote = models.BooleanField(default=False)
    work_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    
    # Job Details
    job_description = models.TextField()
    qualifications = models.TextField(help_text="Academic, technical, or experience requirements")
    skills_required = models.TextField(help_text="Comma-separated list of required skills")
    experience_level = models.CharField(max_length=50, choices=EXPERIENCE_LEVEL_CHOICES, default='entry')
    years_of_experience = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(50)])
    
    # Compensation
    salary_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='KES')
    salary_display = models.CharField(max_length=100, blank=True, help_text="e.g., 'KES 50,000 - 100,000' or 'Competitive'")
    
    # Dates
    date_posted = models.DateTimeField(auto_now_add=True, db_index=True)
    application_deadline = models.DateTimeField(null=True, blank=True)
    
    # Application
    application_link = models.URLField(blank=True, help_text="External application link (optional)")
    application_instructions = models.TextField(blank=True, help_text="How to apply instructions")
    
    # Tracking
    job_id = models.CharField(max_length=50, unique=True, blank=True, db_index=True, help_text="Unique job reference number")
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='jobnix')
    
    # Status and Visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Analytics
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_jobs')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'jobs'
        ordering = ['-date_posted', '-created_at']
        indexes = [
            models.Index(fields=['job_title', 'location']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.job_id:
            # Generate unique job ID
            from django.utils.text import slugify
            import uuid
            base = slugify(f"{self.company_name}-{self.job_title}")[:30]
            self.job_id = f"{base}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if job application deadline has passed"""
        if self.application_deadline:
            return timezone.now() > self.application_deadline
        return False
    
    @property
    def salary_display_text(self):
        """Get formatted salary display"""
        if self.salary_display:
            return self.salary_display
        if self.salary_range_min and self.salary_range_max:
            return f"{self.salary_currency} {self.salary_range_min:,.0f} - {self.salary_range_max:,.0f}"
        return "Salary: Competitive / Negotiable"


class Application(models.Model):
    """Job application model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview Scheduled'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', limit_choices_to={'role': 'youth'})
    
    # Application Details
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Notes
    applicant_notes = models.TextField(blank=True, help_text="Notes from applicant")
    employer_notes = models.TextField(blank=True, help_text="Internal notes from employer")
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # AI Matching Score
    match_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)], help_text="AI-generated match percentage")
    
    class Meta:
        db_table = 'applications'
        ordering = ['-applied_at']
        unique_together = [['job', 'applicant']]
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['applicant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.applicant.username} applied for {self.job.job_title}"


class SavedJob(models.Model):
    """Saved/Bookmarked jobs by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs', limit_choices_to={'role': 'youth'})
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by_users')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_jobs'
        unique_together = [['user', 'job']]
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.job.job_title}"
