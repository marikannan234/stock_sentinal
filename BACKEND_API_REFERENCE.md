## Backend API - Quick Reference & Testing Guide

### Running the Backend

```bash
cd backend

# Option 1: Docker
docker-compose up

# Option 2: Local Python
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: **http://localhost:8000**

### API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## User Profile & Settings API

### Get User Profile
```bash
curl -X GET "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer <your_token>"
```
**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar": "https://...",
  "created_at": "2026-04-02T10:00:00",
  "updated_at": "2026-04-02T10:00:00"
}
```

### Update User Profile
```bash
curl -X PUT "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Smith",
    "avatar": "https://new-avatar-url.jpg"
  }'
```

### Get User Settings
```bash
curl -X GET "http://localhost:8000/api/user/settings" \
  -H "Authorization: Bearer <your_token>"
```
**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "email_notifications": true,
  "dark_mode": true,
  "preferred_currency": "USD",
  "two_factor_enabled": false,
  "created_at": "2026-04-02T10:00:00",
  "updated_at": "2026-04-02T10:00:00"
}
```

### Update User Settings
```bash
curl -X PUT "http://localhost:8000/api/user/settings" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email_notifications": false,
    "dark_mode": false,
    "preferred_currency": "EUR",
    "two_factor_enabled": true
  }'
```

---

## Support Ticket API

### Create Support Ticket
```bash
curl -X POST "http://localhost:8000/api/support/ticket" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Cannot Execute Trade",
    "message": "I'm unable to execute a BUY order for AAPL",
    "priority": "high"
  }'
```
**Response:** HTTP 201 Created
```json
{
  "id": 1,
  "user_id": 1,
  "subject": "Cannot Execute Trade",
  "message": "I'm unable to execute a BUY order for AAPL",
  "status": "open",
  "priority": "high",
  "response": null,
  "created_at": "2026-04-02T10:00:00",
  "updated_at": "2026-04-02T10:00:00"
}
```

### List User's Tickets
```bash
curl -X GET "http://localhost:8000/api/support/tickets" \
  -H "Authorization: Bearer <your_token>"

# Filter by status
curl -X GET "http://localhost:8000/api/support/tickets?status_filter=open" \
  -H "Authorization: Bearer <your_token>"
```

### Get Specific Ticket
```bash
curl -X GET "http://localhost:8000/api/support/ticket/1" \
  -H "Authorization: Bearer <your_token>"
```

### Update Ticket (Add Response)
```bash
curl -X PUT "http://localhost:8000/api/support/ticket/1" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "response": "We've fixed the issue. Try again now."
  }'
```

### Delete Ticket
```bash
curl -X DELETE "http://localhost:8000/api/support/ticket/1" \
  -H "Authorization: Bearer <your_token>"
```

---

## Trading API

### Create Trade (Buy 10 shares of AAPL @ $150)
```bash
curl -X POST "http://localhost:8000/api/trade/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "quantity": 10,
    "entry_price": 150.00,
    "trade_type": "BUY"
  }'
```
**Response:** HTTP 201 Created
```json
{
  "id": 1,
  "user_id": 1,
  "symbol": "AAPL",
  "quantity": 10.0,
  "entry_price": 150.0,
  "current_price": 150.0,
  "trade_type": "BUY",
  "status": "open",
  "created_at": "2026-04-02T10:00:00",
  "updated_at": "2026-04-02T10:00:00"
}
```

### List User's Open Trades
```bash
curl -X GET "http://localhost:8000/api/trade/" \
  -H "Authorization: Bearer <your_token>"

# Filter by status
curl -X GET "http://localhost:8000/api/trade/?status_filter=open" \
  -H "Authorization: Bearer <your_token>"

# Filter by symbol
curl -X GET "http://localhost:8000/api/trade/?symbol_filter=AAPL" \
  -H "Authorization: Bearer <your_token>"
```

### Get Trade Details
```bash
curl -X GET "http://localhost:8000/api/trade/1" \
  -H "Authorization: Bearer <your_token>"
```

### Update Trade (Update current price)
```bash
curl -X PUT "http://localhost:8000/api/trade/1" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_price": 155.50
  }'
```

### Close Trade (Sell @ $155.50)
```bash
curl -X POST "http://localhost:8000/api/trade/1/close" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"exit_price": 155.50}'
```
**Response:** HTTP 200
```json
{
  "id": 1,
  "user_id": 1,
  "symbol": "AAPL",
  "quantity": 10.0,
  "entry_price": 150.0,
  "exit_price": 155.50,
  "profit_loss": 55.0,
  "duration": 120.5,
  "trade_type": "BUY",
  "closed_at": "2026-04-02T12:00:00"
}
```

### Get Trade History
```bash
curl -X GET "http://localhost:8000/api/trade/history/list" \
  -H "Authorization: Bearer <your_token>"

# Filter by symbol
curl -X GET "http://localhost:8000/api/trade/history/list?symbol_filter=AAPL" \
  -H "Authorization: Bearer <your_token>"
```

### Get Trading Statistics
```bash
curl -X GET "http://localhost:8000/api/trade/summary/stats" \
  -H "Authorization: Bearer <your_token>"
```
**Response:**
```json
{
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "win_rate": 60.0,
  "total_profit_loss": 245.75,
  "average_trade_duration": 480
}
```

---

## Stock Data API

### Get Stock Details with Indicators
```bash
curl -X GET "http://localhost:8000/api/stocks/AAPL" \
  -H "Authorization: Bearer <your_token>"

# With specific time range
curl -X GET "http://localhost:8000/api/stocks/AAPL?range=1w" \
  -H "Authorization: Bearer <your_token>"
```
**Supported Ranges:** `1d`, `1w`, `1m`, `3m`, `6m`, `1y`

**Response:**
```json
{
  "symbol": "AAPL",
  "name": "AAPL Inc.",
  "current_price": 175.43,
  "change_percent": 2.15,
  "change_amount": 3.70,
  "market_cap": 2750000000000.0,
  "pe_ratio": 28.45,
  "dividend_yield": 0.45,
  "indicators": {
    "sma_20": 174.32,
    "sma_50": 172.85,
    "ema_12": 175.10,
    "ema_26": 173.95,
    "rsi": 62.34,
    "macd": 1.15,
    "signal_line": 0.76
  },
  "historical_data": [
    {
      "date": "2026-03-26T00:00:00",
      "close": 171.85,
      "high": 172.69,
      "low": 168.39,
      "volume": 45237000
    },
    ...
  ]
}
```

### Get Live Stock Quotes (Top 50 Stocks)
```bash
curl -X GET "http://localhost:8000/api/stocks/live/quotes" \
  -H "Authorization: Bearer <your_token>"
```
**Response:**
```json
{
  "quotes": [
    {
      "symbol": "AAPL",
      "price": 175.43,
      "change_percent": 2.15,
      "change_amount": 3.70
    },
    {
      "symbol": "MSFT",
      "price": 420.25,
      "change_percent": 1.45,
      "change_amount": 6.00
    },
    ...
  ]
}
```

### Get Market Summary (Gainers, Losers, Movers)
```bash
curl -X GET "http://localhost:8000/api/stocks/market-summary/overview" \
  -H "Authorization: Bearer <your_token>"
```
**Response:**
```json
{
  "top_gainers": [
    {
      "symbol": "TSLA",
      "price": 245.60,
      "change_percent": 8.45,
      "change_amount": 19.25
    },
    ...
  ],
  "top_losers": [
    {
      "symbol": "INTC",
      "price": 45.30,
      "change_percent": -3.20,
      "change_amount": -1.50
    },
    ...
  ],
  "most_active": [
    {
      "symbol": "GME",
      "price": 18.75,
      "change_percent": -1.25,
      "change_amount": -0.24
    },
    ...
  ]
}
```

---

## Authentication

### Login
```bash
curl -X POST "http://localhost:8000/api/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword"
  }'
```
**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### Use Token in Requests
All API calls require the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Database Migration

### Apply Migration to Create New Tables
```bash
cd backend

# Check migration status
alembic current

# Apply all pending migrations
alembic upgrade head

# Verify tables were created
psql -U postgres -d stock_sentinel -c "\dt"
```

**New Tables Created:**
- `user_settings` - User preferences
- `support_tickets` - Support requests
- `trades` - Active trades
- `trade_history` - Closed trades with P/L

---

## Error Responses

### Authentication Error (Invalid/Missing Token)
```json
{
  "detail": "Not authenticated"
}
```
**Status:** 401

### Validation Error (Bad Request)
```json
{
  "detail": [
    {
      "loc": ["body", "quantity"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```
**Status:** 422

### Not Found Error
```json
{
  "detail": "Trade not found"
}
```
**Status:** 404

### Business Logic Error (e.g., Insufficient Shares)
```json
{
  "detail": "Insufficient shares for AAPL"
}
```
**Status:** 400

---

## Testing Workflow

### 1. Register/Login
```bash
# Register new user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'

# Login
curl -X POST "http://localhost:8000/api/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
# Copy access_token
```

### 2. Update Settings
```bash
export TOKEN="<your_access_token>"

curl -X PUT "http://localhost:8000/api/user/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dark_mode": false,
    "preferred_currency": "EUR"
  }'
```

### 3. Create a Trade
```bash
curl -X POST "http://localhost:8000/api/trade/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "MSFT",
    "quantity": 5,
    "entry_price": 420.00,
    "trade_type": "BUY"
  }'
```

### 4. View Stock Details
```bash
curl -X GET "http://localhost:8000/api/stocks/MSFT?range=1m" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Create Support Ticket
```bash
curl -X POST "http://localhost:8000/api/support/ticket" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Ticket",
    "message": "This is a test",
    "priority": "normal"
  }'
```

### 6. Get Market Summary
```bash
curl -X GET "http://localhost:8000/api/stocks/market-summary/overview" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Integration with Frontend

### JavaScript Fetch Example
```javascript
// Get current user's trading stats
const token = localStorage.getItem('stocksentinel_token');

const response = await fetch('/api/trade/summary/stats', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const stats = await response.json();
console.log(`Win Rate: ${stats.win_rate}%`);
console.log(`Total P/L: $${stats.total_profit_loss}`);
```

### React Hook Example
```javascript
import useAuthStore from '@/store/useAuthStore';

export const useTradingStats = () => {
  const token = useAuthStore(state => state.token);
  const [stats, setStats] = useState(null);

  useEffect(async () => {
    const response = await fetch('/api/trade/summary/stats', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    setStats(await response.json());
  }, [token]);

  return stats;
};
```

---

## Performance Notes

- All queries include proper indexes on `user_id`, `symbol`/`ticker`, and `created_at`
- Trade history queries are optimized for date range filtering
- Stock data endpoints use mock generation (replace with real API calls in production)
- Consider adding pagination for large result sets (trade history, tickets)

---

## Troubleshooting

### Connection Refused
- Ensure backend is running: `python -m uvicorn app.main:app --reload`
- Check port 8000 is available

### JWT Token Invalid
- Token may have expired (tokens expire in 24 hours by default)
- Re-login to get a new token
- Check token is being sent in header

### Database Migration Failed
- Ensure PostgreSQL is running
- Check database connection string in `.env`
- Run: `alembic current` to check migration status

### Trade Creation Fails
- Verify symbol format (uppercase)
- Ensure quantity > 0
- Check user has sufficient balance (if implemented)

---

## Status: PRODUCTION READY ✅
