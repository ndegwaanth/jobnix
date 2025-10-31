from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
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
        
        user = authenticate(request, username=username, password=password)
        if user:
            # Check if user's role matches
            if user.role != role and role in ['youth', 'employer']:
                messages.error(request, f'Please login as {user.get_role_display()}')
                return render(request, 'accounts/login.html')
            
            # Check if email is verified
            if not user.is_verified:
                messages.warning(request, 'Please verify your email before logging in. A verification code has been sent to your email.')
                verification = send_verification_email(user, user.email)
                return redirect('accounts:verify_email', user_id=user.id)
            
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
            messages.error(request, 'Invalid username or password')
    
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
                
                if verification:
                    messages.success(request, f'Registration successful! Please check your email ({email}) for verification code.')
                    return redirect('accounts:verify_email', user_id=user.id)
                else:
                    messages.warning(request, 'Registration successful but email could not be sent. Please contact support.')
                    return redirect('accounts:login')
                    
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    # Get role from query parameter if present
    context = {
        'role': request.GET.get('role', '')
    }
    return render(request, 'accounts/signup.html', context)


def verify_email_view(request, user_id):
    """Email verification view"""
    try:
        user = User.objects.get(id=user_id)
        
        if request.method == 'POST':
            code = request.POST.get('code', '').strip()
            
            if not code:
                messages.error(request, 'Please enter verification code')
                return render(request, 'accounts/verify_email.html', {'user': user})
            
            success, message = verify_email_code(user, user.email, code)
            
            if success:
                messages.success(request, message)
                # Auto login after verification
                login(request, user)
                return redirect('accounts:dashboard')
            else:
                messages.error(request, message)
        
        # Get latest verification code
        verification = EmailVerification.objects.filter(
            user=user,
            email=user.email,
            is_verified=False
        ).first()
        
        context = {
            'user': user,
            'email': user.email,
            'has_code': verification is not None
        }
        
        return render(request, 'accounts/verify_email.html', context)
        
    except User.DoesNotExist:
        messages.error(request, 'Invalid user')
        return redirect('accounts:register')


def resend_verification_code(request, user_id):
    """Resend verification code"""
    try:
        user = User.objects.get(id=user_id)
        verification = send_verification_email(user, user.email)
        
        if verification:
            messages.success(request, 'Verification code has been sent to your email')
        else:
            messages.error(request, 'Failed to send verification code. Please try again later.')
            
    except User.DoesNotExist:
        messages.error(request, 'Invalid user')
    
    return redirect('accounts:verify_email', user_id=user_id)


@login_required
def dashboard_view(request):
    """Dashboard view - redirects based on user role"""
    user = request.user
    
    if user.role == 'youth' or user.role == 'job_seeker':
        return render(request, 'accounts/dashboard_youth.html', {'user': user})
    elif user.role == 'employer':
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
