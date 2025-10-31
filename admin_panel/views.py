from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q

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
@staff_member_required
def admin_dashboard_view(request):
    """Admin dashboard with overview statistics"""
    from accounts.models import User, EmailVerification
    
    stats = {
        'total_users': User.objects.count() if User else 0,
        'verified_users': User.objects.filter(is_verified=True).count() if User else 0,
        'total_jobs': Job.objects.count() if Job else 0,
        'total_applications': Application.objects.count() if Application else 0,
        'total_courses': Course.objects.count() if Course else 0,
        'total_enrollments': Enrollment.objects.count() if Enrollment else 0,
        'youth_users': User.objects.filter(role='youth').count() if User else 0,
        'employer_users': User.objects.filter(role='employer').count() if User else 0,
        'pending_verifications': EmailVerification.objects.filter(is_verified=False).count() if hasattr(EmailVerification, 'objects') else 0,
    }
    context = {
        'stats': stats,
        'user': request.user
    }
    return render(request, 'admin_panel/dashboard.html', context)

@staff_member_required
def user_management_view(request):
    """Manage users"""
    users = User.objects.all() if User else []
    context = {'users': users}
    return render(request, 'admin_panel/user_management.html', context)

@staff_member_required
def job_management_view(request):
    """Manage job postings"""
    jobs = Job.objects.all() if Job else []
    context = {'jobs': jobs}
    return render(request, 'admin_panel/job_management.html', context)

@staff_member_required
def analytics_view(request):
    """View analytics and reports"""
    # Analytics logic will be implemented with models
    context = {}
    return render(request, 'admin_panel/analytics.html', context)
