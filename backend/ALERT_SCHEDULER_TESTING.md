# Background Alert System - Quick Start & Testing Guide

## Quick Start (5 Minutes)

### 1. Start FastAPI with Scheduler Active

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**Expected output in logs:**
```
✅ Background scheduler started (alert checks every 30 seconds)
All routes registered (StockSentinel API is ready to serve requests)
```

### 2. Verify Scheduler is Running

Open another terminal:
```bash
curl http://localhost:8000/api/health
```

**Expected response:**
```json
{"status": "healthy", "timestamp": "2026-04-02T12:00:00"}
```

### 3. Test Alert Creation (via Swagger)

1. Open http://localhost:8000/docs
2. Go to **POST /api/alerts** endpoint
3. Click "Try it out"
4. Enter request body:
```json
{
  "stock_symbol": "AAPL",
  "condition": ">",
  "target_value": 195.0
}
```
5. Click "Execute"
6. Note the returned `alert_id`

## Manual Testing

### Test 1: Verify Scheduler is Running

**File:** `test_scheduler_running.py`

```python
from app.services.scheduler import is_scheduler_running

print(f"Scheduler running: {is_scheduler_running()}")
```

**Run:**
```bash
python test_scheduler_running.py
# Output: Scheduler running: True
```

### Test 2: Manual Alert Check

**File:** `test_manual_check.py`

```python
from app.services.alert_service import check_all_alerts

print("Running manual alert check...")
check_all_alerts()
print("Check completed. See logs for results.")
```

**Run:**
```bash
python test_manual_check.py
```

**Expected output in logs:**
```
Starting alert check cycle (total_alerts: 5)
Alert check cycle completed (alerts_triggered: 0, symbols_processed: 3)
```

### Test 3: Create Alert and Watch Triggering

**File:** `test_alert_trigger.py`

```python
from datetime import datetime
from app.db.session import SessionLocal
from app.models.alert import Alert, AlertCondition
from app.models.user import User

# Setup
db = SessionLocal()

# Get first user (or create one)
user = db.query(User).first()
if not user:
    print("No users found. Create a user via API first.")
    exit(1)

# Create an alert with VERY LOW target (guaranteed to trigger)
# Example: AAPL current price ~195, alert triggers if price > 1 (always true)
alert = Alert(
    user_id=user.id,
    stock_symbol="AAPL",
    condition=AlertCondition.GREATER_THAN,
    target_value=1.0,  # Very low, guaranteed to match current price
    is_active=True,
)

db.add(alert)
db.commit()
db.refresh(alert)

print(f"Created alert: {alert.id}")
print(f"Symbol: {alert.stock_symbol}")
print(f"Condition: {alert.condition.value}")
print(f"Target: {alert.target_value}")
print(f"Active: {alert.is_active}")
print()
print("Waiting 35 seconds for scheduler to run...")
print("(Scheduler runs every 30 seconds)")

import time
for i in range(35):
    time.sleep(1)
    print(f"  {i}s", end="\r")

# Check if triggered
db.refresh(alert)
print()
print(f"After 35 seconds:")
print(f"  is_active: {alert.is_active} (should be False if triggered)")
print(f"  triggered_at: {alert.triggered_at}")

if not alert.is_active:
    print("\n✅ SUCCESS: Alert was triggered!")
else:
    print("\n❌ FAILED: Alert was not triggered")
    print("Check logs for scheduler activity")

db.close()
```

**Run:**
```bash
python test_alert_trigger.py
# Expected: ✅ SUCCESS: Alert was triggered!
```

### Test 4: Multiple Alerts with Different Symbols

**File:** `test_multiple_alerts.py`

```python
from app.db.session import SessionLocal
from app.models.alert import Alert, AlertCondition
from app.models.user import User

db = SessionLocal()
user = db.query(User).first()

if not user:
    print("No users found. Create a user via API first.")
    exit(1)

# Create alerts for different symbols
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
alerts = []

for symbol in symbols:
    alert = Alert(
        user_id=user.id,
        stock_symbol=symbol,
        condition=AlertCondition.GREATER_THAN,
        target_value=1.0,  # Guaranteed to trigger
        is_active=True,
    )
    db.add(alert)
    alerts.append(alert)

db.commit()

print(f"Created {len(alerts)} alerts:")
for alert in alerts:
    print(f"  - {alert.symbol} > {alert.target_value}")

print("\nWaiting 35 seconds...")
import time
time.sleep(35)

db.refresh(*alerts)
triggered = sum(1 for a in alerts if not a.is_active)

print(f"\nResults:")
print(f"  Total alerts: {len(alerts)}")
print(f"  Triggered: {triggered}")
print(f"  Active: {sum(1 for a in alerts if a.is_active)}")

if triggered > 0:
    print("\n✅ SUCCESS: Alerts were triggered!")
else:
    print("\n❌ FAILED: No alerts were triggered")

db.close()
```

**Run:**
```bash
python test_multiple_alerts.py
```

### Test 5: Check Scheduler Logs

**File:** `test_scheduler_logs.sh` (PowerShell)

```powershell
# Tail the application logs (last 50 lines)
Get-Content logs/app.log -Tail 50

# Or filter for scheduler logs
Get-Content logs/app.log | Select-String "alert check" -Context 0,5
```

## Performance Testing

### Test 6: Load Test with 100 Alerts

**File:** `test_load_100_alerts.py`

```python
from app.db.session import SessionLocal
from app.models.alert import Alert, AlertCondition
from app.models.user import User
import time

db = SessionLocal()
user = db.query(User).first()

if not user:
    print("No users found.")
    exit(1)

# Create 100 alerts
print("Creating 100 alerts...")
start = time.time()

symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX", "NVDA"]
for i in range(100):
    alert = Alert(
        user_id=user.id,
        stock_symbol=symbols[i % len(symbols)],
        condition=AlertCondition.GREATER_THAN,
        target_value=1.0,
        is_active=True,
    )
    db.add(alert)

db.commit()
elapsed = time.time() - start
print(f"✓ Created 100 alerts in {elapsed:.2f}s")

# Wait for scheduler to check them
print("\nWaiting for scheduler to run...")
time.sleep(35)

# Count triggered
triggered = db.query(Alert).filter(Alert.is_active == False).count()
print(f"\nResults:")
print(f"  Total alerts: 100")
print(f"  Triggered: {triggered}")
print(f"  Check cycle time: {elapsed:.2f}s")

if triggered > 95:
    print("\n✅ SUCCESS: Scheduler handled load well!")
else:
    print(f"\n⚠️  Only {triggered}/100 alerts triggered, check logs")

db.close()
```

**Run:**
```bash
python test_load_100_alerts.py
```

## Integration Testing

### Test 7: Full End-to-End Flow

1. **Start the app:**
```bash
cd backend
uvicorn app.main:app --reload
```

2. **In another terminal, register a user:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

3. **Login to get token:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }'
```
(Note the `access_token` from response)

4. **Create an alert:**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "condition": ">",
    "target_value": 1.0
  }'
```

5. **Wait 35 seconds and check alert:**
```bash
curl -X GET http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

The alert should have `is_active: false` and `triggered_at` set.

## Debugging

### Check Scheduler Status

```python
from app.services.scheduler import get_scheduler, is_scheduler_running

print(f"Running: {is_scheduler_running()}")

scheduler = get_scheduler()
if scheduler:
    jobs = scheduler.get_jobs()
    for job in jobs:
        print(f"Job: {job.name} (ID: {job.id})")
        print(f"  Function: {job.func_ref}")
        print(f"  Next run: {job.next_run_time}")
```

### Monitor Logs in Real-Time

**PowerShell (Windows):**
```powershell
Get-Content logs/app.log -Wait -Tail 10
```

**Bash (Linux/Mac):**
```bash
tail -f logs/app.log
```

### Check Active Alerts Count

```python
from app.db.session import SessionLocal
from app.models.alert import Alert

db = SessionLocal()
active = db.query(Alert).filter(Alert.is_active == True).count()
triggered = db.query(Alert).filter(Alert.is_active == False).count()

print(f"Active alerts: {active}")
print(f"Triggered alerts: {triggered}")
print(f"Total: {active + triggered}")

db.close()
```

### Force Run Scheduler Job

```python
from app.services.scheduler import get_scheduler

scheduler = get_scheduler()
if scheduler:
    # Get the job
    job = scheduler.get_job("check_alerts_job")
    if job:
        print("Running job manually...")
        job.func()  # Call the check_all_alerts() function
        print("Done!")
```

## Troubleshooting Checklist

- [ ] FastAPI starts without errors
- [ ] Log shows "Background scheduler started"
- [ ] At least one alert exists in database
- [ ] Alert `is_active = True`
- [ ] Stock symbol is valid (try AAPL, MSFT)
- [ ] Waited at least 30 seconds for scheduler run
- [ ] Check logs for "[ERROR]" messages
- [ ] Verify database connection works: `SELECT COUNT(*) FROM alerts`
- [ ] Test yfinance manually: `python -c "import yfinance; print(yfinance.Ticker('AAPL').info)"`

## Success Criteria

✅ **All tests pass if:**
- Scheduler starts with app
- At least 90% of alerts trigger within 35 seconds
- Logs show alert checking activity
- Triggered alerts have `is_active=False` and `triggered_at` timestamp
- No database errors in logs
- No hanging or blocking the main thread

## Next Steps

1. **Set up notifications** - Email/SMS when alert triggers
2. **Create monitoring dashboard** - View alert status in real-time
3. **Implement alert history** - Keep records of all triggered alerts  
4. **Add manual email trigger** - Button to send test notification
5. **Create alert analytics** - Charts of most-triggered symbols
