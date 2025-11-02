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
from education.models import Course, Enrollment, Payment
from django.db.models import Sum, Count, Q

# Create your views here.
@login_required
def admin_dashboard_view(request):
    """Admin dashboard with comprehensive statistics from database - accessible to all logged in users"""
    # Allow any logged in user to access admin dashboard
    # You can add role checking here if needed: if request.user.role != 'admin' and not request.user.is_staff
    
    # Get comprehensive statistics from database
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Earnings tracking - calculate total earnings from paid courses
    total_earnings = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Monthly earnings
    from datetime import timedelta
    this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_earnings = Payment.objects.filter(
        status='completed',
        payment_date__gte=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Free vs Paid courses
    free_courses_count = Course.objects.filter(is_free=True).count()
    paid_courses_count = Course.objects.filter(is_free=False).count()
    
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
        'total_earnings': total_earnings,
        'monthly_earnings': monthly_earnings,
        'free_courses_count': free_courses_count,
        'paid_courses_count': paid_courses_count,
        'total_payments': Payment.objects.filter(status='completed').count(),
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
    """Manage job postings - view all jobs with filters"""
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
                return redirect('admin_panel:job_management')
        except Job.DoesNotExist:
            messages.error(request, 'Job not found')
    
    # Get application counts
    for job in jobs:
        job.applications_count_obj = job.applications.count()
    
    context = {
        'jobs': jobs.order_by('-created_at'),
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/job_management.html', context)


@login_required
def job_add_view(request):
    """Add a new job posting"""
    if request.method == 'POST':
        try:
            # Get or create employer user
            company_email = request.POST.get('company_email')
            company_name = request.POST.get('company_name')
            
            # Try to find existing employer
            employer = None
            if company_email:
                try:
                    employer = User.objects.get(email=company_email, role='employer')
                except User.DoesNotExist:
                    # Create new employer account
                    employer = User.objects.create_user(
                        username=company_email.split('@')[0],
                        email=company_email,
                        role='employer',
                        is_verified=True,
                    )
                    from accounts.models import EmployerProfile
                    EmployerProfile.objects.create(
                        user=employer,
                        company_name=company_name,
                    )
            
            if not employer:
                messages.error(request, 'Employer email is required')
                return redirect('admin_panel:job_add')
            
            job = Job.objects.create(
                job_title=request.POST.get('job_title'),
                company_name=company_name,
                company=employer,
                location=request.POST.get('location', ''),
                is_remote=request.POST.get('is_remote') == 'on',
                work_type=request.POST.get('work_type', 'full_time'),
                job_description=request.POST.get('job_description', ''),
                qualifications=request.POST.get('qualifications', ''),
                skills_required=request.POST.get('skills_required', ''),
                experience_level=request.POST.get('experience_level', 'entry'),
                years_of_experience=int(request.POST.get('years_of_experience', 0) or 0),
                salary_range_min=float(request.POST.get('salary_range_min', 0) or 0) if request.POST.get('salary_range_min') else None,
                salary_range_max=float(request.POST.get('salary_range_max', 0) or 0) if request.POST.get('salary_range_max') else None,
                salary_currency=request.POST.get('salary_currency', 'KES'),
                salary_display=request.POST.get('salary_display', ''),
                application_link=request.POST.get('application_link', ''),
                application_instructions=request.POST.get('application_instructions', ''),
                status=request.POST.get('status', 'pending'),
                is_active=request.POST.get('is_active') == 'on',
                is_featured=request.POST.get('is_featured') == 'on',
            )
            
            # Handle application deadline
            deadline_str = request.POST.get('application_deadline')
            if deadline_str:
                from django.utils.dateparse import parse_datetime
                try:
                    job.application_deadline = parse_datetime(deadline_str)
                except:
                    pass
            
            job.save()
            messages.success(request, f'Job "{job.job_title}" created successfully')
            return redirect('admin_panel:job_edit', job_id=job.id)
        except Exception as e:
            messages.error(request, f'Error creating job: {str(e)}')
    
    employers = User.objects.filter(role='employer')
    context = {
        'employers': employers,
    }
    return render(request, 'admin_panel/job_add.html', context)


@login_required
def job_edit_view(request, job_id):
    """Edit an existing job posting"""
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        try:
            job.job_title = request.POST.get('job_title')
            job.company_name = request.POST.get('company_name')
            job.location = request.POST.get('location', '')
            job.is_remote = request.POST.get('is_remote') == 'on'
            job.work_type = request.POST.get('work_type', 'full_time')
            job.job_description = request.POST.get('job_description', '')
            job.qualifications = request.POST.get('qualifications', '')
            job.skills_required = request.POST.get('skills_required', '')
            job.experience_level = request.POST.get('experience_level', 'entry')
            job.years_of_experience = int(request.POST.get('years_of_experience', 0) or 0)
            job.salary_range_min = float(request.POST.get('salary_range_min', 0) or 0) if request.POST.get('salary_range_min') else None
            job.salary_range_max = float(request.POST.get('salary_range_max', 0) or 0) if request.POST.get('salary_range_max') else None
            job.salary_currency = request.POST.get('salary_currency', 'KES')
            job.salary_display = request.POST.get('salary_display', '')
            job.application_link = request.POST.get('application_link', '')
            job.application_instructions = request.POST.get('application_instructions', '')
            job.status = request.POST.get('status', 'pending')
            job.is_active = request.POST.get('is_active') == 'on'
            job.is_featured = request.POST.get('is_featured') == 'on'
            
            # Handle application deadline
            deadline_str = request.POST.get('application_deadline')
            if deadline_str:
                from django.utils.dateparse import parse_datetime
                try:
                    job.application_deadline = parse_datetime(deadline_str)
                except:
                    job.application_deadline = None
            else:
                job.application_deadline = None
            
            job.save()
            messages.success(request, f'Job "{job.job_title}" updated successfully')
            return redirect('admin_panel:job_management')
        except Exception as e:
            messages.error(request, f'Error updating job: {str(e)}')
    
    # Get application stats
    job.applications_count_obj = job.applications.count()
    
    employers = User.objects.filter(role='employer')
    context = {
        'job': job,
        'employers': employers,
    }
    return render(request, 'admin_panel/job_edit.html', context)


@login_required
def job_delete_view(request, job_id):
    """Delete a job posting"""
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        job_title = job.job_title
        job.delete()
        messages.success(request, f'Job "{job_title}" deleted successfully')
        return redirect('admin_panel:job_management')
    
    context = {
        'job': job,
    }
    return render(request, 'admin_panel/job_delete.html', context)


@login_required
def course_management_view(request):
    """Manage courses - view all courses with filters"""
    courses = Course.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        courses = courses.filter(status=status_filter)
    
    # Filter by pricing
    pricing_filter = request.GET.get('pricing')
    if pricing_filter == 'free':
        courses = courses.filter(is_free=True)
    elif pricing_filter == 'paid':
        courses = courses.filter(is_free=False, price__gt=0)
    
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
                return redirect('admin_panel:course_management')
        except Course.DoesNotExist:
            messages.error(request, 'Course not found')
    
    # Get earnings per course
    for course in courses:
        course.total_earnings = Payment.objects.filter(
            course=course,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        course.enrollments_count_obj = course.enrollments.count()
    
    context = {
        'courses': courses.order_by('-created_at'),
        'status_filter': status_filter,
        'pricing_filter': pricing_filter,
    }
    return render(request, 'admin_panel/course_management.html', context)


@login_required
def course_add_view(request):
    """Add a new course"""
    from education.models import CourseModule, CourseContent
    
    if request.method == 'POST':
        try:
            course = Course.objects.create(
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                category=request.POST.get('category', ''),
                skills_taught=request.POST.get('skills_taught', ''),
                level=request.POST.get('level', 'beginner'),
                duration_hours=int(request.POST.get('duration_hours', 0) or 0),
                price=float(request.POST.get('price', 0) or 0),
                is_free=request.POST.get('is_free') == 'on',
                status=request.POST.get('status', 'pending'),
                is_active=request.POST.get('is_active') == 'on',
            )
            
            # Handle instructor assignment if provided
            instructor_id = request.POST.get('instructor')
            if instructor_id:
                try:
                    instructor = User.objects.get(id=instructor_id, role__in=['institution', 'employer'])
                    course.instructor = instructor
                except User.DoesNotExist:
                    pass
            
            course.save()
            
            # Handle course content creation (modules and contents)
            # Process all modules/sections
            i = 0
            while True:
                module_title = request.POST.get(f'module_title_{i}')
                if not module_title:
                    break
                
                # Check if section has video (required)
                section_video_url = request.POST.get(f'section_video_url_{i}', '').strip()
                section_video_file = request.FILES.get(f'section_video_file_{i}')
                section_video_title = request.POST.get(f'section_video_title_{i}', '').strip()
                
                if not section_video_url and not section_video_file:
                    i += 1
                    continue  # Skip sections without videos
                
                # Create module (section)
                module = CourseModule.objects.create(
                    course=course,
                    title=module_title,
                    description=request.POST.get(f'module_description_{i}', ''),
                    order=int(request.POST.get(f'module_order_{i}', i) or i)
                )
                
                # Create video content for this section (primary video)
                if section_video_title or section_video_url or section_video_file:
                    video_content = CourseContent.objects.create(
                        course=course,
                        module=module,
                        content_type='video',
                        title=section_video_title or f"{module_title} - Video",
                        description=request.POST.get(f'section_video_description_{i}', ''),
                        order=0  # Video is always first in section
                    )
                    
                    if section_video_url:
                        video_content.video_url = section_video_url
                    if section_video_file:
                        video_content.video_file = section_video_file
                    
                    video_content.video_duration = request.POST.get(f'section_video_duration_{i}', '')
                    video_content.is_free_preview = False  # Main video is not free preview
                    video_content.save()
                
                # Process subsection content items for this module (documents, links, text, etc.)
                j = 0
                subsection_order = 1  # Start after video (order 0)
                while True:
                    content_module_index = request.POST.get(f'content_module_index_{j}')
                    if content_module_index is None:
                        break
                    
                    # Check if this content belongs to current module
                    if int(content_module_index) == i:
                        content_type = request.POST.get(f'content_type_{j}')
                        content_title = request.POST.get(f'content_title_{j}')
                        
                        if content_type and content_title:
                            content = CourseContent.objects.create(
                                course=course,
                                module=module,
                                content_type=content_type,
                                title=content_title,
                                description=request.POST.get(f'content_description_{j}', ''),
                                order=subsection_order  # Subsections come after video
                            )
                            
                            # Handle different content types
                            if content_type == 'document':
                                content.document_url = request.POST.get(f'document_url_{j}', '')
                                if f'document_file_{j}' in request.FILES:
                                    content.document_file = request.FILES[f'document_file_{j}']
                            elif content_type == 'link':
                                content.external_link = request.POST.get(f'external_link_{j}', '')
                                content.link_title = request.POST.get(f'link_title_{j}', '')
                            elif content_type == 'text':
                                content.text_content = request.POST.get(f'text_content_{j}', '')
                            elif content_type == 'quiz':
                                content.text_content = request.POST.get(f'text_content_{j}', '')  # Quiz stored in text_content for now
                            elif content_type == 'assignment':
                                content.text_content = request.POST.get(f'text_content_{j}', '')  # Assignment stored in text_content for now
                            
                            content.is_free_preview = request.POST.get(f'is_free_preview_{j}') == 'on'
                            content.save()
                            subsection_order += 1
                    
                    j += 1
                
                i += 1
            
            messages.success(request, f'Course "{course.title}" created successfully')
            return redirect('admin_panel:course_edit', course_id=course.id)
        except Exception as e:
            messages.error(request, f'Error creating course: {str(e)}')
    
    instructors = User.objects.filter(role__in=['institution', 'employer'])
    context = {
        'instructors': instructors,
    }
    return render(request, 'admin_panel/course_add.html', context)


@login_required
def course_edit_view(request, course_id):
    """Edit an existing course"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        try:
            course.title = request.POST.get('title')
            course.description = request.POST.get('description')
            course.category = request.POST.get('category', '')
            course.skills_taught = request.POST.get('skills_taught', '')
            course.level = request.POST.get('level', 'beginner')
            course.duration_hours = int(request.POST.get('duration_hours', 0) or 0)
            course.price = float(request.POST.get('price', 0) or 0)
            course.is_free = request.POST.get('is_free') == 'on'
            course.status = request.POST.get('status', 'pending')
            course.is_active = request.POST.get('is_active') == 'on'
            
            # Handle instructor assignment
            instructor_id = request.POST.get('instructor')
            if instructor_id:
                try:
                    instructor = User.objects.get(id=instructor_id, role__in=['institution', 'employer'])
                    course.instructor = instructor
                except User.DoesNotExist:
                    course.instructor = None
            else:
                course.instructor = None
            
            course.save()
            messages.success(request, f'Course "{course.title}" updated successfully')
            return redirect('admin_panel:course_management')
        except Exception as e:
            messages.error(request, f'Error updating course: {str(e)}')
    
    instructors = User.objects.filter(role__in=['institution', 'employer'])
    
    # Get earnings and enrollment stats
    course.total_earnings = Payment.objects.filter(
        course=course,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    course.enrollments_count_obj = course.enrollments.count()
    
    context = {
        'course': course,
        'instructors': instructors,
    }
    return render(request, 'admin_panel/course_edit.html', context)


@login_required
def course_delete_view(request, course_id):
    """Delete a course"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Course "{course_title}" deleted successfully')
        return redirect('admin_panel:course_management')
    
    context = {
        'course': course,
    }
    return render(request, 'admin_panel/course_delete.html', context)


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


@login_required
def instructor_management_view(request):
    """Manage instructors"""
    instructors = User.objects.filter(role__in=['institution', 'employer'])
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        instructors = instructors.filter(role=role_filter)
    
    # Search filter
    search = request.GET.get('search')
    if search:
        instructors = instructors.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    context = {
        'instructors': instructors.order_by('-created_at'),
        'role_filter': role_filter,
        'search': search,
    }
    return render(request, 'admin_panel/instructor_management.html', context)


@login_required
def instructor_add_view(request):
    """Add a new instructor"""
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role', 'institution')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            
            # Create user
            instructor = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name,
                is_verified=True,
                is_active=True
            )
            
            # Create profile based on role
            if role == 'employer':
                from accounts.models import EmployerProfile
                EmployerProfile.objects.create(
                    user=instructor,
                    company_name=request.POST.get('company_name', ''),
                    location=request.POST.get('location', ''),
                    contact_email=email,
                    contact_phone=request.POST.get('phone', ''),
                )
            elif role == 'institution':
                from accounts.models import InstitutionProfile
                InstitutionProfile.objects.create(
                    user=instructor,
                    institution_name=request.POST.get('institution_name', ''),
                    location=request.POST.get('location', ''),
                    contact_email=email,
                    contact_phone=request.POST.get('phone', ''),
                )
            
            messages.success(request, f'Instructor "{instructor.username}" created successfully')
            return redirect('admin_panel:instructor_management')
        except Exception as e:
            messages.error(request, f'Error creating instructor: {str(e)}')
    
    return render(request, 'admin_panel/instructor_add.html')


@login_required
def instructor_edit_view(request, instructor_id):
    """Edit an instructor"""
    instructor = get_object_or_404(User, id=instructor_id, role__in=['institution', 'employer'])
    
    if request.method == 'POST':
        try:
            instructor.username = request.POST.get('username')
            instructor.email = request.POST.get('email')
            instructor.first_name = request.POST.get('first_name', '')
            instructor.last_name = request.POST.get('last_name', '')
            
            # Update password if provided
            new_password = request.POST.get('password')
            if new_password:
                instructor.set_password(new_password)
            
            instructor.is_active = request.POST.get('is_active') == 'on'
            instructor.save()
            
            # Update profile
            if instructor.role == 'employer' and hasattr(instructor, 'employer_profile'):
                profile = instructor.employer_profile
                profile.company_name = request.POST.get('company_name', '')
                profile.location = request.POST.get('location', '')
                profile.contact_email = request.POST.get('email', '')
                profile.contact_phone = request.POST.get('phone', '')
                profile.save()
            elif instructor.role == 'institution' and hasattr(instructor, 'institution_profile'):
                profile = instructor.institution_profile
                profile.institution_name = request.POST.get('institution_name', '')
                profile.location = request.POST.get('location', '')
                profile.contact_email = request.POST.get('email', '')
                profile.contact_phone = request.POST.get('phone', '')
                profile.save()
            
            messages.success(request, f'Instructor "{instructor.username}" updated successfully')
            return redirect('admin_panel:instructor_management')
        except Exception as e:
            messages.error(request, f'Error updating instructor: {str(e)}')
    
    context = {
        'instructor': instructor,
    }
    return render(request, 'admin_panel/instructor_edit.html', context)
