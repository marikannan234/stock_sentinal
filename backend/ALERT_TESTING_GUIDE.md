# Alert System Diagnosis & Testing Guide

## Quick Diagnosis: Check Alert State

```bash
# Connect to database and see your alert state
docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel

# View alert status
SELECT 
  id, 
  stock_symbol, 
  alert_type,
  condition,
  target_value,
  is_active,
  is_triggered,
  last_triggered_at,
  triggered_at
FROM alerts 
ORDER BY created_at DESC 
LIMIT 5;

# Exit psql
\q
```

---

## The 10-Minute Cooldown: How It Works

Your alert system has a **cooldown mechanism** to prevent email spam:

1. **First Trigger** (e.g., 08:00:00)
   - Alert condition matches
   - Email sent
   - `is_triggered = True`
   - `last_triggered_at = 08:00:00`

2. **Cooldown Period** (08:00:01 - 08:09:59)
   - Condition is STILL true
   - **Email NOT sent** (cooldown active)
   - Log: `Alert in cooldown period, skipping trigger`

3. **After 10 Minutes** (08:10:00+)
   - Condition still true
   - **Email IS sent again**
   - `last_triggered_at = 08:10:00`

4. **If Condition Becomes False** (e.g., 08:05:00)
   - Price drops below trigger level
   - Condition = FALSE
   - **Re-arm happens automatically**
   - `is_triggered = False`
   - `last_triggered_at = NULL`
   - Alert ready to trigger again

---

## Option A: Testing with 10-Minute Cooldown (Production Behavior)

### Create Alerts That Will Trigger

**1. PRICE Alert (Will trigger immediately if price matches)**

```bash
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0aGFsYXBhdGh5a2FubmFuMTIzQGdtYWlsLmNvbSIsImV4cCI6MTc3NTEzODM2OH0.KgmlnUl-vOR1_HUNeGwcPgbN6EG-6K2I6Dn522Fnk-0"

# Get current MSFT price
python -c "import yfinance as yf; price = yf.Ticker('MSFT').history(period='1d')['Close'].iloc[-1]; print(f'Current MSFT: \${price:.2f}')"

# Create alert for price LESS THAN current price (will trigger immediately)
# If MSFT is $400, create alert for price < 450
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "MSFT",
    "alert_type": "PRICE",
    "target_value": 450.0,
    "condition": "<"
  }'
```

**2. PERCENTAGE_CHANGE Alert (Always triggers eventually)**

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "GOOGL",
    "alert_type": "PERCENTAGE_CHANGE",
    "target_value": 0.05
  }'
```

**3. VOLUME_SPIKE Alert (Often triggers)**

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "TSLA",
    "alert_type": "VOLUME_SPIKE",
    "target_value": 30000000.0
  }'
```

### Monitor the Cooldown in Real-Time

```bash
# Terminal 1: Watch logs for triggers and cooldown
cd backend
tail -f logs/app.log | grep -E "(ALERT TRIGGERED|cooldown|Re-arm|Email)"

# Terminal 2: Check database state
watch "docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c 'SELECT id, stock_symbol, is_triggered, last_triggered_at FROM alerts WHERE is_active=true ORDER BY id DESC LIMIT 5;'"

# Terminal 3: Check AlertHistory for triggered records
watch "docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c 'SELECT alert_id, stock_symbol, triggered_at, email_sent FROM alert_history ORDER BY triggered_at DESC LIMIT 10;'"
```

---

## Option B: Testing Without Cooldown (Dev Mode)

For **immediate testing** without waiting 10 minutes between triggers:

### Enable Dev Mode

Create/edit `.env` file in `backend/`:

```bash
cd backend
```

Add this line to `.env`:

```
ALERT_DEV_MODE=true
```

Or set via environment variable:

```bash
# PowerShell
$env:ALERT_DEV_MODE='true'
cd backend
uvicorn app.main:app --reload
```

### Restart Server

```bash
# Stop the server (Ctrl+C in uvicorn terminal)
# Then restart:
cd backend
uvicorn app.main:app --reload
```

### Now Create & Test Alerts Rapidly

```bash
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0aGFsYXBhdGh5a2FubmFuMTIzQGdtYWlsLmNvbSIsImV4cCI6MTc3NTEzODM2OH0.KgmlnUl-vOR1_HUNeGwcPgbN6EG-6K2I6Dn522Fnk-0"

# Create alert
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "NVDA",
    "alert_type": "PRICE",
    "target_value": 100.0,
    "condition": ">"
  }'

# Wait 30 seconds for scheduler cycle
Start-Sleep -Seconds 30

# Check if email was sent
docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c "
SELECT alert_id, triggered_at, email_sent 
FROM alert_history 
WHERE stock_symbol='NVDA' 
ORDER BY triggered_at DESC;"
```

In dev mode, you'll see in logs:
```
INFO: Dev mode: Overriding cooldown, allowing trigger
```

---

## Understanding Re-arm Logic

**Re-arm ONLY happens when condition becomes false.**

### Example: Test Re-arm Behavior

```bash
# Step 1: Create alert for AAPL price < 100
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "PRICE",
    "target_value": 100.0,
    "condition": "<"
  }'

# Step 2: Wait for trigger (30 seconds - when price is < 100)
# If AAPL price is $150, condition is FALSE, no trigger happens

# Step 3: Manually edit alert to trigger
# Create with condition that WILL match immediately:
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "PRICE",
    "target_value": 150.0,
    "condition": "<"
  }'

# Step 4: Wait 30 seconds - Email sent!
# Check logs: "🔔 ALERT TRIGGERED"

# Step 5: Watch for re-arm
# When price moves ABOVE 150 (condition false), you'll see:
# "INFO: Re-arming alert (condition no longer met)"

# Step 6: When price drops BELOW 150 again (condition true again)
# And 10 minutes have passed (or dev mode on)
# Email is sent AGAIN!
```

---

## Comprehensive Testing Script

Save as `test_alerts_complete.ps1`:

```powershell
# ============================================================================
# Stock Sentinel Alert System - Comprehensive Testing Script
# ============================================================================

param(
    [switch]$DevMode = $false,
    [int]$DelaySeconds = 30
)

$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0aGFsYXBhdGh5a2FubmFuMTIzQGdtYWlsLmNvbSIsImV4cCI6MTc3NTEzODM2OH0.KgmlnUl-vOR1_HUNeGwcPgbN6EG-6K2I6Dn522Fnk-0"
$API_URL = "http://localhost:8000/api/alerts"
$headers = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Stock Sentinel Alert System Test Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

if ($DevMode) {
    Write-Host "🔧 DEV MODE ENABLED - Cooldown bypassed" -ForegroundColor Yellow
} else {
    Write-Host "📋 PRODUCTION MODE - 10-minute cooldown active" -ForegroundColor Yellow
}

# Function to create alert
function Create-Alert($symbol, $type, $target, $condition) {
    $body = @{
        stock_symbol = $symbol
        alert_type = $type
        target_value = $target
    }
    
    if ($condition -ne $null) {
        $body.condition = $condition
    }
    
    $json = $body | ConvertTo-Json
    
    try {
        $response = Invoke-WebRequest -Uri $API_URL -Method POST -Headers $headers -Body $json
        $alertId = ($response.Content | ConvertFrom-Json).id
        Write-Host "✓ Created $type alert: $symbol ($alertId)" -ForegroundColor Green
        return $alertId
    } catch {
        Write-Host "✗ Failed to create alert: $_" -ForegroundColor Red
        return $null
    }
}

# Test 1: PRICE Alert
Write-Host "`n1️⃣  Testing PRICE Alert..." -ForegroundColor Magenta
$priceAlert = Create-Alert "AAPL" "PRICE" 100.0 ">"

# Test 2: PERCENTAGE_CHANGE Alert
Write-Host "`n2️⃣  Testing PERCENTAGE_CHANGE Alert..." -ForegroundColor Magenta
$percentAlert = Create-Alert "MSFT" "PERCENTAGE_CHANGE" 0.1 $null

# Test 3: VOLUME_SPIKE Alert
Write-Host "`n3️⃣  Testing VOLUME_SPIKE Alert..." -ForegroundColor Magenta
$volumeAlert = Create-Alert "GOOGL" "VOLUME_SPIKE" 20000000.0 $null

# Test 4: CRASH Alert
Write-Host "`n4️⃣  Testing CRASH Alert..." -ForegroundColor Magenta
$crashAlert = Create-Alert "TSLA" "CRASH" 5.0 $null

Write-Host "`n⏳ Waiting $DelaySeconds seconds for scheduler to run..." -ForegroundColor Cyan
for ($i = 0; $i -lt $DelaySeconds; $i++) {
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
}
Write-Host "`n✓ Scheduler should have run" -ForegroundColor Green

# Check AlertHistory
Write-Host "`n📊 Alert History:" -ForegroundColor Cyan
try {
    $historyQuery = "SELECT alert_id, stock_symbol, triggered_at, email_sent FROM alert_history ORDER BY triggered_at DESC LIMIT 10;"
    $history = docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c $historyQuery
    Write-Host $history -ForegroundColor Yellow
} catch {
    Write-Host "Could not query database" -ForegroundColor Red
}

# Check Alert State
Write-Host "`n📋 Alert Status:" -ForegroundColor Cyan
try {
    $statusQuery = "SELECT id, stock_symbol, is_triggered, last_triggered_at FROM alerts ORDER BY created_at DESC LIMIT 5;"
    $status = docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c $statusQuery
    Write-Host $status -ForegroundColor Yellow
} catch {
    Write-Host "Could not query database" -ForegroundColor Red
}

Write-Host "`n✅ Test complete! Check logs for details:" -ForegroundColor Green
Write-Host "   tail -f logs/app.log | grep -E '(ALERT|cooldown|Re-arm|Email)'" -ForegroundColor Cyan
```

Run it:
```bash
cd backend

# Production mode (10-min cooldown):
.\test_alerts_complete.ps1

# Dev mode (no cooldown):
.\test_alerts_complete.ps1 -DevMode

# Custom delay (wait 60 seconds instead of 30):
.\test_alerts_complete.ps1 -DelaySeconds 60
```

---

## Key Log Indicators

### What You Should See

**First trigger:**
```
WARNING: 🔔 ALERT TRIGGERED
  alert_id: 1
  symbol: AAPL
  current_price: 151.25
  triggered_at: 2026-04-02T14:30:15.123456

INFO: Email notification queued for alert
  alert_id: 1
  user_email: thalapathykannan123@gmail.com
  history_id: 42
```

**During cooldown (next 10 min):**
```
DEBUG: Alert in cooldown period, skipping trigger
  alert_id: 1
  seconds_until_rearm: 598
```

**When condition becomes false (re-arm):**
```
INFO: Re-arming alert (condition no longer met)
  alert_id: 1
  alert_type: PRICE
  symbol: AAPL
```

**After cooldown expires (if condition still true):**
```
WARNING: 🔔 ALERT TRIGGERED
  alert_id: 1
  symbol: AAPL
  (same as first trigger)
```

---

## Troubleshooting

### "Emails keep getting blocked in production"

**Solution:**
- In production, increase `ALERT_COOLDOWN_MINUTES` to 30 or 60
- Set `ALERT_LOG_COOLDOWN_CHECKS: false` to reduce log spam
- Implement cooldown alert summary emails (e.g., send weekly summary instead of each trigger)

### "I need different cooldown for different alert types"

Future enhancement in `trigger_alert()`:
```python
# Custom cooldown per alert type
cooldown_map = {
    "PRICE": 10,
    "PERCENTAGE_CHANGE": 5,
    "VOLUME_SPIKE": 15,
    "CRASH": 30,
}
cooldown_minutes = cooldown_map.get(alert.alert_type.value, 10)
```

### "Scheduler isn't running"

Check it's actually running:
```bash
tail -f logs/app.log | grep "Starting alert check cycle"
```

Should see logs every 30 seconds. If not:
1. Restart server: `Ctrl+C` then `uvicorn app.main:app --reload`
2. Check server startup logs for scheduler init errors
3. Verify database connection is working

---

## Configuration Summary

**in `.env` or environment variables:**

```env
# Alert behavior
ALERT_COOLDOWN_MINUTES=10              # Time between triggers (default: 10)
ALERT_DEV_MODE=false                   # Bypass cooldown for testing (default: false)
ALERT_LOG_COOLDOWN_CHECKS=true          # Log cooldown skips (default: true)

# Email
ENABLE_EMAIL_NOTIFICATIONS=true
MAIL_FROM=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

---

## Next Steps

1. **Check current alert state** with the database query above
2. **Choose:** Production testing (10-min cooldown) OR Dev mode (no cooldown)
3. **Create test alerts** using curl commands or test script
4. **Monitor logs** in real-time: `tail -f logs/app.log`
5. **Check AlertHistory** after 30 seconds
6. **Verify email** was sent by checking your inbox and alert_history.email_sent

**Questions?** Check the logs first - they tell you exactly what's happening!
