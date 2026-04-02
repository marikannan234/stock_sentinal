# Alert System Documentation

## Overview

The **Alert System** for Stock Sentinel is a production-grade price monitoring solution that allows users to set custom price alerts for stocks. Alerts trigger when stock prices meet specified conditions and can be managed via REST APIs.

**Key Features:**
- ✅ Multiple condition types (>, <, >=, <=, percentage_change)
- ✅ Duplicate prevention
- ✅ Enable/disable alerts without deletion
- ✅ Stock price fetching with fallback mechanisms
- ✅ Comprehensive logging and error handling
- ✅ Database indexes for performance
- ✅ User authorization and data isolation
- ✅ Async support for scalability

---

## Database Schema

### Alerts Table

```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stock_symbol VARCHAR(16) NOT NULL,
    condition VARCHAR(50) NOT NULL,  -- Enum: >, <, >=, <=, percentage_change
    target_value FLOAT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP NULL,
    
    UNIQUE(user_id, stock_symbol, condition, target_value),
    INDEX(user_id, is_active),
    INDEX(stock_symbol),
    INDEX(user_id, stock_symbol)
);
```

### Key Constraints

| Constraint | Purpose |
|-----------|---------|
| `user_id` FK | Links alert to user; cascades on delete |
| `UNIQUE` Composite | Prevents duplicate alerts with same conditions |
| `Index (user_id, is_active)` | Fast retrieval of active user alerts |
| `Index (stock_symbol)` | Fast lookup by stock for batch checking |
| `Index (user_id, stock_symbol)` | Efficient symbol-based filtering |

---

## API Endpoints

### 1. Create Alert

**Endpoint:** `POST /api/alerts`

**Request:**
```json
{
    "stock_symbol": "AAPL",
    "condition": ">",
    "target_value": 150.50
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "user_id": 123,
    "stock_symbol": "AAPL",
    "condition": ">",
    "target_value": 150.50,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "triggered_at": null
}
```

**Error Codes:**
| Code | Reason |
|------|--------|
| 400 | Invalid input (negative price, invalid symbol) |
| 409 | Duplicate alert already exists |

**Implementation Details:**
- Stock symbol is automatically converted to uppercase
- Duplicate check prevents creating identical alerts
- `is_active` defaults to `true`

---

### 2. Get All Alerts

**Endpoint:** `GET /api/alerts`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "stock_symbol": "AAPL",
        "condition": ">",
        "target_value": 150.50,
        "is_active": true,
        "created_at": "2024-01-15T10:30:00Z",
        "triggered_at": null
    },
    {
        "id": 2,
        "stock_symbol": "MSFT",
        "condition": "<",
        "target_value": 300.00,
        "is_active": false,
        "created_at": "2024-01-14T15:20:00Z",
        "triggered_at": "2024-01-15T09:45:00Z"
    }
]
```

**Features:**
- Returns all alerts for authenticated user
- Ordered by creation date (newest first)
- Includes both active and inactive alerts

---

### 3. Get Single Alert

**Endpoint:** `GET /api/alerts/{alert_id}`

**Response (200 OK):**
```json
{
    "id": 1,
    "user_id": 123,
    "stock_symbol": "AAPL",
    "condition": ">",
    "target_value": 150.50,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "triggered_at": null
}
```

**Error Codes:**
| Code | Reason |
|------|--------|
| 404 | Alert not found |
| 403 | Unauthorized (alert belongs to another user) |

---

### 4. Get Alerts by Stock Symbol

**Endpoint:** `GET /api/alerts/symbol/{symbol}`

**Parameters:**
- `symbol`: Stock ticker (e.g., "AAPL", "msft")

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "stock_symbol": "AAPL",
        "condition": ">",
        "target_value": 150.00,
        "is_active": true,
        "created_at": "2024-01-15T10:30:00Z",
        "triggered_at": null
    },
    {
        "id": 3,
        "stock_symbol": "AAPL",
        "condition": "<",
        "target_value": 140.00,
        "is_active": true,
        "created_at": "2024-01-15T11:00:00Z",
        "triggered_at": null
    }
]
```

---

### 5. Update Alert Status

**Endpoint:** `PATCH /api/alerts/{alert_id}`

**Request:**
```json
{
    "is_active": false
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "stock_symbol": "AAPL",
    "condition": ">",
    "target_value": 150.50,
    "is_active": false,
    "created_at": "2024-01-15T10:30:00Z",
    "triggered_at": null
}
```

**Features:**
- Only supports toggling `is_active` status
- Preserves all other alert data
- Useful for temporarily pausing alerts without deletion

---

### 6. Delete Alert

**Endpoint:** `DELETE /api/alerts/{alert_id}`

**Response:** `204 No Content`

**Error Codes:**
| Code | Reason |
|------|--------|
| 404 | Alert not found |
| 403 | Unauthorized |

---

## Alert Conditions

### Supported Conditions

```python
class AlertCondition(str, Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    PERCENTAGE_CHANGE = "percentage_change"
```

### Examples

| Condition | Target | Description |
|-----------|--------|-------------|
| `>` | 150.50 | Trigger when price > $150.50 |
| `<` | 140.00 | Trigger when price < $140.00 |
| `>=` | 155.00 | Trigger when price ≥ $155.00 |
| `<=` | 145.00 | Trigger when price ≤ $145.00 |
| `percentage_change` | 5.0 | Trigger when price changes ≥ 5% |

---

## Alert Checking Logic

### Matching Conditions

```python
def matches_condition(self, current_price: float, previous_price: Optional[float] = None) -> bool:
    """Check if current price matches alert condition."""
    
    if condition == ">":
        return current_price > target_value
    elif condition == "<":
        return current_price < target_value
    elif condition == ">=":
        return current_price >= target_value
    elif condition == "<=":
        return current_price <= target_value
    elif condition == "percentage_change":
        pct_change = ((current_price - previous_price) / previous_price) * 100
        return abs(pct_change) >= target_value
```

### Triggering Alerts

1. **Check Alert:** Service fetches current price
2. **Match Condition:** Compare price against target using operator
3. **Mark as Triggered:** Set `triggered_at` timestamp if condition met
4. **Log Event:** Record in application logs
5. **Prevent Duplicates:** Once triggered, remains marked (won't re-trigger)

---

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def manage_alerts():
    client = httpx.AsyncClient()
    headers = {"Authorization": "Bearer YOUR_API_TOKEN"}
    base_url = "http://localhost:8000/api"
    
    # 1. Create alert
    alert_data = {
        "stock_symbol": "AAPL",
        "condition": ">",
        "target_value": 150.50
    }
    response = await client.post(
        f"{base_url}/alerts",
        json=alert_data,
        headers=headers
    )
    alert = response.json()
    alert_id = alert["id"]
    print(f"Alert created: {alert_id}")
    
    # 2. Get all alerts
    response = await client.get(f"{base_url}/alerts", headers=headers)
    all_alerts = response.json()
    print(f"Total alerts: {len(all_alerts)}")
    
    # 3. Get alerts for specific stock
    response = await client.get(
        f"{base_url}/alerts/symbol/AAPL",
        headers=headers
    )
    aapl_alerts = response.json()
    print(f"AAPL alerts: {len(aapl_alerts)}")
    
    # 4. Disable alert
    response = await client.patch(
        f"{base_url}/alerts/{alert_id}",
        json={"is_active": False},
        headers=headers
    )
    updated = response.json()
    print(f"Alert disabled: {updated['is_active']}")
    
    # 5. Delete alert
    response = await client.delete(
        f"{base_url}/alerts/{alert_id}",
        headers=headers
    )
    print(f"Alert deleted: {response.status_code == 204}")

asyncio.run(manage_alerts())
```

### cURL Examples

**Create Alert:**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "condition": ">",
    "target_value": 150.50
  }'
```

**Get All Alerts:**
```bash
curl http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update Alert Status:**
```bash
curl -X PATCH http://localhost:8000/api/alerts/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

**Delete Alert:**
```bash
curl -X DELETE http://localhost:8000/api/alerts/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Service Functions

### AlertService Class

```python
class AlertService:
    def __init__(self, db: Session):
        """Initialize with database session."""
    
    # CRUD Operations
    def create_alert(user: User, request: CreateAlertRequest) -> AlertResponse
    def get_alert(user: User, alert_id: int) -> AlertResponse
    def get_all_alerts_for_user(user: User) -> List[AlertResponse]
    def get_active_alerts_for_user(user: User) -> List[AlertResponse]
    def get_alerts_by_symbol(user: User, symbol: str) -> List[AlertResponse]
    def delete_alert(user: User, alert_id: int) -> None
    def update_alert_status(user: User, alert_id: int, request: UpdateAlertRequest) -> AlertResponse
    
    # Stock Price Fetching
    async def fetch_stock_price(symbol: str, timeout: int = 10) -> Optional[float]
    async def fetch_stock_price_with_httpx(symbol: str, timeout: int = 10) -> Optional[float]
    
    # Alert Checking
    async def check_alert(alert: Alert, current_price: float, previous_price: Optional[float]) -> bool
    async def check_all_user_alerts(user: User) -> Dict[int, bool]
    async def check_all_alerts_for_symbol(symbol: str) -> Dict[int, bool]
```

---

## Stock Price Fetching

### Primary Method: yfinance

```python
@staticmethod
async def fetch_stock_price(symbol: str, timeout: int = 10) -> Optional[float]:
    """
    Fetch stock price using yfinance.
    
    Advantages:
    - No API key required
    - Free and reliable
    - Covers all major exchanges
    
    Returns:
    - Current closing price
    - None if fetch fails
    """
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    return float(data["Close"].iloc[-1])
```

### Fallback Method: httpx + Alpha Vantage API

```python
@staticmethod
async def fetch_stock_price_with_httpx(symbol: str, timeout: int = 10) -> Optional[float]:
    """
    Fallback method using httpx client.
    
    Requirements:
    - Free API key from https://www.alphavantage.co/
    - Set in environment variables
    
    Returns:
    - Current quote price
    - None if fetch fails
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get("https://www.alphavantage.co/query", params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": os.getenv("ALPHAVANTAGE_API_KEY")
        })
        data = response.json()
        return float(data["Global Quote"]["05. price"])
```

---

## Logging

All alert operations are logged with structured logging:

### Log Events

```python
# Alert creation
logger.info("Alert created successfully", extra={
    "user_id": user.id,
    "alert_id": alert.id,
    "symbol": symbol,
    "condition": condition,
    "target_value": target_value,
})

# Alert triggered
logger.info("Alert triggered successfully", extra={
    "alert_id": alert.id,
    "user_id": alert.user_id,
    "symbol": alert.stock_symbol,
    "current_price": current_price,
})

# Alert deletion
logger.info("Alert deleted successfully", extra={
    "user_id": user.id,
    "alert_id": alert_id,
})

# Error during price fetch
logger.error("Failed to fetch stock price", extra={
    "symbol": symbol,
    "error": str(e),
    "error_type": type(e).__name__,
})
```

---

## Error Handling

### Exception Hierarchy

```
APIException (base)
├── ValidationError
│   └── InvalidAlertConditionError
├── NotFoundError
│   └── AlertNotFoundError
├── AuthorizationError
├── ConflictError
│   └── DuplicateAlertError
└── ExternalAPIError
```

### Common Errors

| HTTP Code | Error | When It Occurs |
|-----------|-------|----------------|
| 400 | Invalid Input | Negative price, empty symbol |
| 400 | Invalid Alert Condition | Unknown condition provided |
| 404 | Alert Not Found | Alert ID doesn't exist |
| 403 | Authorization Error | User accessing another's alert |
| 409 | Duplicate Alert | Same alert already exists |
| 502 | External API Error | Stock price fetch fails |

---

## Database Migrations

### Creating the alerts table

Run Alembic migration:

```bash
# Generate new migration
alembic revision --autogenerate -m "Add alerts table"

# Apply migration
alembic upgrade head
```

### Migration Example

```python
def upgrade():
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stock_symbol', sa.String(16), nullable=False),
        sa.Column('condition', sa.Enum(AlertCondition), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'stock_symbol', 'condition', 'target_value'),
    )
    op.create_index('ix_alerts_user_id_active', 'alerts', ['user_id', 'is_active'])
    op.create_index('ix_alerts_stock_symbol', 'alerts', ['stock_symbol'])
    op.create_index('ix_alerts_user_stock', 'alerts', ['user_id', 'stock_symbol'])
```

---

## Performance Optimization

### Indexes

| Index | Purpose | Query Performance |
|-------|---------|-------------------|
| `(user_id, is_active)` | Get user's active alerts | O(log n) |
| `(stock_symbol)` | Batch check by symbol | O(log n) |
| `(user_id, stock_symbol)` | Filter by user + symbol | O(log n) |

### Query Examples

```python
# Fast: Uses composite index
active_alerts = db.query(Alert).filter(
    Alert.user_id == user_id,
    Alert.is_active == True
).all()

# Fast: Uses symbol index for batch processing
symbol_alerts = db.query(Alert).filter(
    Alert.stock_symbol == symbol
).all()

# Efficient batch fetch
from sqlalchemy import or_
symbols = ["AAPL", "MSFT", "GOOGL"]
alerts = db.query(Alert).filter(
    Alert.stock_symbol.in_(symbols),
    Alert.is_active == True
).all()
```

---

## Best Practices

### For Alert Creation

1. **Validate inputs before creating** - Check stock_symbol format and target_value
2. **Prevent duplicates** - Check for existing alerts with same conditions
3. **Use uppercase symbols** - Normalize all stock symbols to uppercase
4. **Log all operations** - Record alerts created/deleted for audit trail

### For Alert Checking

1. **Batch fetch prices** - Group alerts by symbol to minimize API calls
2. **Handle API failures** - Implement fallback mechanisms
3. **Cache prices** - Store recent prices to avoid redundant API calls
4. **Log triggered alerts** - Record when conditions are met

### For User Experience

1. **Prevent accidental deletion** - Offer disable option before delete
2. **Show duplicate prevention** - Return 409 with helpful message
3. **Provide clear conditions** - Validate and explain alert conditions
4. **Return full object** - Return complete alert data after modifications

---

## Testing

### Unit Test Example

```python
import pytest
from app.models.alert import Alert, AlertCondition
from app.services.alert_service import AlertService

def test_create_alert(db_session, current_user):
    service = AlertService(db_session)
    request = CreateAlertRequest(
        stock_symbol="TEST",
        condition=AlertCondition.GREATER_THAN,
        target_value=100.0
    )
    alert = service.create_alert(current_user, request)
    
    assert alert.user_id == current_user.id
    assert alert.stock_symbol == "TEST"
    assert alert.target_value == 100.0
    assert alert.is_active is True

def test_duplicate_alert_prevention(db_session, current_user):
    service = AlertService(db_session)
    request = CreateAlertRequest(
        stock_symbol="TEST",
        condition=AlertCondition.GREATER_THAN,
        target_value=100.0
    )
    # Create first alert
    service.create_alert(current_user, request)
    
    # Creating duplicate should raise
    with pytest.raises(DuplicateAlertError):
        service.create_alert(current_user, request)

def test_condition_matching():
    alert = Alert(
        stock_symbol="TEST",
        condition=AlertCondition.GREATER_THAN,
        target_value=100.0
    )
    
    assert alert.matches_condition(101.0) is True
    assert alert.matches_condition(99.0) is False

def test_percentage_change_condition():
    alert = Alert(
        stock_symbol="TEST",
        condition=AlertCondition.PERCENTAGE_CHANGE,
        target_value=5.0
    )
    
    # 5% increase: (105 - 100) / 100 * 100 = 5%
    assert alert.matches_condition(105.0, previous_price=100.0) is True
    
    # 3% increase: (103 - 100) / 100 * 100 = 3%
    assert alert.matches_condition(103.0, previous_price=100.0) is False
```

---

## Future Enhancements

### Phase 2: Advanced Features

- [ ] **Email/SMS Notifications** - Send alerts to user via email/SMS
- [ ] **Webhook Support** - POST to user's endpoint when triggered
- [ ] **Alert History** - Track all triggered events
- [ ] **Recurring Alerts** - Auto-reset alerts after triggering
- [ ] **Complex Conditions** - Multiple conditions (AND/OR)
- [ ] **Portfolio Alerts** - Alert when portfolio value changes
- [ ] **Alert Templates** - Save and reuse alert configurations
- [ ] **Scheduled Checks** - Configurable check intervals using APScheduler

### Phase 3: ML Integration

- [ ] **Smart Suggestions** - ML-recommended alert values
- [ ] **Anomaly Detection** - Alert on unusual price movements
- [ ] **Trend-Based Alerts** - Alert based on trend changes

---

## File Structure

```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── alert.py          # Alert SQLAlchemy model
│   │   ├── user.py           # User model (updated with relationship)
│   │   └── ...
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── alert.py          # Pydantic schemas for alerts
│   │   └── ...
│   │
│   ├── services/
│   │   ├── alert_service.py  # Business logic for alerts
│   │   └── ...
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── alert.py      # Alert API endpoints
│   │   │   ├── auth.py
│   │   │   └── ...
│   │   ├── deps.py           # Dependencies (DB, auth)
│   │   └── ...
│   │
│   ├── core/
│   │   ├── exceptions.py     # Updated with alert exceptions
│   │   ├── logging_config.py
│   │   └── ...
│   │
│   └── main.py               # Updated with alert routes
│
└── requirements.txt          # Updated with dependencies
```

---

## Configuration

### Environment Variables

```bash
# .env file
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/stocksentinel
JWT_SECRET_KEY=your-secret-key
FINNHUB_API_KEY=your-finnhub-key
ALPHAVANTAGE_API_KEY=your-alphavantage-key  # For fallback price fetching
ENVIRONMENT=development
DEBUG=True
```

---

## Summary

The Alert System provides a **production-ready** solution for stock price monitoring with:

✅ **Complete REST API** - Full CRUD operations  
✅ **Robust Error Handling** - Custom exceptions with proper HTTP codes  
✅ **Structured Logging** - All operations logged for debugging  
✅ **User Authorization** - Alerts isolated per user  
✅ **Performance Optimized** - Database indexes and efficient queries  
✅ **Scalable Architecture** - Async functions for concurrent operations  
✅ **Extensible Design** - Easy to add notifications and webhooks  

---

**Last Updated:** 2026-04-01  
**Version:** 1.0.0  
**Status:** Production Ready ✅
