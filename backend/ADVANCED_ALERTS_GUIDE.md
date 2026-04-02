# Advanced Alert System - Complete Guide

## Overview

The Stock Sentinel alert system has been extended to support multiple alert types, enabling sophisticated monitoring strategies beyond simple price thresholds.

## Alert Types

### 1. **PRICE Alert** (Simple Price Threshold)

Monitor when stock price crosses a threshold using comparison operators.

**When to use:**
- Simple price targets
- Basic buy/sell points
- Quick alerts

**Configuration:**
```json
{
  "stock_symbol": "AAPL",
  "alert_type": "price",
  "condition": ">",
  "target_value": 150.00
}
```

**Supported Conditions:**
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal

**Example Triggers:**
- Alert set: AAPL > 150.00
- Current price: 151.50 → ✅ **TRIGGERED**
- Current price: 149.99 → ❌ Not triggered

---

### 2. **PERCENTAGE_CHANGE Alert** (Relative Price Movement)

Monitor percentage change from the last recorded price. Useful for detecting significant moves relative to the stock's typical movement.

**When to use:**
- Track significant gains/losses
- Portfolio rebalancing triggers
- Momentum-based alerts
- Stable vs volatile stocks
- Stocks with different price ranges

**Configuration:**
```json
{
  "stock_symbol": "AAPL",
  "alert_type": "percentage_change",
  "condition": ">",
  "target_value": 5.0
}
```

**How it works:**
```
Percentage Change = ((current_price - last_price) / last_price) × 100

Alert triggers if: |percentage_change| >= target_value
```

**Update Logic:**
- `last_price` is updated after every check
- First check: `last_price` is set to current price (establishes baseline)
- Subsequent checks: Compare against previous price

**Example Scenarios:**

**Scenario 1: Upward Movement**
```
Last Price: $100.00
Current Price: $105.50
Percentage Change: 5.5%
Alert Target: 5.0%

Result: ✅ TRIGGERED (5.5% >= 5.0%)
```

**Scenario 2: Downward Movement (uses absolute value)**
```
Last Price: $100.00
Current Price: $94.50
Percentage Change: -5.5% (absolute: 5.5%)
Alert Target: 5.0%

Result: ✅ TRIGGERED (|-5.5%| = 5.5% >= 5.0%)
```

---

### 3. **VOLUME_SPIKE Alert** (Unusual Trading Activity)

Detect when trading volume exceeds normal levels, indicating unusual market activity.

**When to use:**
- Detect institutional buying/selling
- Q4 earnings surprises
- Corporate announcements
- Unusual options activity
- Pump and dump detection

**Configuration:**
```json
{
  "stock_symbol": "AAPL",
  "alert_type": "volume_spike",
  "condition": ">",
  "target_value": 1.5
}
```

**How it works:**
```
threshold_volume = average_volume × target_value

Alert triggers if: current_volume > threshold_volume

Average Volume = 20-day average (excludes today)
```

**Example Scenarios:**

**Scenario 1: 50% Above Average**
```
20-Day Average Volume: 50,000,000 shares
Current Volume: 75,000,000 shares
Alert Threshold: 1.5x (75,000,000 target)

Result: ✅ TRIGGERED (75M > 75M threshold)
```

**Scenario 2: Below Spike Threshold**
```
20-Day Average Volume: 50,000,000 shares
Current Volume: 60,000,000 shares
Alert Threshold: 1.5x (75,000,000 target)

Result: ❌ Not triggered (60M < 75M threshold)
```

**Common Multiplier Values:**
- `1.2` - 20% above normal (conservative)
- `1.5` - 50% above normal (moderate)
- `2.0` - Double normal volume (aggressive)
- `3.0` - Triple volume (extreme spike)

---

### 4. **CRASH Alert** (Sudden Price Drop Detection)

Detect rapid price declines to trigger protective actions.

**When to use:**
- Stop-loss protection
- Downside risk alerts
- Market correction monitoring
- Gap-down detection
- Portfolio protection

**Configuration:**
```json
{
  "stock_symbol": "AAPL",
  "alert_type": "crash",
  "condition": "<",
  "target_value": 5.0
}
```

**How it works:**
```
percentage_change = ((current_price - last_price) / last_price) × 100

Alert triggers if: percentage_change <= -target_value
```

**Note:** `target_value` is specified as positive (5.0 means -5% drop).

**Update Logic:**
- `last_price` is updated after every check
- First check: `last_price` is set to current price
- Subsequent checks: Compare against previous price

**Example Scenarios:**

**Scenario 1: Sharp Down Move**
```
Last Price: $100.00
Current Price: $94.00
Percentage Change: -6.0%
Alert Target: 5.0%

Result: ✅ TRIGGERED (-6.0% <= -5.0%)
```

**Scenario 2: Small Down Move**
```
Last Price: $100.00
Current Price: $96.50
Percentage Change: -3.5%
Alert Target: 5.0%

Result: ❌ Not triggered (-3.5% > -5.0%)
```

**Scenario 3: Up Move (no trigger on gains)**
```
Last Price: $100.00
Current Price: $102.00
Percentage Change: +2.0%
Alert Target: 5.0%

Result: ❌ Not triggered (+2.0% > -5.0%)
```

---

### 5. **CUSTOM Alert** (Extensible Framework)

Foundation for implementing custom monitoring logic. Currently delegates to price threshold checks but can be extended.

**When to use:**
- Complex multi-factor conditions
- Technical analysis rules
- Custom indicators
- Proprietary strategies

**Configuration:**
```json
{
  "stock_symbol": "AAPL",
  "alert_type": "custom",
  "condition": ">",
  "target_value": 150.00
}
```

**Current Behavior:** Identical to PRICE alert

**Future Extensions:** Can be modified to support:
- Multiple moving averages
- RSI/MACD thresholds
- Sector correlation
- Options implied volatility
- Custom scoring models

---

## Implementation Details

### Database Schema

**alerts table:**
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stock_symbol VARCHAR(16) NOT NULL,
    alert_type alerttype NOT NULL DEFAULT 'price',
    condition alertcondition NOT NULL DEFAULT '>',
    target_value FLOAT NOT NULL,
    last_price FLOAT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT NOW(),
    triggered_at DATETIME NULL,
    
    UNIQUE (user_id, stock_symbol, alert_type, condition, target_value),
    INDEX ix_alerts_user_id_active (user_id, is_active),
    INDEX ix_alerts_alert_type (alert_type)
);
```

**Enum Types:**
```sql
-- AlertType enum
CREATE TYPE alerttype AS ENUM (
    'price',
    'percentage_change',
    'volume_spike',
    'crash',
    'custom'
);

-- AlertCondition enum
CREATE TYPE alertcondition AS ENUM (
    'greater_than',
    'less_than',
    'greater_than_or_equal',
    'less_than_or_equal',
    'percentage_change'
);
```

### Model Methods

**Alert Model** (`app/models/alert.py`):

```python
# Type-specific check methods
alert.check_price_alert(current_price: float) -> bool
alert.check_percentage_change_alert(current_price: float) -> bool
alert.check_volume_spike_alert(current_volume: float, avg_volume: float) -> bool
alert.check_crash_alert(current_price: float) -> bool
alert.check_custom_alert(current_price: float) -> bool

# Unified dispatcher
alert.check_alert(
    current_price: float,
    avg_volume: Optional[float] = None,
    current_volume: Optional[float] = None
) -> bool
```

### Background Scheduler

**check_all_alerts()** function runs every 30 seconds:

```python
1. Fetch all active alerts from database
2. Group by symbol for efficient batch processing
3. Fetch current price & 20-day volume data via yfinance
4. Calculate average volume (20-day, excluding today)
5. For each alert:
   - Dispatch to appropriate check method based on type
   - Trigger alert if condition matches
   - Update last_price for percentage/crash alerts
6. Log detailed statistics per alert type
```

**Performance:**
- Single yfinance call per symbol (all alerts grouped)
- Batched database updates
- Error isolation (one symbol error doesn't stop others)
- Comprehensive logging for debugging

---

## API Reference

### Create Alert

**Endpoint:** `POST /api/alerts`

**Request:**
```json
{
  "stock_symbol": "AAPL",
  "alert_type": "percentage_change",
  "condition": ">",
  "target_value": 5.0
}
```

**Response:**
```json
{
  "id": 42,
  "user_id": 1,
  "stock_symbol": "AAPL",
  "alert_type": "percentage_change",
  "condition": ">",
  "target_value": 5.0,
  "last_price": null,
  "is_active": true,
  "created_at": "2026-04-02T10:30:00",
  "triggered_at": null
}
```

### Get Alert

**Endpoint:** `GET /api/alerts/{alert_id}`

**Response:** (same as above)

### List User Alerts

**Endpoint:** `GET /api/alerts`

**Query Parameters:**
- `is_active` - Filter by active status (optional)

**Response:**
```json
[
  {
    "id": 42,
    "stock_symbol": "AAPL",
    "alert_type": "percentage_change",
    ...
  },
  {
    "id": 43,
    "stock_symbol": "MSFT",
    "alert_type": "volume_spike",
    ...
  }
]
```

### Delete Alert

**Endpoint:** `DELETE /api/alerts/{alert_id}`

**Response:** `204 No Content`

---

## Usage Examples

### Example 1: Catch Momentum (5% moves)

```json
POST /api/alerts
{
  "stock_symbol": "TSLA",
  "alert_type": "percentage_change",
  "condition": ">",
  "target_value": 5.0
}
```

**Triggers when:** TSLA moves 5% (up or down) from last check

---

### Example 2: Stop Loss (10% drop)

```json
POST /api/alerts
{
  "stock_symbol": "AAPL",
  "alert_type": "crash",
  "condition": "<",
  "target_value": 10.0
}
```

**Triggers when:** AAPL drops 10% or more from last check

---

### Example 3: Unusual Activity (3x volume)

```json
POST /api/alerts
{
  "stock_symbol": "GOOGL",
  "alert_type": "volume_spike",
  "condition": ">",
  "target_value": 3.0
}
```

**Triggers when:** GOOGL volume exceeds 3x the 20-day average

---

### Example 4: Price Target (simple)

```json
POST /api/alerts
{
  "stock_symbol": "MSFT",
  "alert_type": "price",
  "condition": ">=",
  "target_value": 350.00
}
```

**Triggers when:** MSFT reaches $350 or higher

---

## Field Descriptions

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `stock_symbol` | string | ✅ | - | 1-16 chars, uppercase |
| `alert_type` | enum | ✅ | "price" | price, percentage_change, volume_spike, crash, custom |
| `condition` | enum | ✅ | ">" | >, <, >=, <= |
| `target_value` | float | ✅ | - | Must be positive |
| `last_price` | float | ❌ | null | Auto-updated for percentage_change/crash |
| `is_active` | bool | ❌ | true | Disabled after trigger |
| `created_at` | datetime | ❌ | now() | Auto-set |
| `triggered_at` | datetime | ❌ | null | Auto-set when triggered |

---

## Data Flow Diagram

```
Background Scheduler (30s interval)
    ↓
check_all_alerts()
    ├─ Fetch active alerts
    ├─ Group by symbol
    ├─ For each symbol:
    │   ├─ Fetch price & volume via yfinance
    │   ├─ Calculate 20-day avg volume
    │   └─ For each alert:
    │       ├─ Route to check_alert() by type
    │       ├─ Check condition
    │       ├─ Update last_price if needed
    │       └─ Trigger if matched
    ├─ Email notification (if enabled)
    └─ Log statistics
```

## Testing

### Manual Test: Create Percentage Change Alert

```bash
# 1. Start app
uvicorn app.main:app --reload

# 2. Create alert via Swagger UI at /docs
POST /api/alerts
{
  "stock_symbol": "AAPL",
  "alert_type": "percentage_change",
  "condition": ">",
  "target_value": 1.0
}

# 3. Wait 30-60 seconds for scheduler
# 4. Monitor logs for trigger event
# 5. Check email for notification
```

### View Logs

```bash
tail -f backend/logs/app.log | grep -E "Alert|trigger|percentage"
```

**Expected output:**
```
[INFO] Starting alert check cycle
[DEBUG] Fetched data for symbol: AAPL, current_price: 175.50
[INFO] 🔔 ALERT TRIGGERED - percentage_change detected
[INFO] Email notification queued
[INFO] Alert check cycle completed
```

---

## Production Considerations

### Performance

- **Query optimization:** Composite indexes on (user_id, is_active)
- **Batch processing:** One yfinance call per symbol
- **Error isolation:** Failures don't cascade
- **Logging:** Structured logs for monitoring

### Reliability

- **No duplicate triggers:** `is_active` flag prevents re-triggering
- **Error handling:** All exceptions caught and logged
- **Database session:** Proper cleanup in finally block
- **Email failures:** Don't crash alert system

### Monitoring

Monitor these logs in production:

```bash
# Alert triggers
grep "ALERT TRIGGERED" app.log

# Email failures
grep "Failed to send" app.log | grep -i email

# Scheduler health
grep "Alert check cycle completed" app.log
```

### Future Enhancements

1. **User Preferences**
   - Enable/disable per alert
   - Custom notification frequency
   - Digest emails (hourly/daily)

2. **Advanced Checks**
   - Multiple condition combinations (AND/OR)
   - Custom technical indicators
   - Correlation with other stocks
   - Sector-based alerts

3. **Notification Channels**
   - SMS via Twilio
   - Webhook delivery
   - Slack/Discord
   - Mobile push notifications

4. **Analytics**
   - Alert accuracy tracking
   - Win rate per alert type
   - Performance dashboards
   - Alert statistics per user

---

## Troubleshooting

### Alert Not Triggering

**Check:**
1. Alert is active: `is_active = true`
2. Scheduler is running: Check logs for "Alert check cycle"
3. Price data available: `grep "Fetched data" app.log`
4. Condition logic: Test with extreme values
5. Database connection: Check if writes are persisting

**Debug:**
```bash
# Manually test alert logic
python -c "
from app.models.alert import Alert, AlertType
from app.services.alert_service import check_all_alerts

# Run scheduler immediately
check_all_alerts()
"
```

### Email Not Received

**Check:**
1. Email enabled: `ENABLE_EMAIL_NOTIFICATIONS=True`
2. User has email: `SELECT email FROM users WHERE id = ?`
3. Gmail settings: Check credentials password
4. View logs: `grep -i email app.log`

**Enable debug logging:**
```python
# Add to app/core/logging_config.py
logging.getLogger("fastapi_mail").setLevel(logging.DEBUG)
```

### High Database Load

**Optimize:**
1. Archive triggered alerts
2. Increase check interval (if acceptable)
3. Add data retention policy
4. Monitor query performance

---

## Summary

The advanced alert system provides:

✅ **Multiple alert types** for diverse monitoring strategies  
✅ **Efficient processing** with batched data fetching  
✅ **Automatic updates** of tracking fields (last_price)  
✅ **Robust error handling** with email notifications  
✅ **Production-ready** logging and monitoring  
✅ **Extensible architecture** for future enhancements  

Start using advanced alerts today! 🚀
