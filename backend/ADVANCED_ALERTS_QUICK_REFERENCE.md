# Advanced Alert System - Developer Quick Reference

## Quick Start

### Install Migration

```bash
cd backend
alembic upgrade head
```

### Create Different Alert Types

```python
from app.services.alert_service import AlertService
from app.schemas.alert import CreateAlertRequest
from app.models.alert import AlertType

# Inject AlertService via dependency
service = AlertService(db)

# 1. PRICE Alert
request = CreateAlertRequest(
    stock_symbol="AAPL",
    alert_type=AlertType.PRICE,
    condition=">",
    target_value=150.00
)
alert = service.create_alert(user, request)

# 2. PERCENTAGE_CHANGE Alert
request = CreateAlertRequest(
    stock_symbol="AAPL",
    alert_type=AlertType.PERCENTAGE_CHANGE,
    condition=">",
    target_value=5.0  # 5% change
)
alert = service.create_alert(user, request)

# 3. VOLUME_SPIKE Alert
request = CreateAlertRequest(
    stock_symbol="AAPL",
    alert_type=AlertType.VOLUME_SPIKE,
    condition=">",
    target_value=1.5  # 1.5x average volume
)
alert = service.create_alert(user, request)

# 4. CRASH Alert
request = CreateAlertRequest(
    stock_symbol="AAPL",
    alert_type=AlertType.CRASH,
    condition="<",
    target_value=10.0  # 10% drop
)
alert = service.create_alert(user, request)

# 5. CUSTOM Alert
request = CreateAlertRequest(
    stock_symbol="AAPL",
    alert_type=AlertType.CUSTOM,
    condition=">",
    target_value=150.00
)
alert = service.create_alert(user, request)
```

## Model Methods Reference

### Alert Model (`app/models/alert.py`)

```python
from app.models.alert import Alert, AlertType, AlertCondition

# Check specific alert type
alert.check_price_alert(current_price: float) -> bool
alert.check_percentage_change_alert(current_price: float) -> bool
alert.check_volume_spike_alert(current_volume: float, avg_volume: float) -> bool
alert.check_crash_alert(current_price: float) -> bool
alert.check_custom_alert(current_price: float) -> bool

# Unified dispatcher (recommended)
should_trigger = alert.check_alert(
    current_price=175.50,
    avg_volume=50_000_000,
    current_volume=75_000_000
)
```

### Calculation Examples

**PERCENTAGE_CHANGE:**
```python
# Alert config: target_value=5.0 (5%)
last_price = 100.00
current_price = 105.50
percentage_change = ((105.50 - 100.00) / 100.00) * 100  # 5.5%
triggers = percentage_change >= 5.0  # True ✅
```

**VOLUME_SPIKE:**
```python
# Alert config: target_value=1.5 (150%)
avg_volume = 50_000_000
current_volume = 75_000_000
threshold = avg_volume * 1.5  # 75_000_000
triggers = current_volume > threshold  # True ✅
```

**CRASH:**
```python
# Alert config: target_value=10.0 (10% drop)
last_price = 100.00
current_price = 89.50
percentage_change = ((89.50 - 100.00) / 100.00) * 100  # -10.5%
triggers = percentage_change <= -10.0  # True ✅
```

## Scheduler Integration

### Background Scheduler (`check_all_alerts()`)

```python
# app/services/alert_service.py
def check_all_alerts() -> None:
    """Called every 30 seconds by APScheduler"""
    
    db = SessionLocal()
    try:
        # 1. Fetch alerts
        alerts = db.query(Alert).filter(Alert.is_active == True).all()
        
        # 2. Group by symbol
        alerts_by_symbol = {}
        for alert in alerts:
            symbol = alert.stock_symbol.upper()
            if symbol not in alerts_by_symbol:
                alerts_by_symbol[symbol] = []
            alerts_by_symbol[symbol].append(alert)
        
        # 3. Fetch data per symbol (efficient batching)
        for symbol, symbol_alerts in alerts_by_symbol.items():
            stock = yf.Ticker(symbol)
            data = stock.history(period="20d")
            
            current_price = float(data["Close"].iloc[-1])
            current_volume = float(data["Volume"].iloc[-1])
            avg_volume = float(data["Volume"].iloc[:-1].mean())
            
            # 4. Check each alert
            for alert in symbol_alerts:
                should_trigger = alert.check_alert(
                    current_price,
                    avg_volume=avg_volume,
                    current_volume=current_volume
                )
                
                if should_trigger:
                    trigger_alert(db, alert, current_price)
                
                # 5. Update last_price
                if alert.alert_type in [
                    AlertType.PERCENTAGE_CHANGE,
                    AlertType.CRASH
                ]:
                    alert.last_price = current_price
                    db.commit()
    finally:
        db.close()
```

## Schema Changes

### Database Migration (`0005_add_advanced_alerts.py`)

**New Columns:**
```sql
-- AlertType enum
ALTER TABLE alerts ADD COLUMN alert_type alerttype NOT NULL DEFAULT 'price';

-- Previous price tracking
ALTER TABLE alerts ADD COLUMN last_price FLOAT NULL;

-- New indexes
CREATE INDEX ix_alerts_alert_type ON alerts(alert_type);

-- Updated unique constraint
ALTER TABLE alerts 
  DROP CONSTRAINT uq_alerts_user_stock_condition,
  ADD CONSTRAINT uq_alerts_user_stock_type_condition 
    UNIQUE (user_id, stock_symbol, alert_type, condition, target_value);
```

### Pydantic Schema Updates (`app/schemas/alert.py`)

```python
from app.models.alert import AlertType

class AlertBase(BaseModel):
    stock_symbol: str
    condition: AlertCondition
    target_value: float
    alert_type: AlertType = AlertType.PRICE  # New field

class AlertResponse(AlertBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    triggered_at: Optional[datetime]
    last_price: Optional[float]  # New field
```

## Testing Checklist

### Unit Tests

```python
def test_percentage_change_alert():
    alert = Alert(
        alert_type=AlertType.PERCENTAGE_CHANGE,
        target_value=5.0,
        last_price=100.0
    )
    assert alert.check_percentage_change_alert(105.5) == True
    assert alert.check_percentage_change_alert(104.9) == False

def test_volume_spike_alert():
    alert = Alert(
        alert_type=AlertType.VOLUME_SPIKE,
        target_value=1.5
    )
    assert alert.check_volume_spike_alert(75_000_000, 50_000_000) == True
    assert alert.check_volume_spike_alert(70_000_000, 50_000_000) == False

def test_crash_alert():
    alert = Alert(
        alert_type=AlertType.CRASH,
        target_value=10.0,
        last_price=100.0
    )
    assert alert.check_crash_alert(89.5) == True
    assert alert.check_crash_alert(91.0) == False
```

### Integration Tests

```bash
# 1. Create alerts of each type
# 2. Run scheduler manually
# 3. Verify triggers in logs
# 4. Check email delivery (if enabled)

# Run manually:
python -c "from app.services.alert_service import check_all_alerts; check_all_alerts()"
```

### Manual Testing

```bash
# 1. Start app
cd backend
uvicorn app.main:app --reload

# 2. Open Swagger UI
http://localhost:8000/docs

# 3. Create test alerts
POST /api/alerts
{
  "stock_symbol": "AAPL",
  "alert_type": "percentage_change",
  "condition": ">",
  "target_value": 1.0
}

# 4. Monitor logs
tail -f backend/logs/app.log | grep -i percentage

# 5. Wait 30-60 seconds for scheduler
# 6. Verify trigger and email
```

## Key Files Reference

| File | Purpose | Key Changes |
|------|---------|-------------|
| `app/models/alert.py` | Alert data model | Added AlertType enum, last_price field, check_* methods |
| `app/services/alert_service.py` | Alert business logic | Enhanced check_all_alerts(), updated create_alert() |
| `app/schemas/alert.py` | API schemas | Added alert_type, last_price to schemas |
| `alembic/versions/0005_add_advanced_alerts.py` | DB migration | Adds alert_type, last_price columns, indexes |

## Performance Tips

### 1. Optimize Frequent Checks

```python
# Good: Group by symbol
alerts_by_symbol = {}
for alert in alerts:
    symbol = alert.stock_symbol.upper()
    if symbol not in alerts_by_symbol:
        alerts_by_symbol[symbol] = []
    alerts_by_symbol[symbol].append(alert)

# One yfinance call per symbol
for symbol, symbol_alerts in alerts_by_symbol.items():
    stock = yf.Ticker(symbol)
    data = stock.history(period="20d")  # Get volume history once
```

### 2. Batch Database Updates

```python
# Commit once per symbol (not per alert)
for alert in symbol_alerts:
    alert.last_price = current_price
db.commit()  # Single commit
```

### 3. Monitor Query Time

```python
import time

start = time.time()
alerts = db.query(Alert).filter(Alert.is_active == True).all()
elapsed = time.time() - start

logger.info(f"Fetched {len(alerts)} alerts in {elapsed:.3f}s")
```

## Common Pitfalls

### ❌ Don't: Mix up crash and percentage change

```python
# WRONG: Using percentage_change condition for crash detection
alert = Alert(
    alert_type=AlertType.CRASH,
    condition=">",  # ❌ Wrong operator
    target_value=10.0
)

# RIGHT: Crash uses any condition, logic handles negative percent
alert = Alert(
    alert_type=AlertType.CRASH,
    condition="<",  # ✅ Correct
    target_value=10.0
)
```

### ❌ Don't: Forget volume parameters for volume spike

```python
# WRONG: Missing volume parameters
should_trigger = alert.check_alert(current_price)

# RIGHT: Include volume for volume_spike alerts
should_trigger = alert.check_alert(
    current_price,
    avg_volume=avg_volume,
    current_volume=current_volume
)
```

### ❌ Don't: Update last_price for PRICE alerts

```python
# WRONG: Updating last_price for all types
alert.last_price = current_price
db.commit()

# RIGHT: Only update for types that use it
if alert.alert_type in [AlertType.PERCENTAGE_CHANGE, AlertType.CRASH]:
    alert.last_price = current_price
    db.commit()
```

## Logging Reference

**Alert Check Cycle:**
```
[INFO] Starting alert check cycle - total_alerts=15
[DEBUG] Fetched data for symbol: AAPL, current_price=175.50, current_volume=50M
[INFO] 🔔 ALERT TRIGGERED - alert_id=42, type=percentage_change
[INFO] Alert check cycle completed - total_checked=15, triggered=2
```

**Email Notifications:**
```
[INFO] Email notification queued - alert_id=42, to_email=user@example.com
[INFO] Alert notification email sent successfully - symbol=AAPL
[WARNING] Failed to send alert notification email - symbol=AAPL (will retry)
```

**Errors:**
```
[ERROR] Error checking individual alert - alert_id=42, error=...
[ERROR] Error fetching data for symbol: XYZ - alerts_count=3
[ERROR] Fatal error in alert check cycle - error=...
```

## Support

For issues or questions:
1. Check logs: `app/logs/app.log`
2. Review ADVANCED_ALERTS_GUIDE.md for detailed docs
3. Test with manual scheduler run
4. Verify database migration applied: `alembic current`

---

**Migration applied?** ✅ `alembic upgrade head`  
**Scheduler running?** ✅ Check logs for "Alert check cycle"  
**Emails working?** ✅ Test with simple price alert first  
