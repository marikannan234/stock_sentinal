## SMTP Email Service Migration Guide

### Overview

The Stock Sentinel email system has been migrated from async FastMail implementation to a **simple, synchronous SMTP service**. This provides:

✅ **Reliability**: Works perfectly in sync contexts (like the alert scheduler)  
✅ **Simplicity**: Pure Python `smtplib` with no async complexity  
✅ **Performance**: Faster email delivery without async overhead  
✅ **Debugging**: Much easier to troubleshoot SMTP issues  

---

## What Changed

### ❌ Old Implementation (AsyncMail)
```python
# OLD: Complex async handling from sync context
from app.services.email_service import send_alert_triggered_email

send_alert_email_async(
    user_email="user@example.com",
    symbol="AAPL",
    current_price=175.50,
    condition=">",
    target_value=175.00,
    triggered_at="2025-01-16T10:30:45Z",
)
```

**Problems**:
- Requires event loop handling in sync context
- Can fail with "no running event loop" errors
- Complex error handling and recovery
- Hard to debug SMTP issues

### ✅ New Implementation (SMTP)
```python
# NEW: Simple, straightforward SMTP
from app.services.email_smtp import send_alert_notification

success = send_alert_notification(
    user_email="user@example.com",
    symbol="AAPL",
    current_price=175.50,
    condition=">",
    target_value=175.00,
    triggered_at="2025-01-16T10:30:45Z",
)

if success:
    print("Email sent successfully")
```

**Benefits**:
- Works in any sync context (scheduler, background tasks, etc.)
- Simple error handling and retries
- Direct SMTP control and debugging
- No async/await complexity

---

## Module Structure

### `app/services/email_smtp.py` (NEW)

**Functions:**

#### `send_alert_email_smtp(to_email, subject, html_body, text_body=None)`
Low-level SMTP email sending function.

**Parameters:**
- `to_email` (str): Recipient email address
- `subject` (str): Email subject line
- `html_body` (str): HTML email content
- `text_body` (str, optional): Plain text fallback

**Returns:**
- `True` if sent successfully
- `False` if failed (error details in logs)

**Example:**
```python
from app.services.email_smtp import send_alert_email_smtp

success = send_alert_email_smtp(
    to_email="user@example.com",
    subject="Stock Alert: AAPL",
    html_body="<h1>Your alert triggered</h1>",
    text_body="Your alert triggered for AAPL"
)
```

#### `send_alert_notification(user_email, symbol, current_price, ...)`
High-level function for sending formatted alert emails.

**Parameters:**
- `user_email` (str): Recipient email
- `symbol` (str): Stock symbol (e.g., "AAPL")
- `current_price` (float): Current stock price
- `condition` (str): Alert condition (">", "<", ">=", "<=")
- `target_value` (float): Target price
- `triggered_at` (str): ISO timestamp
- `alert_type` (str): Type of alert (price, sma_above, etc.)
- `sma_value` (float, optional): SMA indicator value
- `sma_period` (int, optional): SMA period
- `ema_value` (float, optional): EMA indicator value
- `ema_period` (int, optional): EMA period
- `rsi_value` (float, optional): RSI indicator value
- `rsi_period` (int, optional): RSI period

**Returns:**
- `True` if sent successfully
- `False` if failed (error details in logs)

**Example:**
```python
from app.services.email_smtp import send_alert_notification

success = send_alert_notification(
    user_email="user@example.com",
    symbol="AAPL",
    current_price=175.50,
    condition=">",
    target_value=175.00,
    triggered_at="2025-01-16T10:30:45Z",
    alert_type="price"
)
```

---

## Configuration

Email settings are configured via environment variables in `.env`:

```env
# Email Service Configuration
ENABLE_EMAIL_NOTIFICATIONS=true

# Gmail SMTP Settings
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
```

### Gmail Configuration

1. **Enable 2-Factor Authentication** on your Gmail account

2. **Generate App Password**:
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the generated 16-character password

3. **Set Environment Variables**:
   ```env
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```

### Custom SMTP Server

For non-Gmail SMTP servers:

```env
MAIL_SERVER=smtp.your-server.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_USERNAME=your-username
MAIL_PASSWORD=your-password
MAIL_FROM=noreply@your-server.com
```

---

## Integration Points

### Alert Service (`app/services/alert_service.py`)

When an alert is triggered, the system calls:

```python
from app.services.email_smtp import send_alert_notification

# In _trigger_alert() method
email_sent = send_alert_notification(
    user_email=alert.user.email,
    symbol=alert.stock_symbol,
    current_price=current_price,
    condition=alert.condition.value,
    target_value=alert.target_value,
    triggered_at=triggered_at_str,
    alert_type=alert.alert_type.value,
    sma_value=sma_value,
    sma_period=sma_period,
    ema_value=ema_value,
    ema_period=ema_period,
    rsi_value=rsi_value,
    rsi_period=rsi_period,
)

# Update history record
if email_sent:
    history_entry.email_sent = True
    history_entry.email_sent_at = now
    db.commit()
```

---

## Testing

### Test Script

Run the test script to verify email configuration:

```bash
cd backend
python ../test_email_smtp.py
```

**Output:**
```
================================================================================
TESTING SMTP EMAIL SERVICE
================================================================================

📧 Email Configuration:
  - Enabled: True
  - SMTP Server: smtp.gmail.com:587
  - From Address: your-email@gmail.com
  - Username: your-email@gmail.com
  - STARTTLS: True

📤 Sending test alert email to: your-email@gmail.com
✅ Email sent successfully!
```

### Manual Testing

1. **Create a test alert** that will trigger immediately:
   ```bash
   # Use current price or slightly higher to trigger alert
   ```

2. **Check the alert history** to see if email was sent:
   ```sql
   SELECT * FROM alert_history 
   WHERE email_sent = true 
   ORDER BY triggered_at DESC;
   ```

3. **Check logs** for email sending details:
   ```bash
   tail -f backend/logs/app.log | grep -i "email"
   ```

---

## Error Handling

The SMTP service handles common errors gracefully:

### Configuration Error
```
❌ SMTP error sending alert email: [Errno -2] Can't connect to 'smtp.gmail.com' on port 587
```
**Fix**: Check `MAIL_SERVER` and `MAIL_PORT` settings

### Authentication Error
```
❌ SMTP error sending alert email: (535, b'5.7.8 Username and password not accepted')
```
**Fix**: Verify `MAIL_USERNAME` and `MAIL_PASSWORD` in `.env`

### Invalid Email
```
❌ Failed to send alert email: Invalid email address
```
**Fix**: Verify recipient email is valid

### Network Timeout
```
❌ SMTP error sending alert email: timed out
```
**Fix**: Check internet connection and SMTP server accessibility

---

## Logging

Email operations are logged with full context:

```
[2025-01-16 10:30:45] [INFO] ✅ Alert email sent successfully
    to_email: user@example.com
    subject: Stock Alert: AAPL
```

Enable debug logging to see detailed SMTP communication:

```python
# In .env or config
LOG_LEVEL=DEBUG
```

---

## Troubleshooting

### Email Not Received

1. **Check if email is disabled**:
   ```env
   ENABLE_EMAIL_NOTIFICATIONS=true  # Must be true
   ```

2. **Verify SMTP credentials**:
   ```bash
   python test_email_smtp.py
   ```

3. **Check spam folder** - SMTP emails might be filtered

4. **Verify From address** matches Gmail account:
   ```env
   MAIL_FROM=your-email@gmail.com  # Must match MAIL_USERNAME
   ```

5. **Check logs** for SMTP errors:
   ```bash
   grep -i "email\|smtp" backend/logs/errors.log
   ```

### "Can't connect to SMTP server"

1. Verify server address and port in `.env`
2. Check firewall allows outbound SMTP (port 587)
3. For Gmail, ensure less secure apps is disabled (using app password instead)

### "Username and password not accepted"

1. Verify credentials are correct
2. For Gmail, use app password (16 chars), not account password
3. Test credentials with: `python test_email_smtp.py`

---

## Performance Considerations

### Synchronous vs Asynchronous

The synchronous SMTP approach:

✅ **Pros:**
- Simple, no async complexity
- Works in scheduler context
- Reliable error handling
- Easy debugging

⚠️ **Cons:**
- Blocks scheduler thread during email sending (~1-2 seconds)
- No built-in retry logic

### Optimization

For high-volume deployments:

1. **Async Queue**: Use Celery + FastMail for async email queue  
   (Consider for Phase 2)

2. **Connection Pooling**: Reuse SMTP connections  
   (Low priority - email sending is infrequent)

3. **Timeout Optimization**: Current timeout = 10 seconds  
   (Can reduce to 5 seconds for faster failure detection)

---

## Migration Notes

### Files Modified
- `app/services/alert_service.py`:
  - Removed `send_alert_email_async()` function
  - Removed async/event loop handling
  - Updated email sending call to use `send_alert_notification()`
  - Simplified error handling

### Files Added
- `app/services/email_smtp.py`:
  - New SMTP email service module
  - `send_alert_email_smtp()` - Low-level SMTP function
  - `send_alert_notification()` - High-level alert email function
  - Comprehensive error handling and logging

### Files Removed
- `app/services/email_service.py` (can be removed after verification)

### Dependencies
- **No new dependencies** - Uses Python standard library `smtplib`
- Existing: `python-multipart` (for email content handling)

---

## Next Steps

1. **Verify Configuration**: Update `.env` with correct SMTP settings
2. **Run Test**: Execute `python test_email_smtp.py`
3. **Create Test Alert**: Trigger an alert and verify email reception
4. **Monitor Logs**: Watch logs for email sending activity

---

## References

- [Python smtplib Documentation](https://docs.python.org/3/library/smtplib.html)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [SMTP Configuration Guide](https://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol)

