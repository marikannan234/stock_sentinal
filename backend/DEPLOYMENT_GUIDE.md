# Quick Deployment Guide - Production Alert Enhancements

## Pre-Deployment Checklist

- [ ] All code changes reviewed and tested locally
- [ ] Database backup created
- [ ] Maintenance window scheduled (if needed)
- [ ] Rollback plan reviewed
- [ ] Team notified of deployment

## Step 1: Apply Database Migration

```bash
# Navigate to backend directory
cd backend

# Apply the migration
alembic upgrade add_tracking_history

# Verify migration was applied successfully
alembic current
# Expected output: add_tracking_history

# Verify table structure
psql -d stock_db -c "\d alert_history"
psql -d stock_db -c "\d+ alerts"
```

**What Gets Created:**
- `alert_history` table with 12 columns
- `is_triggered` column in alerts table
- `last_triggered_at` column in alerts table
- 6 database indexes for optimal query performance

## Step 2: Verify Code Changes

```bash
# Check that all models import correctly
python -c "
from app.models.alert import Alert, AlertHistory
print('✓ Alert model loaded')
print('✓ AlertHistory model loaded')
print(f'Alert fields: is_triggered, last_triggered_at')
print(f'AlertHistory: 12 fields for complete audit trail')
"

# Check that services import correctly
python -c "
from app.services.alert_service import check_all_alerts, trigger_alert
from app.services.email_service import send_alert_triggered_email
print('✓ Alert service loaded')
print('✓ Email service loaded')
"
```

## Step 3: Start the Server

```bash
# Activate virtual environment
.\activate.ps1  # On Windows PowerShell
# or
source venv/bin/activate  # On Linux/Mac

# Start the server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## Step 4: Test Alert Creation (All Types)

### Test 1: PRICE Alert (with condition)

```bash
# Set your JWT token
$TOKEN = "your_jwt_token_here"

# Create PRICE alert
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "stock_symbol": "AAPL",
  "alert_type": "PRICE",
  "target_value": 150.0,
  "condition": ">"
}
EOF

# Expected response: 201 Created with alert ID
```

### Test 2: PERCENTAGE_CHANGE Alert (no condition)

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "stock_symbol": "MSFT",
  "alert_type": "PERCENTAGE_CHANGE",
  "target_value": 5.0
}
EOF

# Expected response: 201 Created with alert ID
```

### Test 3: VOLUME_SPIKE Alert (no condition)

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "stock_symbol": "GOOGL",
  "alert_type": "VOLUME_SPIKE",
  "target_value": 150.0
}
EOF

# Expected response: 201 Created with alert ID
```

### Test 4: CRASH Alert (no condition)

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "stock_symbol": "TSLA",
  "alert_type": "CRASH",
  "target_value": 10.0
}
EOF

# Expected response: 201 Created with alert ID
```

## Step 5: Monitor Scheduler

Open a new terminal and watch the logs:

```bash
cd backend
tail -f logs/app.log | grep -E "(Starting alert check|ALERT TRIGGERED|cooldown|Re-arming)"
```

**Expected Log Output:**
```
INFO: Starting alert check cycle - total_alerts: 4
DEBUG: Fetched data for symbol - symbol: AAPL, current_price: 151.25
INFO: Re-arming alert (condition no longer met) - alert_id: 1
WARNING: 🔔 ALERT TRIGGERED - alert_id: 2, symbol: MSFT, alert_type: PERCENTAGE_CHANGE
```

## Step 6: Verify Database Records

### Check AlertHistory Table

```bash
# Connect to database
psql -d stock_db

# View all alert history records
SELECT id, alert_id, stock_symbol, alert_type, created_at, email_sent 
FROM alert_history 
ORDER BY triggered_at DESC 
LIMIT 10;

# Check specific alert history
SELECT * FROM alert_history 
WHERE alert_id = 1 
ORDER BY triggered_at DESC 
LIMIT 5;
```

### Check Alert State

```bash
# View alert state fields
SELECT id, stock_symbol, alert_type, is_triggered, last_triggered_at, is_active
FROM alerts 
WHERE id IN (1, 2, 3, 4);
```

## Step 7: Test Cooldown Behavior

### Setup Test Alert

```bash
# Create a test alert that will likely trigger
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "stock_symbol": "AAPL",
  "alert_type": "PRICE",
  "target_value": 200.0,  # Usually above current price
  "condition": "<"  # Will trigger immediately if price < 200
}
EOF
```

### Monitor Cooldown

```bash
# Watch logs for cooldown skips
tail -f logs/app.log | grep "cooldown"

# Expected sequence:
# 1. First cycle: ALERT TRIGGERED ✓
# 2. Next cycles (< 10 min): Alert in cooldown period, skipping trigger
# 3. After 10 min: ALERT TRIGGERED (if condition still met)
```

## Step 8: Verify Email Notifications

### Check Email Service Configuration

```bash
python -c "
from app.config import settings
print(f'Email enabled: {settings.ENABLE_EMAIL_NOTIFICATIONS}')
print(f'SMTP server: {settings.MAIL_SERVER}:{settings.MAIL_PORT}')
print(f'From: {settings.MAIL_FROM}')
"
```

### Check Email Send Logs

```bash
tail -f logs/app.log | grep -E "(Email notification|Failed to send|email)"
```

### Verify AlertHistory Email Status

```bash
psql -d stock_db -c "
SELECT 
  id,
  alert_id,
  triggered_at,
  email_sent,
  email_sent_at
FROM alert_history 
ORDER BY triggered_at DESC 
LIMIT 10;
"
```

## Post-Deployment Checks

### Performance Baseline

```bash
# Check scheduler performance
python -c "
import time
from app.services.alert_service import check_all_alerts
from app.db.session import SessionLocal

start = time.time()
check_all_alerts()
elapsed = time.time() - start
print(f'Scheduler cycle time: {elapsed:.2f} seconds')
print('Expected: < 5 seconds for < 1000 alerts')
"
```

### Database Health

```bash
# Check table sizes
psql -d stock_db -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Check indexes
psql -d stock_db -c "
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('alerts', 'alert_history') 
ORDER BY tablename, indexname;
"
```

### Log Review

```bash
# Check for errors in last hour
grep -i error logs/app.log | tail -20

# Check alert trigger activity
grep "ALERT TRIGGERED" logs/app.log | wc -l

# Check cooldown activity
grep "cooldown" logs/app.log | wc -l
```

## Monitoring Dashboard Queries

### Active Alerts with State

```sql
SELECT 
  a.id,
  a.stock_symbol,
  a.alert_type,
  a.condition,
  a.target_value,
  a.is_active,
  a.is_triggered,
  a.last_triggered_at,
  COUNT(h.id) as total_triggers,
  MAX(h.triggered_at) as last_trigger
FROM alerts a
LEFT JOIN alert_history h ON a.id = h.alert_id
GROUP BY a.id, a.stock_symbol, a.alert_type, a.condition, a.target_value, a.is_active, a.is_triggered, a.last_triggered_at
ORDER BY a.id DESC;
```

### Trigger Statistics (24-hour)

```sql
SELECT 
  alert_type,
  COUNT(*) as total_triggers,
  COUNT(*) FILTER (WHERE email_sent) as emails_sent,
  ROUND(100.0 * COUNT(*) FILTER (WHERE email_sent) / COUNT(*), 2) as email_success_rate
FROM alert_history
WHERE triggered_at > NOW() - INTERVAL '24 hours'
GROUP BY alert_type
ORDER BY total_triggers DESC;
```

### Email Status Overview

```sql
SELECT 
  CASE WHEN email_sent THEN 'Sent' ELSE 'Failed' END as status,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM alert_history WHERE triggered_at > NOW() - INTERVAL '24 hours'), 2) as percentage
FROM alert_history
WHERE triggered_at > NOW() - INTERVAL '24 hours'
GROUP BY email_sent;
```

## Rollback Procedure (If Needed)

```bash
cd backend

# Downgrade database to previous migration
alembic downgrade 25e65135c38c

# Verify rollback
alembic current
# Expected: 25e65135c38c

# Restart server
# Server will work with old code path (is_triggered, last_triggered_at ignored)
# AlertHistory records will remain in database
```

## Success Criteria

- [ ] Database migration applied without errors
- [ ] All 4 alert types create successfully
- [ ] Scheduler runs every 30 seconds without errors
- [ ] Alert triggers recorded in AlertHistory
- [ ] Email notifications sent and logged
- [ ] Cooldown prevents duplicate emails within 10 minutes
- [ ] Re-arm logic resets alerts when conditions become false
- [ ] No performance degradation (< 5 sec per cycle)
- [ ] All logs appear correctly formatted
- [ ] Database indexes are in place and used

## Common Issues & Solutions

### Issue: Migration Fails with "Table Already Exists"

**Solution:**
```bash
# Check migration history
alembic history

# If migration was partially applied:
alembic stamp add_tracking_history
```

### Issue: AlertHistory Table Not Found

**Solution:**
```bash
# Verify migration was applied
alembic current

# Apply if not done:
alembic upgrade add_tracking_history

# Check table exists:
psql -d stock_db -c "\dt alert_history"
```

### Issue: Alerts Not Triggering

**Solution:**
```bash
# Check scheduler is running
tail -f logs/app.log | grep "Starting alert check"

# Check alert status
psql -d stock_db -c "SELECT id, stock_symbol, is_active, is_triggered FROM alerts LIMIT 5;"

# Manually trigger check for debugging
python -c "from app.services.alert_service import check_all_alerts; check_all_alerts()"
```

### Issue: Email Send Failures

**Solution:**
```bash
# Check email config
python -c "from app.config import settings; print(settings.MAIL_FROM, settings.MAIL_SERVER)"

# Check AlertHistory email_sent status
psql -d stock_db -c "SELECT COUNT(*) FILTER (WHERE email_sent) FROM alert_history WHERE triggered_at > NOW() - INTERVAL '1 hour';"

# Check logs
grep -i "email" logs/app.log | tail -20
```

## Final Sign-Off

- [ ] All tests passed
- [ ] Performance acceptable
- [ ] Logs reviewed and no errors
- [ ] Database integrity verified
- [ ] Team notified of deployment completion
- [ ] Monitoring configured for ongoing surveillance

**Deployment Date:** _______________
**Deployed By:** ___________________
**Tested By:** ______________________

---

For detailed information, see [PRODUCTION_ENHANCEMENTS.md](PRODUCTION_ENHANCEMENTS.md)
