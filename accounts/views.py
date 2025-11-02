from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import User, EmailVerification, JobSeekerProfile, EmployerProfile, InstitutionProfile
from .utils import send_verification_email, verify_email_code


# Create your views here.
def landing_view(request):
    """Landing page view"""
    return render(request, 'landing.html')


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'youth')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password')
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user:
            # Check if user is active
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
                return render(request, 'accounts/login.html')
            
            # Check if user's role matches
            if user.role != role and role in ['youth', 'employer']:
                messages.error(request, f'Please login as {user.get_role_display()}')
                return render(request, 'accounts/login.html')
            
            # Check if email is verified
            if not user.is_verified:
                from django.conf import settings
                # Check if we're in development mode - allow login with warning
                is_dev_mode = settings.DEBUG and settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'
                
                if is_dev_mode:
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
            
            # Redirect based on role
            if user.role == 'youth':
                return redirect('accounts:dashboard')
            elif user.role == 'employer':
                return redirect('accounts:dashboard')
            elif user.role == 'admin' or user.is_staff:
                return redirect('admin_panel:dashboard')
            else:
                return redirect('accounts:dashboard')
        else:
            # Authentication failed - provide more helpful error
            messages.error(request, 'Invalid username or password. Please check your credentials and try again.')
    
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
                
                # Check if using console backend (development mode)
                from django.conf import settings
                is_dev_mode = settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'
                
                if verification:
                    if is_dev_mode:
                        # In development, show code in message
                        messages.info(request, f'Registration successful! Verification code: {verification.code} (Check console/terminal)')
                    # Redirect to email sent confirmation page
                    return redirect('accounts:email_sent', user_id=user.id)
                else:
                    # Email failed but verification code was generated - get it from DB
                    verification = EmailVerification.objects.filter(
                        user=user,
                        email=email,
                        is_verified=False
                    ).first()
                    if verification:
                        messages.warning(request, f'Registration successful but email sending failed. Your verification code is: {verification.code}. Please check your email configuration.')
                    else:
                        messages.warning(request, 'Registration successful but email could not be sent. Please contact support or use resend option.')
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
    """Dashboard view - redirects based on user role"""
    user = request.user
    
    # Import models safely
    try:
        from jobs.models import Job, Application, SavedJob
        from education.models import Course, Enrollment
        
        # Get user statistics
        if user.role == 'youth':
            applications = Application.objects.filter(applicant=user)
            saved_jobs = SavedJob.objects.filter(user=user)
            enrollments = Enrollment.objects.filter(user=user) if hasattr(Enrollment, 'objects') else []
            profile = getattr(user, 'job_seeker_profile', None)
            
            # Get recommended jobs (jobs matching user skills)
            recommended_jobs = Job.objects.filter(status='active', is_active=True).order_by('-date_posted')[:5]
            
            context = {
                'user': user,
                'profile': profile,
                'total_applications': applications.count(),
                'active_applications': applications.filter(status__in=['pending', 'reviewing', 'shortlisted']).count(),
                'applications': applications.order_by('-applied_at')[:5],
                'saved_jobs_count': saved_jobs.count(),
                'total_enrollments': len(enrollments) if enrollments else 0,
                'completed_courses': len([e for e in enrollments if hasattr(e, 'is_completed') and e.is_completed]) if enrollments else 0,
                'recommended_jobs': recommended_jobs,
            }
            return render(request, 'accounts/dashboard_youth.html', context)
            
        elif user.role == 'employer':
            jobs = Job.objects.filter(company=user)
            applications = Application.objects.filter(job__company=user)
            profile = getattr(user, 'employer_profile', None)
            
            context = {
                'user': user,
                'profile': profile,
                'total_jobs': jobs.count(),
                'active_jobs': jobs.filter(status='active', is_active=True).count(),
                'total_applications': applications.count(),
                'pending_applications': applications.filter(status='pending').count(),
                'hired_count': applications.filter(status='accepted').count(),
                'recent_applications': applications.order_by('-applied_at')[:5],
                'jobs': jobs.order_by('-date_posted')[:5],
            }
            return render(request, 'accounts/dashboard_employer.html', context)
            
        elif user.role == 'admin' or user.is_staff:
            return redirect('admin_panel:dashboard')
        else:
            return render(request, 'accounts/dashboard_youth.html', {'user': user})
    except Exception as e:
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
