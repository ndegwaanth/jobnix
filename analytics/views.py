from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta

# Note: Import models only if they exist to avoid circular import issues
try:
    from accounts.models import User
except ImportError:
    User = None

try:
    from jobs.models import Job, Application
except ImportError:
    Job = None
    Application = None

try:
    from education.models import Course, Enrollment
except ImportError:
    Course = None
    Enrollment = None

# Create your views here.
@login_required
def user_analytics_view(request):
    """User-specific analytics"""
    # User analytics logic will be implemented with models
    user_applications = Application.objects.filter(user=request.user) if Application else []
    user_enrollments = Enrollment.objects.filter(user=request.user) if Enrollment else []
    
    context = {
        'total_applications': len(user_applications) if Application else 0,
        'total_enrollments': len(user_enrollments) if Enrollment else 0,
    }
    return render(request, 'analytics/user_analytics.html', context)

@staff_member_required
def platform_analytics_view(request):
    """Platform-wide analytics (admin only)"""
    # Analytics logic will be implemented with models
    context = {
        'total_users': User.objects.count() if User else 0,
        'total_jobs': Job.objects.count() if Job else 0,
        'total_applications': Application.objects.count() if Application else 0,
        'placement_rate': 0,
    }
    return render(request, 'analytics/platform_analytics.html', context)

@login_required
def job_seeker_stats_view(request):
    """Statistics for job seekers"""
    # Stats logic will be implemented with models
    applications = Application.objects.filter(user=request.user) if Application else []
    
    context = {
        'total_applications': len(applications),
        'pending_applications': len([a for a in applications if hasattr(a, 'status') and a.status == 'pending']) if applications else 0,
    }
    return render(request, 'analytics/job_seeker_stats.html', context)
