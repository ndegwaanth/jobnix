from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Course(models.Model):
    """Training course model"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    institution = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses', limit_choices_to={'role': 'institution'}, null=True, blank=True)
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='instructor_courses')
    
    # Course Details
    category = models.CharField(max_length=100, blank=True)
    skills_taught = models.TextField(help_text="Comma-separated list of skills")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration_hours = models.PositiveIntegerField(default=0, help_text="Course duration in hours")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=True)
    
    # Media
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    video_intro_url = models.URLField(blank=True, help_text="Intro video URL")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    
    # Analytics
    enrollments_count = models.PositiveIntegerField(default=0)
    completion_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    
    # Dates
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_courses')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Enrollment(models.Model):
    """Course enrollment model"""
    
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments', limit_choices_to={'role': 'youth'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # Payment tracking
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    
    # Progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    progress_percentage = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'enrollments'
        unique_together = [['user', 'course']]
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"


class Payment(models.Model):
    """Payment/Transaction model for paid courses"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', limit_choices_to={'role': 'youth'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='mpesa')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, db_index=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    payment_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.user.username} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"TXN-{str(uuid.uuid4())[:12].upper()}"
        super().save(*args, **kwargs)


class Certificate(models.Model):
    """Course completion certificate"""
    
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    
    certificate_number = models.CharField(max_length=50, unique=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    
    class Meta:
        db_table = 'certificates'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Certificate for {self.user.username} - {self.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            import uuid
            self.certificate_number = f"CERT-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class SavedCourse(models.Model):
    """Saved/bookmarked courses by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_courses', limit_choices_to={'role': 'youth'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='saved_by_users')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_courses'
        unique_together = [['user', 'course']]
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.course.title}"


class CourseModule(models.Model):
    """Course module/section containing lessons"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'course_modules'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseContent(models.Model):
    """Course content items: videos, documents, links, etc."""
    
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('document', 'Document'),
        ('link', 'External Link'),
        ('text', 'Text Content'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]
    
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='contents', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contents', null=True, blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='video')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Video content
    video_url = models.URLField(blank=True, help_text="YouTube, Vimeo, or other video URL")
    video_file = models.FileField(upload_to='course_videos/', blank=True, null=True, help_text="Upload video file")
    video_duration = models.CharField(max_length=20, blank=True, help_text="e.g., '10:30'")
    
    # Document content
    document_file = models.FileField(upload_to='course_documents/', blank=True, null=True, help_text="PDF, DOC, etc.")
    document_url = models.URLField(blank=True, help_text="External document link")
    
    # Link content
    external_link = models.URLField(blank=True, help_text="External resource link")
    link_title = models.CharField(max_length=200, blank=True)
    
    # Text content
    text_content = models.TextField(blank=True, help_text="Text/HTML content")
    
    # Metadata
    order = models.PositiveIntegerField(default=0)
    is_free_preview = models.BooleanField(default=False, help_text="Available without enrollment")
    duration_minutes = models.PositiveIntegerField(default=0, help_text="Content duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_contents'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"
    
    def get_display_url(self):
        """Get the primary URL for the content"""
        if self.content_type == 'video':
            return self.video_url or (self.video_file.url if self.video_file else '')
        elif self.content_type == 'document':
            return self.document_url or (self.document_file.url if self.document_file else '')
        elif self.content_type == 'link':
            return self.external_link
        return ''
