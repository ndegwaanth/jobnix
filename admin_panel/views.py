from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
import csv

# Import models
from accounts.models import User, Notification as UserNotification, SupportTicket
from jobs.models import Job, Application
from education.models import Course, Enrollment

# Create your views here.
@login_required
def admin_dashboard_view(request):
    """Admin dashboard with comprehensive statistics from database - accessible to all logged in users"""
    # Allow any logged in user to access admin dashboard
    # You can add role checking here if needed: if request.user.role != 'admin' and not request.user.is_staff
    
    # Get comprehensive statistics from database
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    stats = {
        'total_users': total_users,
        'verified_users': verified_users,
        'youth_users': User.objects.filter(role='youth').count(),
        'employer_users': User.objects.filter(role='employer').count(),
        'institution_users': User.objects.filter(role='institution').count(),
        'pending_verifications': total_users - verified_users,
        'total_jobs': Job.objects.count(),
        'active_jobs': Job.objects.filter(status='active', is_active=True).count(),
        'pending_jobs': Job.objects.filter(status='pending').count(),
        'total_applications': Application.objects.count(),
        'total_courses': Course.objects.count(),
        'pending_courses': Course.objects.filter(status='pending').count(),
        'total_enrollments': Enrollment.objects.count(),
        'open_tickets': SupportTicket.objects.filter(status__in=['open', 'in_progress']).count(),
    }
    
    # Recent activity
    recent_jobs = Job.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-created_at')[:5]
    
    # Analytics data
    from accounts.utils import get_skill_demand_analysis, get_regional_employment_insights
    top_skills = get_skill_demand_analysis()[:10]
    top_locations = get_regional_employment_insights()[:10]
    
    context = {
        'stats': stats,
        'user': request.user,
        'recent_jobs': recent_jobs,
        'recent_users': recent_users,
        'top_skills': top_skills,
        'top_locations': top_locations,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
def user_management_view(request):
    """Manage users - approve, deactivate, assign roles"""
    if not (request.user.is_staff or request.user.role == 'admin'):
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    users = User.objects.all()
    
    # Filtering
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Actions
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        try:
            target_user = User.objects.get(id=user_id)
            
            if action == 'approve':
                target_user.is_active = True
                target_user.is_verified = True
                target_user.save()
                messages.success(request, f'User {target_user.username} approved')
            elif action == 'deactivate':
                target_user.is_active = False
                target_user.save()
                messages.success(request, f'User {target_user.username} deactivated')
            elif action == 'change_role':
                new_role = request.POST.get('new_role')
                target_user.role = new_role
                target_user.save()
                messages.success(request, f'Role changed to {new_role}')
            elif action == 'delete':
                target_user.delete()
                messages.success(request, f'User {target_user.username} deleted')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
    
    context = {
        'users': users.order_by('-created_at'),
        'role_filter': role_filter,
    }
    return render(request, 'admin_panel/user_management.html', context)


@login_required
def job_management_view(request):
    """Manage job postings - approve, reject"""
    if not (request.user.is_staff or request.user.role == 'admin'):
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    jobs = Job.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    # Actions
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        action = request.POST.get('action')
        try:
            job = Job.objects.get(id=job_id)
            
            if action == 'approve':
                job.status = 'active'
                job.approved_by = request.user
                job.approved_at = timezone.now()
                job.save()
                messages.success(request, 'Job approved')
            elif action == 'reject':
                job.status = 'closed'
                job.save()
                messages.success(request, 'Job rejected')
            elif action == 'delete':
                job.delete()
                messages.success(request, 'Job deleted')
        except Job.DoesNotExist:
            messages.error(request, 'Job not found')
    
    context = {
        'jobs': jobs.order_by('-created_at'),
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/job_management.html', context)


@login_required
def course_management_view(request):
    """Manage courses - approve, reject"""
    if not (request.user.is_staff or request.user.role == 'admin'):
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    courses = Course.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        courses = courses.filter(status=status_filter)
    
    # Actions
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        action = request.POST.get('action')
        try:
            course = Course.objects.get(id=course_id)
            
            if action == 'approve':
                course.status = 'active'
                course.approved_by = request.user
                course.approved_at = timezone.now()
                course.save()
                messages.success(request, 'Course approved')
            elif action == 'reject':
                course.status = 'archived'
                course.save()
                messages.success(request, 'Course rejected')
            elif action == 'delete':
                course.delete()
                messages.success(request, 'Course deleted')
        except Course.DoesNotExist:
            messages.error(request, 'Course not found')
    
    context = {
        'courses': courses.order_by('-created_at'),
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/course_management.html', context)


@login_required
def analytics_view(request):
    """Comprehensive analytics dashboard"""
    if not (request.user.is_staff or request.user.role == 'admin'):
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from accounts.utils import get_skill_demand_analysis, get_regional_employment_insights
    
    # Time-based analytics
    last_30_days = timezone.now() - timedelta(days=30)
    last_7_days = timezone.now() - timedelta(days=7)
    
    # User analytics
    user_stats = {
        'total': User.objects.count(),
        'new_30_days': User.objects.filter(created_at__gte=last_30_days).count(),
        'new_7_days': User.objects.filter(created_at__gte=last_7_days).count(),
        'verified': User.objects.filter(is_verified=True).count(),
        'by_role': {
            'youth': User.objects.filter(role='youth').count(),
            'employer': User.objects.filter(role='employer').count(),
            'institution': User.objects.filter(role='institution').count(),
        }
    }
    
    # Job analytics
    job_stats = {
        'total': Job.objects.count(),
        'active': Job.objects.filter(status='active', is_active=True).count(),
        'pending': Job.objects.filter(status='pending').count(),
        'new_30_days': Job.objects.filter(created_at__gte=last_30_days).count(),
    }
    
    # Application analytics
    app_stats = {
        'total': Application.objects.count(),
        'new_30_days': Application.objects.filter(applied_at__gte=last_30_days).count(),
        'by_status': {
            'pending': Application.objects.filter(status='pending').count(),
            'accepted': Application.objects.filter(status='accepted').count(),
            'rejected': Application.objects.filter(status='rejected').count(),
        }
    }
    
    # Skill and location analysis
    top_skills = get_skill_demand_analysis()
    top_locations = get_regional_employment_insights()
    
    context = {
        'user_stats': user_stats,
        'job_stats': job_stats,
        'app_stats': app_stats,
        'top_skills': top_skills,
        'top_locations': top_locations,
    }
    
    # Export reports
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="platform_analytics.csv"'
        writer = csv.writer(response)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Users', user_stats['total']])
        writer.writerow(['Total Jobs', job_stats['total']])
        writer.writerow(['Total Applications', app_stats['total']])
        return response
    
    return render(request, 'admin_panel/analytics.html', context)


@login_required
def support_tickets_view(request):
    """Manage support tickets"""
    if not (request.user.is_staff or request.user.role == 'admin'):
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    tickets = SupportTicket.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    # Actions
    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        action = request.POST.get('action')
        try:
            ticket = SupportTicket.objects.get(id=ticket_id)
            
            if action == 'assign':
                ticket.assigned_to = request.user
                ticket.status = 'in_progress'
                ticket.save()
                messages.success(request, 'Ticket assigned to you')
            elif action == 'resolve':
                ticket.status = 'resolved'
                ticket.resolution_notes = request.POST.get('resolution_notes', '')
                ticket.resolved_at = timezone.now()
                ticket.save()
                messages.success(request, 'Ticket resolved')
            elif action == 'close':
                ticket.status = 'closed'
                ticket.save()
                messages.success(request, 'Ticket closed')
        except SupportTicket.DoesNotExist:
            messages.error(request, 'Ticket not found')
    
    context = {
        'tickets': tickets.order_by('-created_at'),
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/support_tickets.html', context)


@login_required
def system_notifications_view(request):
    """Send system-wide notifications"""
    if not (request.user.is_staff or request.user.role == 'admin'):
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        notification_type = request.POST.get('notification_type', 'system')
        target_role = request.POST.get('target_role', 'all')
        
        if title and message:
            # Send to all users or specific role
            if target_role == 'all':
                recipients = User.objects.filter(is_active=True)
            else:
                recipients = User.objects.filter(role=target_role, is_active=True)
            
            notifications_created = 0
            for user in recipients:
                UserNotification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                )
                notifications_created += 1
            
            messages.success(request, f'Notification sent to {notifications_created} users')
            return redirect('admin_panel:system_notifications')
    
    return render(request, 'admin_panel/system_notifications.html')
