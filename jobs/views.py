from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import Job, Application, SavedJob

def job_create_view(request):
    """Create a new job posting"""
    if not request.user.is_authenticated or not hasattr(request.user, 'employerprofile'):
        messages.error(request, 'You must be logged in as an employer to post a job')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        job_title = request.POST.get('job_title')
        company_name = request.POST.get('company_name')
        location = request.POST.get('location')
        description = request.POST.get('description')
        skills_required = request.POST.get('skills_required')
        experience_level = request.POST.get('experience_level')
        work_type = request.POST.get('work_type')
        salary_range = request.POST.get('salary_range')
        
        Job.objects.create(
            employer=request.user.employerprofile,
            job_title=job_title,
            company_name=company_name,
            location=location,
            description=description,
            skills_required=skills_required,
            experience_level=experience_level,
            work_type=work_type,
            salary_range=salary_range,
            status='active',
            is_active=True
        )
        
        messages.success(request, 'Job posted successfully!')
        return redirect('jobs:job_list')
    
    return render(request, 'jobs/job_create.html')


def job_list_view(request):
    """List all available jobs"""
    jobs = Job.objects.filter(status='active', is_active=True).order_by('-date_posted')
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(job_title__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(skills_required__icontains=search_query)
        )
    
    # Work type filter
    work_type = request.GET.get('work_type', '')
    if work_type:
        jobs = jobs.filter(work_type=work_type)
    
    # Location filter
    location = request.GET.get('location', '')
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    # Experience level filter
    experience = request.GET.get('experience', '')
    if experience:
        jobs = jobs.filter(experience_level=experience)
    
    # Get saved job IDs for logged in users
    saved_job_ids = []
    if request.user.is_authenticated:
        saved_job_ids = SavedJob.objects.filter(user=request.user).values_list('job_id', flat=True)
    
    context = {
        'jobs': jobs,
        'saved_job_ids': saved_job_ids,
        'search_query': search_query,
        'selected_work_type': work_type,
        'selected_location': location,
        'selected_experience': experience,
        'work_types': Job.EMPLOYMENT_TYPE_CHOICES,
        'experience_levels': Job.EXPERIENCE_LEVEL_CHOICES,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail_view(request, job_id):
    """Display job details"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Check if user has applied
    has_applied = False
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(applicant=request.user, job=job).exists()
    
    # Check if saved
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'is_saved': is_saved,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def job_apply_view(request, job_id):
    """Apply for a job"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Check if already applied
    if Application.objects.filter(applicant=request.user, job=job).exists():
        messages.info(request, 'You have already applied for this job')
        return redirect('jobs:job_detail', job_id=job_id)
    
    if request.method == 'POST':
        # Create application
        Application.objects.create(
            applicant=request.user,
            job=job,
            status='pending'
        )
        messages.success(request, 'Application submitted successfully!')
        
        # Create notification
        from accounts.models import Notification
        Notification.objects.create(
            user=request.user,
            notification_type='job_application',
            title='Application Submitted',
            message=f'Your application for {job.job_title} has been submitted',
            link=f'/accounts/applications/'
        )
        
        # Update job application count
        job.applications_count += 1
        job.save(update_fields=['applications_count'])
        
        return redirect('jobs:job_detail', job_id=job_id)
    
    context = {'job': job}
    return render(request, 'jobs/job_apply.html', context)


@login_required
def save_job_view(request, job_id):
    """Save/unsave a job"""
    from django.http import JsonResponse
    
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        saved_job, created = SavedJob.objects.get_or_create(
            user=request.user,
            job=job
        )
        
        if not created:
            saved_job.delete()
            return JsonResponse({'saved': False, 'message': 'Job removed from saved'})
        else:
            return JsonResponse({'saved': True, 'message': 'Job saved'})
    
    return redirect('jobs:job_detail', job_id=job_id)

