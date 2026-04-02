# Email Notification System - Implementation Guide

## Overview

Email notifications have been integrated into Stock Sentinel's alert system. When a user's price alert is triggered, an automated email notification is sent to their registered email address with details about the triggered alert.

## What Was Implemented

### 1. **Email Service** (`app/services/email_service.py`)
- FastMail configuration with Gmail SMTP
- Async email sending functions
- HTML-formatted alert notification emails
- Plain text fallback for email clients
- Retry mechanism with exponential backoff
- Comprehensive error handling and logging

### 2. **Alert Service Integration** (`app/services/alert_service.py`)
- `send_alert_email_async()` - Helper function to send async emails from sync scheduler
- Modified `trigger_alert()` - Now sends email when alert is triggered
- Error handling - Email failures don't crash the scheduler
- Logging - All email activities are logged

### 3. **Configuration** (`app/config.py`)
- Email settings added to Pydantic Settings
- Environment variables for SMTP configuration
- Feature flags for enabling/disabling email notifications
- Retry configuration

### 4. **.env File**
- Gmail SMTP credentials configured
- Email feature settings added

## Architecture

```
┌─────────────────────────────────────────┐
│  Background Scheduler (every 30 sec)   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  check_all_alerts()                    │
│  - Fetch active alerts                 │
│  - Check conditions                    │
│  - Match price triggers                │
└────────────────┬────────────────────────┘
                 │
                 ▼ (for each matched alert)
┌─────────────────────────────────────────┐
│  trigger_alert(db, alert, price)       │
│  - Mark alert as triggered             │
│  - Save to database                    │
└────────────────┬────────────────────────┘
                 │
                 ▼ (if ENABLE_EMAIL_NOTIFICATIONS=True)
┌─────────────────────────────────────────┐
│  send_alert_email_async(...)           │
│  - Get user email from alert.user      │
│  - Call email service (async)          │
│  - Handle errors gracefully            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  send_alert_triggered_email()          │
│  (FastMail async coroutine)           │
│  - Render HTML template                │
│  - Send via Gmail SMTP                 │
│  - Log results                         │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  User's Email Inbox                    │
│  ✉️ 🔔 Alert Triggered: AAPL           │
└─────────────────────────────────────────┘
```

## Features

### Email Template
- Professional HTML template with gradient header
- Alert details clearly displayed:
  - Stock symbol
  - Current price
  - Alert condition/criteria
  - Trigger timestamp
- Call-to-action button to view dashboard
- Mobile-responsive design
- Plain text fallback

### Error Handling
- Email failures don't crash the scheduler
- Individual email errors are logged but don't stop other alerts
- Graceful fallback if user email is missing
- Exception details logged for debugging
- Retry mechanism available (optional)

### Async Handling
Since the scheduler runs synchronously but email sending is async:
- `send_alert_email_async()` handles running async code in sync context
- Creates event loop if none exists
- Uses `asyncio.create_task()` if loop is already running
- Uses `loop.run_until_complete()` if loop is not running

### Logging
All email activities are logged:
```
[INFO] Email sent successfully (to_email: user@example.com, subject: 🔔 Stock Alert Triggered: AAPL)
[ERROR] Failed to send alert notification email (symbol: AAPL, error: ConnectionError)
[WARNING] Invalid email address for alert notification (email: invalid-email)
```

## Configuration

### Environment Variables (in .env)

```ini
# Email Server (Gmail SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

# Gmail Credentials
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_FROM=your-email@gmail.com
MAIL_FROM_NAME=Stock Sentinel Alerts

# Feature Flags
ENABLE_EMAIL_NOTIFICATIONS=True
EMAIL_NOTIFICATION_RETRY_COUNT=3
```

### Using Gmail with 2FA

If you have 2-factor authentication enabled on Gmail:

1. Go to [Google Account Security Settings](https://myaccount.google.com/security)
2. Click "App passwords" (bottom section)
3. Select "Mail" and "Windows Computer" (or your device)
4. Google will generate a 16-character password
5. Use this password in `MAIL_PASSWORD` instead of your regular password

**Current Setup:**
```
MAIL_USERNAME=stockernotify@gmail.com
MAIL_PASSWORD=qvbwmnyhfbikvegt  (App-specific password)
MAIL_FROM=stockernotify@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
```

## How It Works

### Step-by-Step Flow

1. **Alert Matches Condition**
   ```
   Alert: AAPL > $195
   Current Price: $196.50
   Match: YES ✓
   ```

2. **trigger_alert() Called**
   ```python
   trigger_alert(db, alert, 196.50)
   ```

3. **Database Updated**
   ```sql
   UPDATE alerts 
   SET is_active = FALSE, triggered_at = NOW() 
   WHERE id = 5
   ```

4. **Email Notification Sent**
   ```python
   send_alert_email_async(
       user_email="user@example.com",
       symbol="AAPL",
       current_price=196.50,
       condition=">",
       target_value=195.00,
       triggered_at="2026-04-02T14:23:45"
   )
   ```

5. **Email Rendered & Sent**
   - HTML template rendered with alert details
   - "From" address: stockernotify@gmail.com
   - "To" address: user@example.com
   - Subject: "🔔 Stock Alert Triggered: AAPL"
   - Sent via Gmail SMTP

6. **User Receives Email**
   - Professional HTML email in inbox
   - Details about triggered alert
   - Link to dashboard for more actions

### Example Email Content

```
Subject: 🔔 Stock Alert Triggered: AAPL

Stock Sentinel Alert Triggered!

Stock Symbol: AAPL
Current Price: $196.50
Alert Condition: AAPL > $195.00
Triggered At: 2026-04-02 14:23:45 UTC

Your price alert for AAPL has been triggered. 
The current price of $196.50 matches your alert condition.

This alert is now inactive.

[View Dashboard Button]

---
Stock Sentinel - Real-time Stock Market Monitoring
This is an automated email. Please do not reply to this message.
```

## Files Modified/Created

### New Files
- **`app/services/email_service.py`** (370 lines)
  - Email configuration
  - HTML template
  - Email sending functions
  - Retry mechanism

### Modified Files
- **`app/config.py`** (+15 lines)
  - Email settings added
  - Configuration for SMTP
  - Feature flags

- **`app/services/alert_service.py`** (+80 lines)
  - Import statements for asyncio and config
  - `send_alert_email_async()` function
  - Modified `trigger_alert()` with email logic

- **`.env`** (added email section)
  - Gmail SMTP configuration
  - Feature flags

- **`requirements.txt`** (3 new packages)
  - fastapi-mail==1.6.2
  - aiosmtplib==5.1.0
  - blinker==1.9.0
  - (jinja2, regex, starlette auto-installed)

## Installation & Setup

### 1. Install Dependencies
```bash
pip install fastapi-mail aiosmtplib blinker
# Or use requirements.txt if updated
pip install -r requirements.txt
```

### 2. Configure .env
```bash
# Edit backend/.env and add:
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # (Not your regular password!)
MAIL_FROM=your-email@gmail.com
MAIL_FROM_NAME=Stock Sentinel Alerts
ENABLE_EMAIL_NOTIFICATIONS=True
EMAIL_NOTIFICATION_RETRY_COUNT=3
```

### 3. Verify Setup
```bash
cd backend
.\.venv\Scripts\Activate.ps1
python -c "from app.services.email_service import send_alert_triggered_email; print('✅ Email service ready')"
```

### 4. Start the Application
```bash
uvicorn app.main:app --reload
```

Watch the logs for "Background scheduler started" message.

## Testing Email Notifications

### Test 1: Manual Email Send
```python
import asyncio
from app.services.email_service import send_alert_triggered_email

# Run manually
asyncio.run(send_alert_triggered_email(
    to_email="test@example.com",
    symbol="AAPL",
    current_price=195.50,
    condition=">",
    target_value=195.00,
    triggered_at="2026-04-02 12:34:56 UTC"
))
```

### Test 2: Via Alert Triggering
1. Create an alert with very low target price (guaranteed to trigger)
2. Wait for scheduler to run (30 seconds)
3. Check user's email inbox
4. Verify email was received

### Test 3: Check Logs
```bash
tail -f backend/logs/app.log | grep -i email
```

Expected output:
```
[INFO] Email sent successfully (to_email: user@example.com)
[INFO] Email notification queued for alert (alert_id: 5)
```

## Troubleshooting

### Issue: Email not sending

**Check 1: Is email enabled?**
```python
from app.config import settings
print(f"Email enabled: {settings.ENABLE_EMAIL_NOTIFICATIONS}")
```

**Check 2: Are credentials correct?**
```python
from app.config import settings
print(f"Server: {settings.MAIL_SERVER}:{settings.MAIL_PORT}")
print(f"Username: {settings.MAIL_USERNAME}")
print(f"From: {settings.MAIL_FROM}")
```

**Check 3: Is the user email valid?**
```python
# Check the alert's user email
from app.db.session import SessionLocal
from app.models.alert import Alert

db = SessionLocal()
alert = db.query(Alert).filter(Alert.id == 5).first()
print(f"User email: {alert.user.email if alert.user else 'NO USER'}")
db.close()
```

**Check 4: Check logs for email errors**
```bash
grep -i "failed to send email" backend/logs/app.log
```

### Issue: "Authentication failed" error

This usually means the password is incorrect or 2FA is preventing login.

**Solution:**
1. Use [App Passwords](https://myaccount.google.com/apppasswords) if 2FA is enabled
2. The 16-character app password is NOT your regular password
3. Update `.env` with the app-specific password
4. Don't use special characters that need escaping

### Issue: "Connection refused" or "timeout"

This means the SMTP server can't be reached.

**Solutions:**
1. Check internet connection
2. Verify firewall isn't blocking port 587
3. Try a different email provider's SMTP settings
4. Check if VPN is interfering

### Issue: Emails going to spam

Gmail might filter automated emails as spam.

**Solutions:**
1. Add email domain to trusted senders
2. Adjust email template (avoid spam keywords)
3. Use company email instead of Gmail

## Production Checklist

- [ ] Use [App Passwords](https://myaccount.google.com/apppasswords) for Gmail
- [ ] Don't commit `.env` with real credentials to git
- [ ] Use environment-specific `.env` files (`.env.production`)
- [ ] Test email delivery before launch
- [ ] Monitor email sending success rate in logs
- [ ] Set up email provider alerts/limits
- [ ] Have fallback email service (SendGrid, AWS SES) as backup
- [ ] Add SMTP connection pooling if high volume
- [ ] Implement email queue/celery for async handling (optional)

## Future Enhancements

1. **Email Templates Per Alert Type**
   ```python
   # Different templates for different alert conditions
   - Price threshold alerts
   - Percentage change alerts
   - Volume alerts
   ```

2. **User Email Preferences**
   ```python
   # Allow users to:
   - Disable emails per alert
   - Choose email frequency (immediate, daily digest, weekly)
   - Select multiple email addresses
   - Add SMS notifications
   ```

3. **Email Queue System**
   - Use Celery + Redis for async email queue
   - Automatic retries on failure
   - Rate limiting

4. **Advanced Email**
   - Stock chart attachment
   - Trending indicators
   - Recommended actions
   - Personalization

5. **Multi-Channel Notifications**
   - SMS via Twilio
   - Push notifications via Firebase
   - Slack/Discord webhooks
   - In-app notifications

## API Reference

### send_alert_triggered_email()
```python
async def send_alert_triggered_email(
    to_email: str,                    # User's email
    symbol: str,                      # Stock symbol (e.g., "AAPL")
    current_price: float,             # Current stock price
    condition: str,                   # Condition operator (">", "<", etc.)
    target_value: float,              # Alert target price
    triggered_at: str,                # Timestamp (ISO format)
) -> bool:
    """
    Send formatted email notification for triggered alert.
    
    Returns:
        True if sent successfully, False otherwise
    """
```

### send_email()
```python
async def send_email(
    to_email: str,                    # Recipient
    subject: str,                     # Email subject
    body: str,                        # Plain text body
    html_body: Optional[str] = None,  # HTML body (optional)
) -> bool:
    """
    Send a generic email.
    
    Returns:
        True if sent successfully, False otherwise
    """
```

### send_alert_email_async()
```python
def send_alert_email_async(
    user_email: str,
    symbol: str,
    current_price: float,
    condition: str,
    target_value: float,
    triggered_at: str,
) -> None:
    """
    Helper to send email from synchronous scheduler context.
    Handles async/sync conversion seamlessly.
    """
```

## Summary

Email notifications are now fully integrated with Stock Sentinel's alert system. When a user's alert triggers:

1. ✅ Alert is marked as triggered in database
2. ✅ Email notification is sent to user
3. ✅ Email contains all alert details
4. ✅ Professional HTML formatting
5. ✅ Errors don't crash the scheduler
6. ✅ All actions are logged

The system is production-ready and can handle email sending without blocking the background scheduler!
