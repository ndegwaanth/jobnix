from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from .models import EmailVerification
import logging

logger = logging.getLogger(__name__)

import resend


logger = logging.getLogger(__name__)

def send_verification_email(user, email):
    """Send email verification code to user with Gmail SMTP or Resend fallback"""
    # Generate verification code
    code = EmailVerification.generate_code()

    # Create or update verification record
    verification, created = EmailVerification.objects.get_or_create(
        user=user,
        email=email,
        defaults={
            'code': code,
            'expires_at': timezone.now() + timedelta(hours=24)
        }
    )

    if not created:
        verification.code = code
        verification.expires_at = timezone.now() + timedelta(hours=24)
        verification.is_verified = False
        verification.verified_at = None
        verification.save()

    # Build verification URL
    verification_url = (settings.FRONTEND_URL or 'http://localhost:8000') + reverse(
        'accounts:verify_email', kwargs={'user_id': user.id}
    )

    # Email content
    subject = 'JobNix - Verify Your Email Address'
    plain_message = f"""
Hello {user.first_name or user.username},

Thank you for signing up for JobNix!

Your email verification code is: {code}

Or click this link to verify: {verification_url}

This code will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
The JobNix Team
    """

    html_message = render_to_string('accounts/emails/verification_email.html', {
        'user': user,
        'code': code,
        'verification_url': verification_url,
        'expires_hours': 24,
    })

    # Try Gmail (SMTP)
    try:
        email_msg = EmailMultiAlternatives(
            subject,
            plain_message.strip(),
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        email_msg.attach_alternative(html_message, "text/html")
        email_msg.send(fail_silently=False)
        logger.info(f"✅ Verification email sent to {email} via Gmail SMTP")
        return verification

    except Exception as e:
        logger.warning(f"⚠️ Gmail SMTP failed: {e}")

        # --- Fallback to Resend (API-based, works on Render) ---
        try:
            if hasattr(settings, "RESEND_API_KEY") and settings.RESEND_API_KEY:
                resend.api_key = settings.RESEND_API_KEY
                resend.Emails.send({
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": [email],
                    "subject": subject,
                    "html": html_message,
                    "text": plain_message,
                })
                logger.info(f"✅ Verification email sent to {email} via Resend API")
            else:
                logger.error("❌ RESEND_API_KEY not found in environment. Using console/log fallback.")
                logger.info(f"Verification code for {email}: {code}")
        except Exception as api_err:
            logger.error(f"❌ Resend API failed: {api_err}")
            logger.info(f"Verification code for {email}: {code}")

        # Always return verification so user can see code on page
        return verification



# def send_verification_email(user, email):
#     """Send email verification code to user with HTML email"""
#     # Generate verification code
#     code = EmailVerification.generate_code()
    
#     # Create or get existing verification record
#     verification, created = EmailVerification.objects.get_or_create(
#         user=user,
#         email=email,
#         defaults={
#             'code': code,
#             'expires_at': timezone.now() + timedelta(hours=24)
#         }
#     )
    
#     if not created:
#         # Update existing verification
#         verification.code = code
#         verification.expires_at = timezone.now() + timedelta(hours=24)
#         verification.is_verified = False
#         verification.verified_at = None
#         verification.save()
    
#     # Build verification URL
#     verification_url = settings.FRONTEND_URL or 'http://localhost:8000'
#     verification_url += reverse('accounts:verify_email', kwargs={'user_id': user.id})
    
#     # Email subject
#     subject = 'JobNix - Verify Your Email Address'
    
#     # Plain text message
#     plain_message = f"""
# Hello {user.first_name or user.username},

# Thank you for signing up for JobNix!

# Your email verification code is: {code}

# Or click this link to verify: {verification_url}

# This code will expire in 24 hours.

# If you didn't create this account, please ignore this email.

# Best regards,
# The JobNix Team
#     """
    
#     # HTML message
#     html_message = render_to_string('accounts/emails/verification_email.html', {
#         'user': user,
#         'code': code,
#         'verification_url': verification_url,
#         'expires_hours': 24,
#     })
    
#     # Check if using console backend (development mode)
#     is_console_backend = settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'
    
#     try:
#         # Try to send HTML email
#         email_msg = EmailMultiAlternatives(
#             subject,
#             plain_message.strip(),
#             settings.DEFAULT_FROM_EMAIL,
#             [email],
#         )
#         email_msg.attach_alternative(html_message, "text/html")
#         email_msg.send(fail_silently=False)
        
#         if is_console_backend:
#             logger.warning(f"Using console backend - Check terminal/console for verification code: {code}")
#         else:
#             logger.info(f"Verification email sent successfully to {email}")
#         return verification
        
#     except Exception as e:
#         error_message = str(e)
#         logger.error(f"Failed to send verification email to {email}: {error_message}")
        
#         # Check for authentication errors
#         if 'Authentication' in error_message or '530' in error_message or '535' in error_message:
#             logger.error("Gmail authentication failed. Please set EMAIL_HOST_PASSWORD in .env file with Gmail App Password.")
#             logger.error("For development, verification code is: " + verification.code)
#         elif 'Connection' in error_message or 'timeout' in error_message.lower():
#             logger.error("Email server connection failed. Please check your email configuration.")
#             logger.error("For development, verification code is: " + verification.code)
        
#         # Always return verification object so user can see the code on the page
#         # The verification code will be displayed on the verification page if email fails or in DEBUG mode
#         return verification


def verify_email_code(user, email, code):
    """Verify email verification code"""
    try:
        verification = EmailVerification.objects.get(
            user=user,
            email=email,
            code=code,
            is_verified=False
        )
        
        if verification.is_expired():
            return False, "Verification code has expired. Please request a new one."
        
        # Mark as verified
        verification.verify()
        
        # Mark user as verified
        user.is_verified = True
        user.save()
        
        return True, "Email verified successfully!"
        
    except EmailVerification.DoesNotExist:
        return False, "Invalid verification code. Please check and try again."


# ========================================
# AI Recommendation & Analytics Utilities
# ========================================

def calculate_job_match_score(user, job):
    """Calculate AI match score between user and job (0-100)"""
    score = 0.0
    total_weight = 0.0
    
    try:
        profile = user.job_seeker_profile
        
        # Skills match (40% weight)
        if profile.skills and job.skills_required:
            user_skills = [s.strip().lower() for s in profile.skills.split(',')]
            job_skills = [s.strip().lower() for s in job.skills_required.split(',')]
            matching_skills = len(set(user_skills) & set(job_skills))
            total_skills = len(set(job_skills))
            if total_skills > 0:
                skills_score = (matching_skills / total_skills) * 100
                score += skills_score * 0.4
                total_weight += 0.4
        
        # Education match (20% weight)
        if profile.education_level and job.experience_level:
            # Simple matching based on level
            education_map = {
                'primary': 'entry',
                'secondary': 'entry',
                'diploma': 'mid',
                'degree': 'mid',
                'masters': 'senior',
                'phd': 'executive'
            }
            user_level = education_map.get(profile.education_level.lower(), 'entry')
            if user_level == job.experience_level:
                score += 100 * 0.2
            elif user_level in ['mid', 'senior', 'executive'] and job.experience_level == 'entry':
                score += 80 * 0.2
            total_weight += 0.2
        
        # Location match (15% weight)
        if profile.location and job.location:
            if profile.location.lower() in job.location.lower() or job.location.lower() in profile.location.lower():
                score += 100 * 0.15
            elif job.is_remote:
                score += 90 * 0.15
            total_weight += 0.15
        
        # Interest match (15% weight)
        if profile.interests and job.job_title:
            interests = [i.strip().lower() for i in profile.interests.split(',')]
            job_title_lower = job.job_title.lower()
            for interest in interests:
                if interest in job_title_lower or any(word in job_title_lower for word in interest.split()):
                    score += 100 * 0.15
                    total_weight += 0.15
                    break
        
        # Application history (10% weight) - bonus for similar jobs applied to
        from jobs.models import Application
        similar_applications = Application.objects.filter(
            applicant=user,
            job__job_title__icontains=job.job_title.split()[0] if job.job_title else ''
        ).count()
        if similar_applications > 0:
            score += min(100, similar_applications * 10) * 0.1
        total_weight += 0.1
        
        # Normalize score
        if total_weight > 0:
            final_score = score / total_weight
        else:
            final_score = 50.0  # Default score
        
        return min(100.0, max(0.0, final_score))
        
    except Exception as e:
        logger.error(f"Error calculating job match score: {str(e)}")
        return 50.0  # Default score on error


def get_recommended_jobs(user, limit=10):
    """Get AI-recommended jobs for a user"""
    try:
        from jobs.models import Job, Application, SavedJob
        
        # Get user's applied and saved job IDs to exclude
        applied_job_ids = Application.objects.filter(applicant=user).values_list('job_id', flat=True)
        saved_job_ids = SavedJob.objects.filter(user=user).values_list('job_id', flat=True)
        excluded_ids = list(applied_job_ids) + list(saved_job_ids)
        
        # Get active jobs
        jobs = Job.objects.filter(status='active', is_active=True).exclude(id__in=excluded_ids)
        
        # Calculate match scores
        jobs_with_scores = []
        for job in jobs[:50]:  # Limit initial calculation
            score = calculate_job_match_score(user, job)
            jobs_with_scores.append((job, score))
        
        # Sort by score and return top matches
        jobs_with_scores.sort(key=lambda x: x[1], reverse=True)
        recommended = [job for job, score in jobs_with_scores[:limit]]
        
        return recommended
        
    except Exception as e:
        logger.error(f"Error getting recommended jobs: {str(e)}")
        return []


def get_user_profile_completeness(user):
    """Calculate profile completeness percentage"""
    try:
        profile = user.job_seeker_profile
        total_fields = 8
        filled_fields = 0
        
        if user.first_name: filled_fields += 1
        if user.last_name: filled_fields += 1
        if user.email: filled_fields += 1
        if profile.education_level: filled_fields += 1
        if profile.skills: filled_fields += 1
        if profile.bio: filled_fields += 1
        if profile.resume: filled_fields += 1
        if profile.profile_picture: filled_fields += 1
        
        return (filled_fields / total_fields) * 100
    except:
        return 0.0


def get_skill_demand_analysis():
    """Analyze most demanded skills from job listings"""
    try:
        from jobs.models import Job
        from collections import Counter
        
        all_skills = []
        jobs = Job.objects.filter(status='active', is_active=True)
        
        for job in jobs:
            if job.skills_required:
                skills = [s.strip().lower() for s in job.skills_required.split(',')]
                all_skills.extend(skills)
        
        skill_counts = Counter(all_skills)
        top_skills = skill_counts.most_common(20)
        
        return top_skills
    except Exception as e:
        logger.error(f"Error in skill demand analysis: {str(e)}")
        return []


def get_regional_employment_insights():
    """Get employment insights by region/location"""
    try:
        from jobs.models import Job
        from collections import Counter
        
        locations = []
        jobs = Job.objects.filter(status='active', is_active=True)
        
        for job in jobs:
            if job.location:
                # Extract main location (before comma if exists)
                location = job.location.split(',')[0].strip()
                locations.append(location)
        
        location_counts = Counter(locations)
        top_locations = location_counts.most_common(15)
        
        return top_locations
    except Exception as e:
        logger.error(f"Error in regional employment insights: {str(e)}")
        return []

