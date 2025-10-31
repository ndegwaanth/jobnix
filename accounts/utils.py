from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import EmailVerification


def send_verification_email(user, email):
    """Send email verification code to user"""
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
    
    # Email subject and message
    subject = 'JobNix - Verify Your Email Address'
    message = f"""
Hello {user.first_name or user.username},

Thank you for signing up for JobNix!

Your email verification code is: {code}

This code will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
The JobNix Team
    """
    
    try:
        send_mail(
            subject,
            message.strip(),
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return verification
    except Exception as e:
        print(f"Error sending email: {e}")
        return None


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

