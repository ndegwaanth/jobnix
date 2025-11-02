from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from .models import EmailVerification
import logging

logger = logging.getLogger(__name__)


def send_verification_email(user, email):
    """Send email verification code to user with HTML email"""
    # Generate verification code
    code = EmailVerification.generate_code()
    
    # Create or get existing verification record
    verification, created = EmailVerification.objects.get_or_create(
        user=user,
        email=email,
        defaults={
            'code': code,
            'expires_at': timezone.now() + timedelta(hours=24)
        }
    )
    
    if not created:
        # Update existing verification
        verification.code = code
        verification.expires_at = timezone.now() + timedelta(hours=24)
        verification.is_verified = False
        verification.verified_at = None
        verification.save()
    
    # Build verification URL
    verification_url = settings.FRONTEND_URL or 'http://localhost:8000'
    verification_url += reverse('accounts:verify_email', kwargs={'user_id': user.id})
    
    # Email subject
    subject = 'JobNix - Verify Your Email Address'
    
    # Plain text message
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
    
    # HTML message
    html_message = render_to_string('accounts/emails/verification_email.html', {
        'user': user,
        'code': code,
        'verification_url': verification_url,
        'expires_hours': 24,
    })
    
    # Check if using console backend (development mode)
    is_console_backend = settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'
    
    try:
        # Try to send HTML email
        email_msg = EmailMultiAlternatives(
            subject,
            plain_message.strip(),
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        email_msg.attach_alternative(html_message, "text/html")
        email_msg.send(fail_silently=False)
        
        if is_console_backend:
            logger.warning(f"Using console backend - Check terminal/console for verification code: {code}")
        else:
            logger.info(f"Verification email sent successfully to {email}")
        return verification
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Failed to send verification email to {email}: {error_message}")
        
        # Check for authentication errors
        if 'Authentication' in error_message or '530' in error_message or '535' in error_message:
            logger.error("Gmail authentication failed. Please set EMAIL_HOST_PASSWORD in .env file with Gmail App Password.")
            logger.error("For development, verification code is: " + code)
        
        # Still return verification object so user can see the code on the page
        # The verification code will be displayed on the verification page if email fails
        return verification


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

