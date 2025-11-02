# Gmail App Password Setup Guide

## The Problem

Gmail requires "App Passwords" for third-party applications. The error you're seeing:
```
530, b'5.7.0 Authentication Required
```
means Gmail is rejecting your authentication.

## Solution: Generate Gmail App Password

### Step 1: Enable 2-Step Verification
1. Go to https://myaccount.google.com/security
2. Under "Signing in to Google", find "2-Step Verification"
3. Click "Get started" and follow the prompts to enable it

### Step 2: Generate App Password
1. Go back to https://myaccount.google.com/security
2. Under "Signing in to Google", find "App passwords"
3. Click "App passwords" (you may need to sign in again)
4. Select:
   - **App**: Mail
   - **Device**: Windows Computer (or Other)
5. Click "Generate"
6. Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)

### Step 3: Update .env File

Open your `.env` file and add/update:
```
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```
(Remove spaces from the App Password - it's 16 characters without spaces)

### Step 4: Restart Django Server

After updating `.env`, restart your Django server:
```bash
python manage.py runserver
```

## Development Mode (Console Backend)

If you don't want to set up Gmail right now, the system will automatically use the console backend when `EMAIL_HOST_PASSWORD` is not set. This means:

✅ Verification codes will be **printed in the terminal/console**  
✅ The code will also be **displayed on the verification page** in development mode  
✅ No emails will be sent, but you can still test the verification flow

## Quick Fix for Testing

For immediate testing without email setup:

1. **Check the terminal/console** - The verification code will be printed there
2. **Check the verification page** - The code is shown on screen in development mode
3. **Or manually verify** - Use Django admin or shell to verify users

## Verify Email Configuration

Check if email is configured by looking at server startup:
- If you see: `⚠️ EMAIL_PASSWORD not set` → Console backend (development)
- If no warning → SMTP backend (production)

## Alternative: Use Console Backend for Development

If you want to force console backend (no emails), add to `.env`:
```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Need Help?

If emails still don't work after setting up App Password:
1. Make sure 2-Step Verification is enabled
2. Make sure App Password was generated (not regular password)
3. Check that `.env` file is in the project root
4. Restart Django server after updating `.env`
5. Check for spaces or quotes in EMAIL_HOST_PASSWORD

