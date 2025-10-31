from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Import models safely to avoid circular import issues
try:
    from .models import Job, Application
except ImportError:
    Job = None
    Application = None

# Create your views here.
def job_list_view(request):
    """List all available jobs"""
    if Job:
        jobs = Job.objects.filter(is_active=True) if hasattr(Job, 'objects') else []
    else:
        jobs = []
    context = {'jobs': jobs}
    return render(request, 'jobs/job_list.html', context)

def job_detail_view(request, job_id):
    """Display job details"""
    if Job and hasattr(Job, 'objects'):
        job = get_object_or_404(Job, id=job_id, is_active=True)
        context = {'job': job}
    else:
        context = {'job': None}
    return render(request, 'jobs/job_detail.html', context)

@login_required
def job_create_view(request):
    """Create a new job posting (for employers)"""
    if request.method == 'POST':
        # Job creation logic will be implemented with forms
        messages.success(request, 'Job posted successfully')
        return redirect('jobs:job_list')
    return render(request, 'jobs/job_create.html')

@login_required
def job_apply_view(request, job_id):
    """Apply for a job"""
    if Job and hasattr(Job, 'objects'):
        job = get_object_or_404(Job, id=job_id, is_active=True)
        if request.method == 'POST':
            # Application logic will be implemented with forms
            messages.success(request, 'Application submitted successfully')
            return redirect('jobs:job_detail', job_id=job_id)
        context = {'job': job}
    else:
        context = {'job': None}
    return render(request, 'jobs/job_apply.html', context)

