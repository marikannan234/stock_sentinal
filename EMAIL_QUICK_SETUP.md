## SMTP Email Service - Quick Reference

### Setup (One-time)

1. **Configure .env**:
   ```env
   ENABLE_EMAIL_NOTIFICATIONS=true
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_STARTTLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-char-app-password
   MAIL_FROM=your-email@gmail.com
   ```

2. **Test Configuration**:
   ```bash
   cd backend
   python ../test_email_smtp.py
   ```

---

### Quick Usage

#### Send Alert Email (Most Common)

```python
from app.services.email_smtp import send_alert_notification

# In alert triggering code
success = send_alert_notification(
    user_email="user@example.com",
    symbol="AAPL",
    current_price=175.50,
    condition=">",
    target_value=175.00,
    triggered_at="2025-01-16T10:30:45Z",
    alert_type="price"
)

if success:
    print("Alert email sent")
else:
    print("Failed to send email (check logs)")
```

#### Send Custom Email

```python
from app.services.email_smtp import send_alert_email_smtp

success = send_alert_email_smtp(
    to_email="user@example.com",
    subject="Stock Update",
    html_body="<h1>Hello</h1><p>Your stock update</p>",
    text_body="Your stock update"  # Optional fallback
)
```

---

### Configuration

**Email Settings** (in `.env`):
| Setting | Value | Example |
|---------|-------|---------|
| `ENABLE_EMAIL_NOTIFICATIONS` | Boolean | `true` |
| `MAIL_SERVER` | SMTP host | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_STARTTLS` | Use TLS | `true` |
| `MAIL_USERNAME` | Login email | `your-email@gmail.com` |
| `MAIL_PASSWORD` | App password | `xxxx-xxxx-xxxx-xxxx` |
| `MAIL_FROM` | Sender email | `your-email@gmail.com` |

**Gmail Setup**:
1. Enable 2FA on Gmail account
2. Get app password: https://myaccount.google.com/apppasswords
3. Use 16-char password (without dashes)

---

### Where It's Used

1. **Alert Triggering** (`alert_service.py`):
   - When alert condition is met
   - Notifies user of triggered alert

2. **Custom Implementation**:
   - Import and call from any sync context
   - NO async/await needed
   - Works with schedulers, background tasks, etc.

---

### Logging

**Success Message**:
```
[2025-01-16 10:30:45] [INFO] ✅ Alert email sent successfully
    to_email: user@example.com
    subject: Stock Alert: AAPL
```

**Error Message**:
```
[2025-01-16 10:30:45] [ERROR] ❌ SMTP error sending alert email
    to_email: user@example.com
    subject: Stock Alert: AAPL
    smtp_error: (535, b'5.7.8 Username and password not accepted')
```

**View Logs**:
```bash
tail -f backend/logs/errors.log | grep -i "email"
```

---

### Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Email not sent | Check `ENABLE_EMAIL_NOTIFICATIONS=true` |
| "Can't connect to server" | Verify `MAIL_SERVER` and `MAIL_PORT` |
| "Username and password not accepted" | Use Gmail app password, not account password |
| Email in spam | Check `MAIL_FROM` matches `MAIL_USERNAME` |
| Email blocked by Gmail | Gmail might block initial send, whitelist sender |

---

### Module Files

| File | Purpose |
|------|---------|
| `app/services/email_smtp.py` | Email SMTP implementation |
| `app/services/alert_service.py` | Alert service (uses email_smtp) |
| `test_email_smtp.py` | Test script for email configuration |

---

### Key Functions

**`send_alert_notification()`** - Send formatted alert email
- ✅ Most common function for alerts
- Includes styled HTML email
- Handles indicator values (SMA, EMA, RSI)

**`send_alert_email_smtp()`** - Send raw SMTP email
- ✅ For custom email content
- Direct SMTP control
- More flexibility

---

### Important Notes

1. **Synchronous Only**: No async/await - works in scheduler context
2. **No Retry Logic**: Failed emails are not retried (add if needed)
3. **Pure Python**: Uses stdlib `smtplib`, no FastMail dependency
4. **Error Handling**: Graceful - errors logged, doesn't break alert flow

---

### Example: Full Alert Flow

```python
# 1. Alert condition met
current_price = 175.50
target_price = 175.00
condition = ">"

if current_price > target_price:
    # 2. Record alert trigger
    alert_entry = AlertHistory(
        alert_id=alert.id,
        is_triggered=True,
        message="Alert triggered"
    )
    db.add(alert_entry)
    db.commit()
    
    # 3. Send email notification
    from app.services.email_smtp import send_alert_notification
    
    success = send_alert_notification(
        user_email=alert.user.email,
        symbol=alert.stock_symbol,
        current_price=current_price,
        condition=condition,
        target_value=target_price,
        triggered_at=datetime.utcnow().isoformat(),
        alert_type=alert.alert_type.value
    )
    
    # 4. Update history if email sent
    if success:
        alert_entry.email_sent = True
        alert_entry.email_sent_at = datetime.utcnow()
        db.commit()
        logger.info(f"Alert email sent to {alert.user.email}")
    else:
        logger.warning(f"Alert triggered but email sending failed")
```

---

### Testing

**Test Email Configuration**:
```bash
python test_email_smtp.py
```

**Expected Output**:
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

---

### Resources

- **Full Documentation**: `backend/SMTP_EMAIL_MIGRATION.md`
- **Python smtplib**: https://docs.python.org/3/library/smtplib.html
- **Gmail App Passwords**: https://support.google.com/accounts/answer/185833

