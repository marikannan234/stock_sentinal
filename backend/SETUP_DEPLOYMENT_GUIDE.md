# Advanced Alert System - Setup & Deployment Guide

## Prerequisites

- ✅ FastAPI application running
- ✅ PostgreSQL database configured
- ✅ SQLAlchemy models working
- ✅ Alembic migrations set up
- ✅ APScheduler for background jobs

---

## Step 1: Apply Database Migration

### Check Current Migration Status

```bash
cd backend
.\.venv\Scripts\Activate.ps1

# See current revision
alembic current
# Output: 0004_add_alerts_table
```

### Apply New Migration

```bash
# Upgrade to next revision
alembic upgrade head

# Should output:
# INFO [alembic.runtime.migration] Context impl PostgreSQLImpl.
# INFO [alembic.runtime.migration] Will assume transactional DDL.
# INFO [alembic.runtime.migration] Running upgrade 0004_add_alerts_table -> 0005_add_advanced_alerts

# Verify
alembic current
# Output: 0005_add_advanced_alerts
```

### Verify Database Changes

```bash
# Connect to PostgreSQL
psql -U postgres -d stocksentinel

# Check new columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'alerts'
ORDER BY ordinal_position;

# Expected new rows:
# alert_type | USER-DEFINED (alerttype)
# last_price | double precision

# Check enum type
\dT alerttype
# Should show: CREATE TYPE public.alerttype AS ENUM ('price', 'percentage_change', ...)

# Check indexes
\d alerts
# Should show: ix_alerts_alert_type, ix_alerts_user_id_active, etc.
```

---

## Step 2: Update Environment (Optional)

The advanced alert system works with existing configuration. No new environment variables required.

**Email Notifications** (already set up):
```ini
# .env
ENABLE_EMAIL_NOTIFICATIONS=True
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=stockernotify@gmail.com
MAIL_PASSWORD=qvbwmnyhfbikvegt
```

---

## Step 3: Start Application

### Terminal 1: FastAPI Server

```bash
cd backend
.\.venv\Scripts\Activate.ps1

# Start with hot reload (development)
uvicorn app.main:app --reload

# Or production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Verify Scheduler Running

```bash
# In FastAPI logs, should see every 30 seconds:
[INFO] Starting alert check cycle - total_alerts=0
[INFO] Alert check cycle completed - total_checked=0
```

---

## Step 4: Create Test Alerts

### Option A: Swagger UI (Recommended)

1. Open http://localhost:8000/docs
2. Scroll to `POST /api/alerts`
3. Click "Try it out"
4. Enter JSON for each alert type

### Option B: curl Commands

**Alert 1: Price Threshold**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "price",
    "condition": ">",
    "target_value": 150.0
  }'
```

**Alert 2: Percentage Change (5%)**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "percentage_change",
    "condition": ">",
    "target_value": 5.0
  }'
```

**Alert 3: Volume Spike (1.5x)**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "volume_spike",
    "condition": ">",
    "target_value": 1.5
  }'
```

**Alert 4: Crash Detection (5% drop)**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "crash",
    "condition": "<",
    "target_value": 5.0
  }'
```

**Alert 5: Custom (current implementation = price)**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "custom",
    "condition": ">",
    "target_value": 150.0
  }'
```

### Get Bearer Token

```bash
# Use login endpoint
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password"
  }'

# Response includes "access_token"
# Use that in Authorization header
```

---

## Step 5: Monitor Alerts

### View All Your Alerts

```bash
curl -X GET http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Specific Alert

```bash
curl -X GET http://localhost:8000/api/alerts/42 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Delete Alert

```bash
curl -X DELETE http://localhost:8000/api/alerts/42 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Step 6: Monitor Scheduler Execution

### Real-time Logs

```bash
# Watch scheduler every 30 seconds
tail -f backend/logs/app.log | grep "Alert check cycle"

# Expected output:
# [INFO] Starting alert check cycle - total_alerts=5
# [DEBUG] Fetched data for symbol: AAPL, current_price=175.50
# [INFO] Alert check cycle completed - total_checked=5, alerts_triggered=0
```

### Monitor Specific Alert Type

```bash
tail -f backend/logs/app.log | grep -i "percentage_change"
```

### Check Email Delivery

```bash
tail -f backend/logs/app.log | grep -i "email"
```

### Monitor Errors

```bash
tail -f backend/logs/app.log | grep -i "error"
```

---

## Step 7: Verify Email Notifications

### Create Low-Value Alert

Create an alert that's likely to trigger (e.g., very low price target):

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "price",
    "condition": "<",
    "target_value": 1.0
  }'
```

### Wait for Trigger

- Wait 30-60 seconds for scheduler
- Check logs for "ALERT TRIGGERED"
- Check inbox for email from stockernotify@gmail.com
- Verify email contains all alert details

---

## Testing Checklist

### ✅ Unit Tests

```python
# Test percentage change logic
from app.models.alert import Alert, AlertType

alert = Alert(
    alert_type=AlertType.PERCENTAGE_CHANGE,
    target_value=5.0,
    last_price=100.0
)

assert alert.check_percentage_change_alert(105.5) == True   # 5.5% >= 5%
assert alert.check_percentage_change_alert(104.9) == False  # 4.9% < 5%
```

### ✅ Integration Tests

```python
# Test check_all_alerts with database
from app.services.alert_service import check_all_alerts

check_all_alerts()  # Should complete without errors
# Check logs for results
```

### ✅ Functional Tests

| Test Case | Command | Expected Result |
|-----------|---------|-----------------|
| Create price alert | POST /api/alerts | 201, returns alert with alert_type |
| Create percentage alert | POST /api/alerts | 201, returns last_price=null |
| List alerts | GET /api/alerts | 200, includes all alert fields |
| Get specific alert | GET /api/alerts/{id} | 200, includes alert_type and last_price |
| Delete alert | DELETE /api/alerts/{id} | 204 No Content |
| Scheduler runs | Wait 30s | Logs show check cycle |
| Alert triggers | Create low target | Alert is_active becomes false |
| Email sent | Check inbox | Email from stockernotify@gmail.com |

---

## Production Configuration

### Environment Variables

```ini
# .env (production)

# Database
DATABASE_URL=postgresql://user:pass@prod-db:5432/stocksentinel

# Email (alerts already configured)
ENABLE_EMAIL_NOTIFICATIONS=True

# FastAPI
DEBUG=False
LOG_LEVEL=INFO

# Scheduler (already configured in app)
# Runs every 30 seconds by default
```

### Logging

```python
# app/core/logging_config.py is already configured
# Logs to: backend/logs/app.log
# Level: INFO (DEBUG in development)
# Format: Structured with context (user_id, alert_id, symbol, etc.)
```

### Monitoring Recommendations

```bash
# Set up log rotation (logrotate)
/var/log/stock-sentinel/app.log {
    daily
    rotate 30
    compress
    delaycompress
    postrotate
        systemctl reload stock-sentinel-api
    endscript
}

# Monitor scheduler health (cron)
*/5 * * * * grep -c "Alert check cycle completed" /var/log/stock-sentinel/app.log | mail -s "Stock Sentinel Health"

# Alert on errors (systemd)
[Service]
OnFailure=alert-on-unit-failure@%u.service
```

---

## Rollback Plan (If Needed)

### Revert Migration

```bash
cd backend
.\.venv\Scripts\Activate.ps1

# Downgrade to previous version
alembic downgrade 0004_add_alerts_table

# Verify
alembic current
# Should show: 0004_add_alerts_table
```

### Notes on Rollback

- Existing alerts remain in database
- New alert_type values become invalid
- Scheduler will skip alerts with missing fields
- Best to backfill alert_type during upgrade (already done with DEFAULT 'price')

---

## Troubleshooting

### Issue: Migration fails with "duplicate key violation"

**Solution:**
```bash
# Check if columns already exist
psql -U postgres -d stocksentinel

SELECT column_name FROM information_schema.columns 
WHERE table_name = 'alerts' AND column_name = 'alert_type';

# If exists, downgrade and reinvestigate
alembic downgrade -1
```

### Issue: Scheduler not running

**Check:**
```bash
# Verify APScheduler is initialized in app startup
grep -i "scheduler\|apscheduler" app/main.py backend/logs/app.log

# Should see scheduler.start() during app startup
```

### Issue: No triggers from volume_spike alerts

**Check:**
```bash
# Verify yfinance returns volume data
python -c "
import yfinance as yf
data = yf.Ticker('AAPL').history('20d')
print(data[['Close', 'Volume']].tail())
"

# Should show volume values
```

### Issue: last_price not updating

**Check:**
```bash
# Verify percentage_change and crash alerts
SELECT id, alert_type, last_price 
FROM alerts 
WHERE alert_type IN ('percentage_change', 'crash');

# Should show last_price populated after first check
```

---

## Performance Tuning

### For High Volume (1000+ alerts)

```sql
-- Add materialized view for alert stats
CREATE MATERIALIZED VIEW alert_stats AS
SELECT 
    alert_type,
    count(*) as total,
    count(*) FILTER (WHERE is_active) as active,
    count(*) FILTER (WHERE triggered_at IS NOT NULL) as triggered
FROM alerts
GROUP BY alert_type;

-- Add partial index for active alerts only
CREATE INDEX ix_alerts_user_id_active_only 
ON alerts (user_id) 
WHERE is_active = true;

-- Add partial index by alert type
CREATE INDEX ix_alerts_percentage_change 
ON alerts (user_id, stock_symbol) 
WHERE alert_type = 'percentage_change' AND is_active = true;
```

---

## Documentation References

- **Complete Guide:** ADVANCED_ALERTS_GUIDE.md
- **Quick Reference:** ADVANCED_ALERTS_QUICK_REFERENCE.md
- **Implementation Summary:** ADVANCED_ALERTS_IMPLEMENTATION_SUMMARY.md (this file)

---

## Support Contacts

**For issues or questions:**

1. Check logs: `backend/logs/app.log`
2. Review documentation files
3. Run test suite
4. Check database state

---

## Success Criteria

After setup, verify:

- [ ] Migration applied successfully
- [ ] Application starts without errors
- [ ] Scheduler logs appear every 30s
- [ ] Can create alerts of all types
- [ ] Alerts display all fields including alert_type
- [ ] Scheduler checks all alert types
- [ ] Email notifications work
- [ ] last_price updates for percentage_change/crash alerts
- [ ] Triggered alerts are marked is_active=false

---

**Ready to deploy! 🚀**

Next steps:
1. Apply migration: `alembic upgrade head`
2. Start application: `uvicorn app.main:app --reload`
3. Create test alerts via Swagger UI
4. Monitor logs for scheduler execution
5. Verify email notifications

Questions? Check the comprehensive guides in the backend directory.
