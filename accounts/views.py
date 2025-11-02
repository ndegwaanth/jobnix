from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.db import models
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from .models import User, EmailVerification, JobSeekerProfile, EmployerProfile, InstitutionProfile, Notification
from .utils import send_verification_email, verify_email_code


# Create your views here.
def landing_view(request):
    """Landing page view"""
    return render(request, 'landing.html')


def login_view(request):
    """User login view - supports username/email login for all roles"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        role = request.POST.get('role', 'youth')  # Role selection for UI, but we'll detect actual role from DB
        
        if not username_or_email or not password:
            messages.error(request, 'Please provide both username/email and password')
            return render(request, 'accounts/login.html')
        
        # Try to authenticate - Django's authenticate works with username
        # First try as username
        user = authenticate(request, username=username_or_email, password=password)
        
        # If that fails, try to find user by email and authenticate
        if not user:
            try:
                # Fetch user from database by email
                user_by_email = User.objects.filter(email=username_or_email).first()
                if user_by_email:
                    # Try authentication with the username from database
                    user = authenticate(request, username=user_by_email.username, password=password)
            except Exception as e:
                pass
        
        if user:
            # Fetch user details from database to verify account status
            try:
                # Ensure we have the latest user data from database
                user = User.objects.get(id=user.id)
            except User.DoesNotExist:
                messages.error(request, 'User account not found in database.')
                return render(request, 'accounts/login.html')
            
            # Check if user is active
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
                return render(request, 'accounts/login.html')
            
            # For admin users, skip role matching (they can login regardless of role tab selected)
            # For youth and employer, check if role matches (but be flexible)
            if user.role == 'admin' or user.is_staff or user.is_superuser:
                # Admin can login regardless of role tab selected
                pass
            elif user.role != role and role in ['youth', 'employer']:
                # Suggest the correct role but allow login
                messages.info(request, f'You are logging in as {user.get_role_display()}. If this is incorrect, please select the correct role tab.')
            
            # Check if email is verified
            if not user.is_verified:
                from django.conf import settings
                # Check if we're in development mode - allow login with warning
                is_dev_mode = settings.DEBUG and settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'
                
                # Admin and staff users can always login without verification
                if user.role == 'admin' or user.is_staff or user.is_superuser:
                    login(request, user)
                    messages.success(request, 'Login successful!')
                elif is_dev_mode:
                    # In development mode, allow login but show warning
                    login(request, user)
                    messages.warning(request, 'You are logged in but your email is not verified. Please verify your email when possible.')
                else:
                    # In production, require verification
                    messages.warning(request, 'Please verify your email before logging in. A verification code will be sent to your email.')
                    verification = send_verification_email(user, user.email)
                    # Get verification code to show in dev mode
                    verification_obj = EmailVerification.objects.filter(
                        user=user,
                        email=user.email,
                        is_verified=False
                    ).first()
                    if verification_obj and settings.DEBUG:
                        messages.info(request, f'Verification code: {verification_obj.code} (Check your email or console)')
                    return redirect('accounts:verify_email', user_id=user.id)
            else:
                login(request, user)
                messages.success(request, 'Login successful!')
            
            # Redirect based on role fetched from database
            if user.role == 'admin' or user.is_staff or user.is_superuser:
                return redirect('admin_panel:dashboard')
            elif user.role == 'youth':
                return redirect('accounts:dashboard')
            elif user.role == 'employer':
                return redirect('accounts:dashboard')
            elif user.role == 'institution':
                return redirect('accounts:dashboard')
            else:
                return redirect('accounts:dashboard')
        else:
            # Authentication failed - check if user exists in database
            user_exists = User.objects.filter(
                Q(username=username_or_email) | Q(email=username_or_email)
            ).exists()
            
            if user_exists:
                messages.error(request, 'Invalid password. Please check your password and try again.')
            else:
                messages.error(request, 'Invalid username or email. No account found with these credentials.')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('landing')


def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                phone = request.POST.get('phone')
                role = request.POST.get('role', 'youth')
                
                # Validate passwords match
                if password != confirm_password:
                    messages.error(request, 'Passwords do not match')
                    return render(request, 'accounts/signup.html')
                
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Username already exists')
                    return render(request, 'accounts/signup.html')
                
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'Email already registered')
                    return render(request, 'accounts/signup.html')
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role=role,
                    is_verified=False
                )
                
                # Create profile based on role
                if role == 'youth':
                    JobSeekerProfile.objects.create(
                        user=user,
                        education_level=request.POST.get('education_level', ''),
                        skills=request.POST.get('skills', ''),
                        interests=request.POST.get('interests', '')
                    )
                elif role == 'employer':
                    EmployerProfile.objects.create(
                        user=user,
                        company_name=request.POST.get('company_name', ''),
                        company_website=request.POST.get('company_website', ''),
                        industry=request.POST.get('industry', ''),
                        company_size=request.POST.get('company_size', '')
                    )
                elif role == 'institution':
                    InstitutionProfile.objects.create(
                        user=user,
                        institution_name=request.POST.get('company_name', 'Company Name'),
                        institution_type=request.POST.get('industry', ''),
                        website=request.POST.get('company_website', '')
                    )
                
                # Send verification email
                verification = send_verification_email(user, email)
                
                # Always get the verification object (even if email failed, code was still generated)
                if not verification:
                    verification = EmailVerification.objects.filter(
                        user=user,
                        email=email,
                        is_verified=False
                    ).order_by('-created_at').first()
                
                # Check if using console backend (development mode)
                from django.conf import settings
                is_dev_mode = settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'
                is_debug = settings.DEBUG
                
                if verification:
                    # Store code in message if in dev/debug mode
                    if is_dev_mode or is_debug:
                        messages.info(request, f'Registration successful! Verification code: {verification.code} (Check console/terminal or verification page)')
                    else:
                        messages.success(request, 'Registration successful! Please check your email for verification code.')
                    # Redirect to email sent confirmation page
                    return redirect('accounts:email_sent', user_id=user.id)
                else:
                    # This should not happen, but handle it gracefully
                    messages.warning(request, 'Registration successful but verification code could not be generated. Please contact support.')
                    return redirect('accounts:verify_email', user_id=user.id)
                    
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    # Get role from query parameter if present
    context = {
        'role': request.GET.get('role', '')
    }
    return render(request, 'accounts/signup.html', context)


def email_sent_view(request, user_id):
    """Email sent confirmation page"""
    try:
        user = User.objects.get(id=user_id)
        context = {
            'user': user,
            'email': user.email
        }
        return render(request, 'accounts/email_sent.html', context)
    except User.DoesNotExist:
        messages.error(request, 'Invalid user')
        return redirect('accounts:register')


def verify_email_view(request, user_id):
    """Email verification view"""
    try:
        user = User.objects.get(id=user_id)
        
        if request.method == 'POST':
            code = request.POST.get('code', '').strip()
            
            if not code:
                messages.error(request, 'Please enter verification code')
                context = {
                    'user': user,
                    'email': user.email,
                    'has_code': True
                }
                return render(request, 'accounts/verify_email.html', context)
            
            success, message = verify_email_code(user, user.email, code)
            
            if success:
                # Auto login after verification
                login(request, user)
                messages.success(request, message)
                return redirect('accounts:verification_success', user_id=user.id)
            else:
                messages.error(request, message)
                # Stay on verification page with error
                verification = EmailVerification.objects.filter(
                    user=user,
                    email=user.email,
                    is_verified=False
                ).first()
                from django.conf import settings
                is_dev_mode = settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'
                is_debug = settings.DEBUG
                
                context = {
                    'user': user,
                    'email': user.email,
                    'has_code': verification is not None,
                    'is_expired': verification.is_expired() if verification else False,
                    'verification_code': verification.code if (verification and (is_dev_mode or is_debug)) else None,
                }
                return render(request, 'accounts/verify_email.html', context)
        
        # Get latest verification code
        verification = EmailVerification.objects.filter(
            user=user,
            email=user.email,
            is_verified=False
        ).first()
        
        # Check if email backend is console (development mode) or DEBUG mode
        from django.conf import settings
        is_dev_mode = settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'
        is_debug = settings.DEBUG
        
        # Show verification code in dev mode or debug mode, or if email sending failed
        show_code = False
        if verification:
            if is_dev_mode or is_debug:
                show_code = True
            else:
                # Check if email might have failed - show code anyway in DEBUG mode
                show_code = is_debug
        
        context = {
            'user': user,
            'email': user.email,
            'has_code': verification is not None,
            'is_expired': verification.is_expired() if verification else False,
            'verification_code': verification.code if (verification and show_code) else None,
        }
        
        return render(request, 'accounts/verify_email.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'Invalid user')
        return redirect('accounts:register')


def verification_success_view(request, user_id):
    """Verification success page"""
    try:
        user = User.objects.get(id=user_id)
        context = {
            'user': user
        }
        return render(request, 'accounts/verification_success.html', context)
    except User.DoesNotExist:
        messages.error(request, 'Invalid user')
        return redirect('accounts:register')


def verification_failed_view(request):
    """Verification failed page"""
    user_id = request.GET.get('user_id')
    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass
    
    context = {
        'user': user
    }
    return render(request, 'accounts/verification_failed.html', context)


def resend_verification_code(request, user_id):
    """Resend verification code"""
    try:
        user = User.objects.get(id=user_id)
        verification = send_verification_email(user, user.email)
        
        if verification:
            # Check if using console backend
            from django.conf import settings
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                messages.info(request, f'Verification code: {verification.code} (Check console/terminal)')
            else:
                messages.success(request, 'Verification code has been sent to your email')
        else:
            # Get the code from the database even if email failed
            verification = EmailVerification.objects.filter(
                user=user,
                email=user.email,
                is_verified=False
            ).first()
            if verification:
                messages.warning(request, f'Email sending failed. Your code is: {verification.code}. Please check your email configuration.')
            else:
                messages.error(request, 'Failed to generate verification code. Please try again later.')
            
    except User.DoesNotExist:
        messages.error(request, 'Invalid user')
    
    return redirect('accounts:verify_email', user_id=user_id)


@login_required
def dashboard_view(request):
    """Dashboard view - redirects based on user role with comprehensive data from database"""
    user = request.user
    
    # Import models safely
    try:
        from jobs.models import Job, Application, SavedJob
        from education.models import Course, Enrollment, Certificate, SavedCourse
        from .models import Notification
        from .utils import get_recommended_jobs, get_user_profile_completeness
        
        # Get user statistics
        if user.role == 'youth':
            applications = Application.objects.filter(applicant=user)
            saved_jobs = SavedJob.objects.filter(user=user)
            enrollments = Enrollment.objects.filter(user=user)
            profile = getattr(user, 'job_seeker_profile', None)
            
            # Get AI-recommended jobs
            recommended_jobs = get_recommended_jobs(user, limit=10)
            
            # Get profile completeness
            profile_completeness = get_user_profile_completeness(user)
            
            # Get unread notifications
            unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
            
            # Get certificates
            certificates = Certificate.objects.filter(user=user)
            
            context = {
                'user': user,
                'profile': profile,
                'total_applications': applications.count(),
                'active_applications': applications.filter(status__in=['pending', 'reviewing', 'shortlisted']).count(),
                'accepted_applications': applications.filter(status='accepted').count(),
                'applications': applications.order_by('-applied_at')[:5],
                'saved_jobs_count': saved_jobs.count(),
                'saved_jobs': saved_jobs.select_related('job').order_by('-saved_at')[:5],
                'total_enrollments': enrollments.count(),
                'completed_courses': enrollments.filter(status='completed').count(),
                'enrollments': enrollments.order_by('-enrolled_at')[:5],
                'recommended_jobs': recommended_jobs,
                'profile_completeness': profile_completeness,
                'unread_notifications': unread_notifications,
                'certificates_count': certificates.count(),
            }
            return render(request, 'accounts/dashboard_youth.html', context)
            
        elif user.role == 'employer':
            jobs = Job.objects.filter(company=user)
            applications = Application.objects.filter(job__company=user)
            profile = getattr(user, 'employer_profile', None)
            from .models import SavedCandidate
            
            # Get saved candidates
            saved_candidates = SavedCandidate.objects.filter(employer=user)
            
            # Get unread notifications
            unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
            
            context = {
                'user': user,
                'profile': profile,
                'total_jobs': jobs.count(),
                'active_jobs': jobs.filter(status='active', is_active=True).count(),
                'pending_jobs': jobs.filter(status='pending').count(),
                'total_applications': applications.count(),
                'pending_applications': applications.filter(status='pending').count(),
                'shortlisted_applications': applications.filter(status='shortlisted').count(),
                'hired_count': applications.filter(status='accepted').count(),
                'recent_applications': applications.select_related('applicant', 'job').order_by('-applied_at')[:5],
                'jobs': jobs.order_by('-date_posted')[:5],
                'saved_candidates_count': saved_candidates.count(),
                'unread_notifications': unread_notifications,
            }
            return render(request, 'accounts/dashboard_employer.html', context)
            
        elif user.role == 'admin' or user.is_staff:
            return redirect('admin_panel:dashboard')
        else:
            return render(request, 'accounts/dashboard_youth.html', {'user': user})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Dashboard error: {str(e)}")
        # Fallback if models don't exist yet
        if user.role == 'employer':
            return render(request, 'accounts/dashboard_employer.html', {'user': user})
        elif user.role == 'admin' or user.is_staff:
            return redirect('admin_panel:dashboard')
        else:
            return render(request, 'accounts/dashboard_youth.html', {'user': user})


@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    
    # Get profile based on role
    profile = None
    if user.role == 'youth':
        profile = getattr(user, 'job_seeker_profile', None)
    elif user.role == 'employer':
        profile = getattr(user, 'employer_profile', None)
    elif user.role == 'institution':
        profile = getattr(user, 'institution_profile', None)
    
    context = {
        'user': user,
        'profile': profile
    }
    
    return render(request, 'accounts/profile.html', context)


# ========================================
# YOUTH / JOB SEEKER DASHBOARD FEATURES
# ========================================

@login_required
def profile_edit_view(request):
    """Edit personal profile"""
    if request.user.role != 'youth':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    user = request.user
    profile = getattr(user, 'job_seeker_profile', None)
    
    if not profile:
        from .models import JobSeekerProfile
        profile = JobSeekerProfile.objects.create(user=user)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        # Save theme preference
        theme_pref = request.POST.get('theme_preference', 'light')
        if theme_pref in ['light', 'dark', 'auto']:
            user.theme_preference = theme_pref
        user.save()
        
        profile.education_level = request.POST.get('education_level', profile.education_level)
        profile.skills = request.POST.get('skills', profile.skills)
        profile.interests = request.POST.get('interests', profile.interests)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.location = request.POST.get('location', profile.location)
        
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        if 'resume' in request.FILES:
            profile.resume = request.FILES['resume']
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        # Sync theme with localStorage
        return redirect('accounts:profile_edit')
    
    context = {'user': user, 'profile': profile}
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def resume_builder_view(request):
    """Generate resume from profile data"""
    if request.user.role != 'youth':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    user = request.user
    profile = getattr(user, 'job_seeker_profile', None)
    from jobs.models import Application
    from education.models import Enrollment, Certificate
    
    applications = Application.objects.filter(applicant=user)
    enrollments = Enrollment.objects.filter(user=user, status='completed')
    certificates = Certificate.objects.filter(user=user)
    
    context = {
        'user': user,
        'profile': profile,
        'applications': applications,
        'enrollments': enrollments,
        'certificates': certificates,
    }
    
    if request.GET.get('download') == 'pdf':
        # PDF generation would go here
        from django.http import HttpResponse
        # This is a placeholder - actual PDF generation requires reportlab or weasyprint
        return HttpResponse("PDF Resume Download - To be implemented with PDF library")
    
    return render(request, 'accounts/resume_builder.html', context)


@login_required
def applications_list_view(request):
    """View all job applications"""
    if request.user.role != 'youth':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import Application
    
    applications = Application.objects.filter(applicant=request.user).select_related('job', 'job__company')
    
    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    context = {
        'applications': applications.order_by('-applied_at'),
        'status_filter': status_filter,
    }
    return render(request, 'accounts/applications_list.html', context)


@login_required
def saved_jobs_view(request):
    """View saved/bookmarked jobs"""
    if request.user.role != 'youth':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import SavedJob
    
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        saved_job_id = request.POST.get('saved_job_id')
        try:
            saved_job = SavedJob.objects.get(id=saved_job_id, user=request.user)
            saved_job.delete()
            messages.success(request, 'Job removed from saved')
            return redirect('accounts:saved_jobs')
        except SavedJob.DoesNotExist:
            messages.error(request, 'Saved job not found')
    
    saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job')
    
    context = {'saved_jobs': saved_jobs}
    return render(request, 'accounts/saved_jobs.html', context)


@login_required
def saved_courses_view(request):
    """View saved courses"""
    if request.user.role != 'youth':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from education.models import SavedCourse
    
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        saved_course_id = request.POST.get('saved_course_id')
        try:
            saved_course = SavedCourse.objects.get(id=saved_course_id, user=request.user)
            saved_course.delete()
            messages.success(request, 'Course removed from saved')
            return redirect('accounts:saved_courses')
        except SavedCourse.DoesNotExist:
            messages.error(request, 'Saved course not found')
    
    saved_courses = SavedCourse.objects.filter(user=request.user).select_related('course')
    
    context = {'saved_courses': saved_courses}
    return render(request, 'accounts/saved_courses.html', context)


@login_required
def certificates_view(request):
    """View all certificates"""
    if request.user.role != 'youth':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from education.models import Certificate
    
    certificates = Certificate.objects.filter(user=request.user).select_related('course')
    
    context = {'certificates': certificates}
    return render(request, 'accounts/certificates.html', context)


@login_required
def notifications_view(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark as read if viewing
    if request.GET.get('mark_read') == 'all':
        notifications.update(is_read=True)
        messages.success(request, 'All notifications marked as read')
    
    context = {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    return render(request, 'accounts/notifications.html', context)


@login_required
def messages_view(request):
    """View messages/chat"""
    from .models import Message
    
    # Get conversations (unique senders/receivers)
    sent_messages = Message.objects.filter(sender=request.user)
    received_messages = Message.objects.filter(receiver=request.user)
    
    # Get unique users in conversations
    conversation_partners = set()
    for msg in sent_messages:
        conversation_partners.add(msg.receiver)
    for msg in received_messages:
        conversation_partners.add(msg.sender)
    
    # Get conversation with specific user
    user_id = request.GET.get('with')
    messages_list = []
    if user_id:
        try:
            other_user = User.objects.get(id=user_id)
            messages_list = Message.objects.filter(
                (Q(sender=request.user, receiver=other_user) |
                 Q(sender=other_user, receiver=request.user))
            ).order_by('created_at')
            
            # Mark as read
            Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
        except User.DoesNotExist:
            pass
    
    # Send message
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        message_text = request.POST.get('message')
        if receiver_id and message_text:
            try:
                receiver = User.objects.get(id=receiver_id)
                Message.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    message=message_text
                )
                messages.success(request, 'Message sent!')
                return redirect(f"{request.path}?with={receiver_id}")
            except User.DoesNotExist:
                messages.error(request, 'User not found')
    
    context = {
        'conversation_partners': conversation_partners,
        'messages': messages_list,
        'current_user_id': user_id,
    }
    return render(request, 'accounts/messages.html', context)


@login_required
def profile_analytics_view(request):
    """View profile analytics and statistics"""
    if request.user.role != 'youth':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import Application
    from education.models import Enrollment
    from .utils import get_user_profile_completeness
    
    applications = Application.objects.filter(applicant=request.user)
    enrollments = Enrollment.objects.filter(user=request.user)
    
    # Application statistics
    app_stats = {
        'total': applications.count(),
        'pending': applications.filter(status='pending').count(),
        'shortlisted': applications.filter(status='shortlisted').count(),
        'accepted': applications.filter(status='accepted').count(),
        'rejected': applications.filter(status='rejected').count(),
    }
    
    # Course statistics
    course_stats = {
        'total': enrollments.count(),
        'in_progress': enrollments.filter(status='in_progress').count(),
        'completed': enrollments.filter(status='completed').count(),
    }
    
    profile_completeness = get_user_profile_completeness(request.user)
    
    context = {
        'app_stats': app_stats,
        'course_stats': course_stats,
        'profile_completeness': profile_completeness,
    }
    return render(request, 'accounts/profile_analytics.html', context)


# ========================================
# EMPLOYER DASHBOARD FEATURES
# ========================================

@login_required
def company_profile_edit_view(request):
    """Edit company profile"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    user = request.user
    profile = getattr(user, 'employer_profile', None)
    
    if not profile:
        from .models import EmployerProfile
        profile = EmployerProfile.objects.create(user=user, company_name=user.username)
    
    if request.method == 'POST':
        profile.company_name = request.POST.get('company_name', profile.company_name)
        profile.company_website = request.POST.get('company_website', profile.company_website)
        profile.industry = request.POST.get('industry', profile.industry)
        profile.company_size = request.POST.get('company_size', profile.company_size)
        profile.company_description = request.POST.get('company_description', profile.company_description)
        profile.location = request.POST.get('location', profile.location)
        profile.contact_email = request.POST.get('contact_email', profile.contact_email)
        profile.contact_phone = request.POST.get('contact_phone', profile.contact_phone)
        
        # Save theme preference
        theme_pref = request.POST.get('theme_preference', 'light')
        if theme_pref in ['light', 'dark', 'auto']:
            user.theme_preference = theme_pref
            user.save()
        
        if 'company_logo' in request.FILES:
            profile.company_logo = request.FILES['company_logo']
        
        profile.save()
        messages.success(request, 'Company profile updated successfully!')
        return redirect('accounts:company_profile_edit')
    
    context = {'user': user, 'profile': profile}
    return render(request, 'accounts/company_profile_edit.html', context)


@login_required
def job_post_create_view(request):
    """Create new job posting"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import Job
    from django.utils import timezone
    
    if request.method == 'POST':
        try:
            from decimal import Decimal
            
            # Parse salary if provided
            salary_min = None
            salary_max = None
            if request.POST.get('salary_range_min'):
                try:
                    salary_min = Decimal(request.POST.get('salary_range_min'))
                except:
                    pass
            if request.POST.get('salary_range_max'):
                try:
                    salary_max = Decimal(request.POST.get('salary_range_max'))
                except:
                    pass
            
            # Parse application deadline
            app_deadline = None
            if request.POST.get('application_deadline'):
                try:
                    from django.utils.dateparse import parse_datetime
                    app_deadline = parse_datetime(request.POST.get('application_deadline'))
                except:
                    pass
            
            job = Job.objects.create(
                job_title=request.POST.get('job_title'),
                company_name=request.POST.get('company_name'),
                company=request.user,
                location=request.POST.get('location'),
                is_remote=request.POST.get('is_remote') == 'on',
                work_type=request.POST.get('work_type', 'full_time'),
                job_description=request.POST.get('job_description'),
                qualifications=request.POST.get('qualifications'),
                skills_required=request.POST.get('skills_required'),
                experience_level=request.POST.get('experience_level', 'entry'),
                years_of_experience=int(request.POST.get('years_of_experience', 0) or 0),
                salary_range_min=salary_min,
                salary_range_max=salary_max,
                application_deadline=app_deadline,
                application_link=request.POST.get('application_link', ''),
                status='pending',  # Requires admin approval
            )
            messages.success(request, 'Job posted successfully! Awaiting admin approval.')
            return redirect('accounts:job_manage', job_id=job.id)
        except Exception as e:
            messages.error(request, f'Error creating job: {str(e)}')
    
    return render(request, 'accounts/job_post_create.html')


@login_required
def job_manage_view(request, job_id):
    """Manage job posting"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import Job, Application
    
    job = Job.objects.filter(id=job_id, company=request.user).first()
    if not job:
        messages.error(request, 'Job not found')
        return redirect('accounts:dashboard')
    
    applications = Application.objects.filter(job=job)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            job.job_title = request.POST.get('job_title', job.job_title)
            job.location = request.POST.get('location', job.location)
            job.job_description = request.POST.get('job_description', job.job_description)
            job.skills_required = request.POST.get('skills_required', job.skills_required)
            job.status = request.POST.get('status', job.status)
            job.save()
            messages.success(request, 'Job updated successfully!')
        elif action == 'delete':
            job.delete()
            messages.success(request, 'Job deleted successfully!')
            return redirect('accounts:dashboard')
        elif action == 'update_application_status':
            app_id = request.POST.get('application_id')
            new_status = request.POST.get('status')
            try:
                app = Application.objects.get(id=app_id, job=job)
                app.status = new_status
                app.save()
                messages.success(request, 'Application status updated!')
            except Application.DoesNotExist:
                messages.error(request, 'Application not found')
    
    context = {
        'job': job,
        'applications': applications.order_by('-applied_at'),
    }
    return render(request, 'accounts/job_manage.html', context)


@login_required
def applicants_view(request, job_id=None):
    """View applicants for jobs"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import Application, Job
    
    if job_id:
        job = Job.objects.filter(id=job_id, company=request.user).first()
        applications = Application.objects.filter(job=job) if job else Application.objects.none()
    else:
        applications = Application.objects.filter(job__company=request.user)
        job = None
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    context = {
        'applications': applications.select_related('applicant', 'job').order_by('-applied_at'),
        'job': job,
        'status_filter': status_filter,
    }
    return render(request, 'accounts/applicants.html', context)


@login_required
def candidate_search_view(request):
    """Search for candidates"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from .models import JobSeekerProfile
    
    candidates = User.objects.filter(role='youth', is_active=True)
    
    # Filtering
    skills_filter = request.GET.get('skills')
    location_filter = request.GET.get('location')
    education_filter = request.GET.get('education')
    
    if skills_filter:
        candidates = candidates.filter(job_seeker_profile__skills__icontains=skills_filter)
    if location_filter:
        candidates = candidates.filter(job_seeker_profile__location__icontains=location_filter)
    if education_filter:
        candidates = candidates.filter(job_seeker_profile__education_level=education_filter)
    
    candidates = candidates.select_related('job_seeker_profile')
    
    context = {
        'candidates': candidates,
        'skills_filter': skills_filter,
        'location_filter': location_filter,
        'education_filter': education_filter,
    }
    return render(request, 'accounts/candidate_search.html', context)


@login_required
def candidate_profile_view(request, candidate_id):
    """View candidate profile"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import Application
    from .models import SavedCandidate
    
    candidate = User.objects.filter(id=candidate_id, role='youth').first()
    if not candidate:
        messages.error(request, 'Candidate not found')
        return redirect('accounts:candidate_search')
    
    profile = getattr(candidate, 'job_seeker_profile', None)
    applications = Application.objects.filter(applicant=candidate, job__company=request.user)
    is_saved = SavedCandidate.objects.filter(employer=request.user, candidate=candidate).exists()
    
    # Save/unsave candidate
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            SavedCandidate.objects.get_or_create(employer=request.user, candidate=candidate)
            messages.success(request, 'Candidate saved!')
        elif action == 'unsave':
            SavedCandidate.objects.filter(employer=request.user, candidate=candidate).delete()
            messages.success(request, 'Candidate removed from saved list')
        return redirect('accounts:candidate_profile', candidate_id=candidate_id)
    
    context = {
        'candidate': candidate,
        'profile': profile,
        'applications': applications,
        'is_saved': is_saved,
    }
    return render(request, 'accounts/candidate_profile.html', context)


@login_required
def saved_candidates_view(request):
    """View saved candidates"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from .models import SavedCandidate
    
    saved_candidates = SavedCandidate.objects.filter(employer=request.user).select_related('candidate')
    
    context = {'saved_candidates': saved_candidates}
    return render(request, 'accounts/saved_candidates.html', context)


@login_required
def interview_manage_view(request, application_id):
    """Manage interview for application"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import Application
    from .models import Interview
    from django.utils import timezone
    
    application = Application.objects.filter(id=application_id, job__company=request.user).first()
    if not application:
        messages.error(request, 'Application not found')
        return redirect('accounts:applicants')
    
    interview = Interview.objects.filter(application=application).first()
    
    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        location = request.POST.get('location', '')
        meeting_link = request.POST.get('meeting_link', '')
        notes = request.POST.get('notes', '')
        
        if scheduled_at:
            scheduled_datetime = timezone.datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            
            if interview:
                interview.scheduled_at = scheduled_datetime
                interview.location = location
                interview.meeting_link = meeting_link
                interview.notes = notes
                interview.save()
            else:
                interview = Interview.objects.create(
                    application=application,
                    scheduled_at=scheduled_datetime,
                    location=location,
                    meeting_link=meeting_link,
                    notes=notes,
                )
            
            # Update application status
            application.status = 'interview'
            application.save()
            
            messages.success(request, 'Interview scheduled successfully!')
            return redirect('accounts:applicants', job_id=application.job.id)
    
    context = {
        'application': application,
        'interview': interview,
    }
    return render(request, 'accounts/interview_manage.html', context)


@login_required
def employer_reports_view(request):
    """Generate employer reports"""
    if request.user.role != 'employer':
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    from jobs.models import Job, Application
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    jobs = Job.objects.filter(company=request.user)
    applications = Application.objects.filter(job__company=request.user)
    
    # Time ranges
    last_30_days = timezone.now() - timedelta(days=30)
    last_7_days = timezone.now() - timedelta(days=7)
    
    # Statistics
    stats = {
        'total_jobs': jobs.count(),
        'active_jobs': jobs.filter(status='active', is_active=True).count(),
        'total_applications': applications.count(),
        'applications_30_days': applications.filter(applied_at__gte=last_30_days).count(),
        'applications_7_days': applications.filter(applied_at__gte=last_7_days).count(),
        'hired_count': applications.filter(status='accepted').count(),
        'pending_applications': applications.filter(status='pending').count(),
    }
    
    # Job performance
    job_performance = []
    for job in jobs[:10]:
        job_apps = applications.filter(job=job)
        job_performance.append({
            'job': job,
            'total_applications': job_apps.count(),
            'accepted': job_apps.filter(status='accepted').count(),
        })
    
    context = {
        'stats': stats,
        'job_performance': job_performance,
    }
    
    # Export to CSV/PDF
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employer_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Job Title', 'Total Applications', 'Accepted', 'Status'])
        for perf in job_performance:
            writer.writerow([
                perf['job'].job_title,
                perf['total_applications'],
                perf['accepted'],
                perf['job'].status,
            ])
        return response
    
    return render(request, 'accounts/employer_reports.html', context)


@login_required
def update_theme_view(request):
    """Update user's theme preference"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        theme = data.get('theme', 'light')
        
        if theme in ['light', 'dark', 'auto']:
            request.user.theme_preference = theme
            request.user.save()
            return JsonResponse({'success': True, 'theme': theme})
    
    return JsonResponse({'success': False}, status=400)
