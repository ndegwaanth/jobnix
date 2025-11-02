# Email Verification Setup Guide

## Configuration

The email verification system is now fully configured to send HTML emails with verification codes.

## Gmail SMTP Setup

1. **Enable 2-Step Verification** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Copy the 16-character password

3. **Update `.env` file**:
   ```
   EMAIL_HOST_USER=ndegwaanthony300@gmail.com
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   ```

## Email Features

✅ **HTML Email Templates** - Professional, branded emails  
✅ **Verification Codes** - 6-digit codes sent to users  
✅ **Verification Links** - Direct links in emails  
✅ **24-Hour Expiration** - Codes expire after 24 hours  
✅ **Resend Functionality** - Users can request new codes  
✅ **Error Handling** - Graceful fallback if email fails

## Email Flow

1. User signs up → Email sent immediately
2. User redirected to "Email Sent" confirmation page
3. User enters verification code or clicks link
4. Success → Redirected to dashboard
5. Failure → Shown error page with resend option

## Testing Email in Development

For development, you can use console backend:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Emails will be printed to console instead of being sent.

## Production Recommendations

For production, consider:
- **SendGrid** (free tier: 100 emails/day)
- **Mailgun** (free tier: 5,000 emails/month)
- **Amazon SES** (very affordable)
- **Postmark** (developer-friendly)

Update `.env` accordingly if using a different provider.

