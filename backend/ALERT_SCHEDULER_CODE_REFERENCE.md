# Background Alert System - Code Reference

## File Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── scheduler.py          ← NEW: Scheduler lifecycle management
│   │   └── alert_service.py      ← MODIFIED: Added check_all_alerts() & trigger_alert()
│   └── main.py                   ← MODIFIED: Integrated scheduler into lifespan
├── ALERT_SCHEDULER_README.md     ← NEW: Implementation summary
├── ALERT_SCHEDULER_GUIDE.md      ← NEW: Technical documentation
└── ALERT_SCHEDULER_TESTING.md    ← NEW: Testing & quick-start guide
```

## Core Functions Reference

### scheduler.py

#### start_scheduler()
```python
def start_scheduler() -> None:
    """
    Start the background scheduler for periodic alert checking.
    
    Starts a BackgroundScheduler that runs alert checking every 30 seconds.
    Safe to call multiple times - subsequent calls are idempotent.
    
    Raises:
        RuntimeError: If scheduler fails to start
    
    Configuration:
    - Interval: 30 seconds
    - Max instances: 1 (prevents concurrent executions)
    - Misfire grace time: 10 seconds
    - Daemon mode: True
    """
```

#### stop_scheduler()
```python
def stop_scheduler() -> None:
    """
    Stop the background scheduler gracefully.
    
    Safe to call multiple times - stopping an already-stopped scheduler is idempotent.
    """
```

#### pause_scheduler()
```python
def pause_scheduler() -> None:
    """Pause the scheduler (temporarily stops job execution)."""
```

#### resume_scheduler()
```python
def resume_scheduler() -> None:
    """Resume the scheduler (resumes job execution)."""
```

#### is_scheduler_running()
```python
def is_scheduler_running() -> bool:
    """Check if scheduler is currently running."""
```

#### get_scheduler()
```python
def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the global scheduler instance."""
```

### alert_service.py

#### check_all_alerts()
```python
def check_all_alerts() -> None:
    """
    Check all active alerts and trigger those whose conditions are met.
    
    This function is called by the background scheduler every 30 seconds.
    
    Process:
    1. Fetch all active alerts from database
    2. Group by stock symbol (efficient batching)
    3. Fetch current prices using yfinance
    4. Compare prices against alert conditions
    5. Trigger matching alerts atomically
    6. Log comprehensive metrics
    
    Features:
    - Graceful error handling (one failure doesn't stop others)
    - Proper database session management
    - Logging with context for debugging
    - No blocking operations
    
    Example output:
    - Starting alert check cycle (total_alerts: 100)
    - 🔔 ALERT TRIGGERED: AAPL > $195 @ $196.50
    - Alert check cycle completed (alerts_triggered: 5)
    """
```

Example usage:
```python
from app.services.alert_service import check_all_alerts

# Run check immediately
check_all_alerts()

# Or scheduler runs it automatically every 30 seconds
```

#### trigger_alert()
```python
def trigger_alert(
    db: Session,
    alert: Alert,
    current_price: float
) -> bool:
    """
    Trigger an alert by marking it as inactive and setting triggered_at timestamp.
    
    Args:
        db: Database session
        alert: Alert to trigger
        current_price: Current stock price that matched the condition
    
    Returns:
        True if alert was triggered successfully, False if already triggered
    
    Operations:
    1. Check if alert already triggered (prevent duplicates)
    2. Set is_active = False
    3. Set triggered_at = datetime.utcnow()
    4. Commit changes to database
    5. Log alert triggered event
    
    Idempotency:
    Once triggered, alert cannot be triggered again without re-enabling via API.
    """
```

Example usage:
```python
from app.db.session import SessionLocal
from app.models.alert import Alert
from app.services.alert_service import trigger_alert

db = SessionLocal()
alert = db.query(Alert).filter(Alert.id == 5).first()

if alert and alert.matches_condition(current_price=196.50):
    triggered = trigger_alert(db, alert, 196.50)
    if triggered:
        print(f"Alert {alert.id} triggered!")
```

## Integration Points

### main.py - FastAPI Lifespan Integration

**Before (without scheduler):**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    Base.metadata.create_all(bind=engine)
    logger.info(f"{settings.APP_NAME} started successfully")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
```

**After (with scheduler):**
```python
from app.services.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    Base.metadata.create_all(bind=engine)
    
    # Start background scheduler
    try:
        start_scheduler()  # ← NEW: Start alert checking
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    logger.info(f"{settings.APP_NAME} started successfully")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    try:
        stop_scheduler()  # ← NEW: Stop scheduler gracefully
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
```

## Alert Model Usage

### Creating an Alert

```python
from datetime import datetime
from app.models.alert import Alert, AlertCondition
from app.db.session import SessionLocal

db = SessionLocal()

# Create alert
alert = Alert(
    user_id=1,
    stock_symbol="AAPL",
    condition=AlertCondition.GREATER_THAN,
    target_value=195.0,
    is_active=True,
)

db.add(alert)
db.commit()
```

### Checking Alert Conditions

```python
# Method 1: Using built-in model method
if alert.matches_condition(current_price=196.50):
    print("Condition matched!")

# Method 2: Manual checking
if alert.condition == AlertCondition.GREATER_THAN:
    if current_price > alert.target_value:
        print("Condition matched!")
```

### Alert Fields

```python
@dataclass
class Alert:
    id: int                          # Primary key
    user_id: int                     # Foreign key to User
    stock_symbol: str                # e.g., "AAPL"
    condition: AlertCondition        # >, <, >=, <=, %
    target_value: float              # Trigger threshold
    is_active: bool = True           # Whether to check
    created_at: datetime             # When created
    triggered_at: Optional[datetime] # When triggered (NULL if not triggered)
```

## Data Flow Example

### Complete Alert Lifecycle

```
1. USER ACTION
   └─ POST /api/alerts
      {stock_symbol: "AAPL", condition: ">", target_value: 195.0}

2. ALERT CREATED
   └─ Database: INSERT INTO alerts (...)
      Returns: {id: 5, user_id: 1, is_active: true, triggered_at: null}

3. SCHEDULER RUNS (30 seconds later)
   ├─ Fetch active alerts
   │  └─ SELECT * FROM alerts WHERE is_active = TRUE
   │     Result: 5 active alerts including our AAPL alert
   │
   ├─ Group by symbol: {AAPL: [alert_1, alert_5], MSFT: [alert_2], ...}
   │
   ├─ Fetch price for AAPL: yfinance.Ticker("AAPL").history()
   │  └─ Current Price: $196.50
   │
   ├─ Check alert_5 condition
   │  └─ 196.50 > 195.0? YES
   │
   └─ Trigger alert_5
      ├─ UPDATE alerts SET is_active=FALSE, triggered_at=NOW()
      │  WHERE id = 5
      │
      └─ Log: "🔔 ALERT TRIGGERED: AAPL > $195 @ $196.50"

4. ALERT TRIGGERED
   └─ Database: {id: 5, is_active: false, triggered_at: 2026-04-02 14:23:45}

5. USER CHECK
   └─ GET /api/alerts
      Returns: {id: 5, is_active: false, triggered_at: 2026-04-02 14:23:45}
```

## Error Handling Examples

### Network Error - yfinance Unavailable

```
Scheduler runs
  ├─ Fetch AAPL price → Network timeout
  │
  └─ LOG: "Error fetching price for symbol: AAPL (Connection timeout)"
     Result: Alerts for AAPL skipped this cycle
     
  ├─ Continue checking other symbols (MSFT, GOOGL, etc.)
  │
  └─ Next cycle: AAPL prices will be fetched again
```

### Database Error - Connection Lost

```
Trigger alert
  ├─ SET is_active = FALSE
  ├─ SET triggered_at = NOW()
  ├─ COMMIT → Database connection lost
  │
  └─ catch Exception:
     ├─ db.rollback()  # Undo changes
     ├─ LOG error
     └─ Return False
     
Result: Alert remains active, will be retried next cycle
```

### Duplicate Trigger Prevention

```
Trigger alert (first time)
  ├─ Check: alert.is_active? TRUE ✓
  ├─ Update database
  ├─ Commit success
  └─ Return True

Trigger alert (second time, 30 seconds later)
  ├─ Check: alert.is_active? FALSE ✗
  ├─ Skip update
  └─ Return False (deduped)
```

## Performance Optimization

### Query Optimization

```python
# Good: Fetch only active alerts, single query
active_alerts = db.query(Alert).filter(
    Alert.is_active == True  # ← Uses ix_alerts_is_active index
).all()

# Bad: Fetch all alerts, filter in Python
all_alerts = db.query(Alert).all()  # ← Loads entire table
active = [a for a in all_alerts if a.is_active]  # ← Filtering in Python
```

### Batching Optimization

```python
# Good: Group by symbol, fetch prices once
symbols = set(alert.stock_symbol for alert in active_alerts)
for symbol in symbols:
    price = fetch_price(symbol)  # ← 1 call per symbol
    alerts = [a for a in active_alerts if a.stock_symbol == symbol]
    for alert in alerts:
        if alert.matches_condition(price):
            trigger_alert(alert, price)

# Bad: Fetch price for each alert
for alert in active_alerts:
    price = fetch_price(alert.stock_symbol)  # ← N calls (duplicates)
    if alert.matches_condition(price):
        trigger_alert(alert, price)
```

## Testing Patterns

### Unit Test - Trigger Alert

```python
from app.services.alert_service import trigger_alert
from app.db.session import SessionLocal
from app.models.alert import Alert

def test_trigger_alert():
    db = SessionLocal()
    
    # Create alert
    alert = Alert(user_id=1, stock_symbol="AAPL", 
                  condition=">", target_value=195.0, is_active=True)
    db.add(alert)
    db.commit()
    
    # Trigger it
    result = trigger_alert(db, alert, 196.50)
    
    # Verify
    assert result == True
    assert alert.is_active == False
    assert alert.triggered_at is not None
    
    db.close()
```

### Integration Test - Full Cycle

```python
def test_alert_check_cycle():
    # Create alert with guaranteed trigger condition
    alert = create_alert(target_value=1.0)  # Always triggers
    
    # Run scheduler
    check_all_alerts()
    
    # Verify
    db = SessionLocal()
    updated = db.query(Alert).filter(Alert.id == alert.id).first()
    assert updated.is_active == False
    assert updated.triggered_at is not None
```

## Debugging Commands

### Check Scheduler Status
```python
from app.services.scheduler import is_scheduler_running, get_scheduler

# Is it running?
print(f"Running: {is_scheduler_running()}")

# Get details
scheduler = get_scheduler()
if scheduler:
    for job in scheduler.get_jobs():
        print(f"Job: {job.name}")
        print(f"  Next run: {job.next_run_time}")
        print(f"  Function: {job.func_ref}")
```

### Count Alerts
```python
from app.db.session import SessionLocal
from app.models.alert import Alert

db = SessionLocal()
active = db.query(Alert).filter(Alert.is_active == True).count()
triggered = db.query(Alert).filter(Alert.is_active == False).count()
print(f"Active: {active}, Triggered: {triggered}")
```

### Run Check Immediately
```python
from app.services.alert_service import check_all_alerts

# Force a check
check_all_alerts()

# Check logs for results
```

### Test Price Fetching
```python
import yfinance as yf

# Test yfinance
ticker = yf.Ticker("AAPL")
data = ticker.history(period="1d")
current_price = float(data["Close"].iloc[-1])
print(f"AAPL current price: ${current_price}")
```

## Common Patterns

### Creating Alerts Programmatically

```python
from app.models.alert import AlertCondition
from app.db.session import SessionLocal

def create_test_alerts(user_id: int, symbol: str, count: int = 5):
    """Create multiple test alerts for a symbol."""
    db = SessionLocal()
    
    for i in range(count):
        alert = Alert(
            user_id=user_id,
            stock_symbol=symbol,
            condition=AlertCondition.GREATER_THAN,
            target_value=100.0 + (i * 10),
            is_active=True,
        )
        db.add(alert)
    
    db.commit()
    db.close()
```

### Batch Trigger Alerts

```python
def trigger_all_alerts_for_symbol(symbol: str, price: float):
    """Trigger all active alerts for a symbol at given price."""
    db = SessionLocal()
    
    alerts = db.query(Alert).filter(
        Alert.stock_symbol == symbol,
        Alert.is_active == True,
    ).all()
    
    triggered = 0
    for alert in alerts:
        if alert.matches_condition(price):
            if trigger_alert(db, alert, price):
                triggered += 1
    
    print(f"Triggered {triggered}/{len(alerts)} alerts")
    db.close()
```

---

For complete documentation, see:
- **ALERT_SCHEDULER_README.md** - Overview & summary
- **ALERT_SCHEDULER_GUIDE.md** - Technical details
- **ALERT_SCHEDULER_TESTING.md** - Testing procedures
