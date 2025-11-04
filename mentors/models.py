from django.db import models
from accounts.models import User
from django.utils import timezone


class Mentor(models.Model):
    """Mentor profile for mentorship program"""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_profile', limit_choices_to={'role__in': ['employer', 'institution']})
    bio = models.TextField(help_text="Professional background and expertise")
    expertise_areas = models.TextField(help_text="Comma-separated areas of expertise (e.g., Software Development, Business, Marketing)")
    years_of_experience = models.IntegerField(default=0)
    current_position = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    languages = models.CharField(max_length=200, default='English', help_text="Languages spoken (comma-separated)")
    availability_hours = models.CharField(max_length=200, blank=True, help_text="e.g., Monday-Friday, 9am-5pm")
    max_mentees = models.IntegerField(default=10, help_text="Maximum number of active mentees")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Hourly rate (0 for free mentorship)")
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, help_text="Average rating from mentees")
    total_sessions = models.IntegerField(default=0)
    total_mentees = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mentors'
        ordering = ['-rating', '-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Mentor"


class MentorshipRequest(models.Model):
    """Mentorship requests from youth to mentors"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentorship_requests', limit_choices_to={'role': 'youth'})
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name='mentorship_requests')
    message = models.TextField(help_text="Why do you want mentorship from this mentor?")
    goals = models.TextField(help_text="What are your career goals?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    match_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="AI-calculated compatibility score")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'mentorship_requests'
        unique_together = [['mentee', 'mentor']]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.mentee.username} → {self.mentor.user.username}"


class MentorshipSession(models.Model):
    """Scheduled mentorship sessions"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    mentorship = models.ForeignKey(MentorshipRequest, on_delete=models.CASCADE, related_name='sessions', limit_choices_to={'status': 'accepted'})
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    meeting_link = models.URLField(blank=True, help_text="Zoom/Teams/Google Meet link")
    meeting_type = models.CharField(max_length=50, choices=[('video', 'Video Call'), ('in_person', 'In Person'), ('phone', 'Phone Call')], default='video')
    agenda = models.TextField(blank=True, help_text="Session agenda or topics to discuss")
    notes = models.TextField(blank=True, help_text="Session notes (filled after session)")
    feedback = models.TextField(blank=True, help_text="Mentor feedback")
    rating = models.IntegerField(null=True, blank=True, help_text="Mentee rating (1-5)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mentorship_sessions'
        ordering = ['scheduled_at']
    
    def __str__(self):
        return f"Session: {self.mentorship.mentee.username} with {self.mentorship.mentor.user.username}"


class MentorshipGoal(models.Model):
    """Career goals set by mentees"""
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    mentorship = models.ForeignKey(MentorshipRequest, on_delete=models.CASCADE, related_name='mentorship_goals', limit_choices_to={'status': 'accepted'})
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    progress_percentage = models.IntegerField(default=0, help_text="Progress percentage (0-100)")
    mentor_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'mentorship_goals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Goal: {self.title} - {self.mentorship.mentee.username}"


class MentorshipResource(models.Model):
    """Learning resources shared by mentors"""
    RESOURCE_TYPES = [
        ('document', 'Document'),
        ('link', 'External Link'),
        ('video', 'Video'),
        ('article', 'Article'),
    ]
    
    mentorship = models.ForeignKey(MentorshipRequest, on_delete=models.CASCADE, related_name='resources', limit_choices_to={'status': 'accepted'})
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='link')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True, help_text="Link to resource")
    file = models.FileField(upload_to='mentorship_resources/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mentorship_resources'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Resource: {self.title}"
