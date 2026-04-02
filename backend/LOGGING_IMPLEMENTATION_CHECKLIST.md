# Production-Level Logging & Error Handling - Implementation Checklist

## ✅ Files Created (Ready to Use)

All the following files have been created for you. No manual creation needed!

### Core Modules
- [x] `backend/app/core/logging_config.py` - Centralized logging configuration
- [x] `backend/app/core/exceptions.py` - Custom exception classes  
- [x] `backend/app/core/error_handlers.py` - Middleware & global exception handlers
- [x] `backend/app/schemas/error_responses.py` - Standardized error response schemas
- [x] `backend/app/main.py` - Updated with logging integration

### Examples & Documentation
- [x] `backend/app/api/routes/example_error_handling.py` - Example routes showing best practices
- [x] `backend/LOGGING_ERROR_HANDLING_GUIDE.md` - Complete implementation guide

---

## 🚀 Implementation Steps

### Step 1: Verify Setup (5 minutes)
```bash
# 1. Navigate to backend
cd backend

# 2. Check that new files exist
ls -la app/core/logging_config.py
ls -la app/core/exceptions.py
ls -la app/core/error_handlers.py

# 3. Start the application
uvicorn app.main:app --reload

# 4. In another terminal, test
curl http://localhost:8000/api/health

# 5. Check logs created
ls -la logs/
tail logs/app.log
```

**Expected Output:**
```
✅ Application started
✅ Logs directory created
✅ Log files appear (app.log, errors.log, access.log)
✅ Colored output in console
```

### Step 2: Test Example Routes (10 minutes)
```bash
# Test successful request
curl "http://localhost:8000/api/example/stock/RELIANCE/simple"

# Test validation error
curl "http://localhost:8000/api/example/stock/INVALID/simple"

# View logs
tail -f logs/app.log
```

### Step 3: Update Existing Routes (Per route, 5-10 minutes each)

For each route in your application:

1. Add imports at the top:
```python
from app.core.logging_config import get_logger
from app.core.exceptions import (
    ValidationError,
    StockNotFoundError,
    ExternalAPIError,
)

logger = get_logger(__name__)
```

2. Replace generic exceptions:
```python
# OLD
raise HTTPException(status_code=404, detail="Not found")

# NEW
raise StockNotFoundError(ticker)
```

3. Add logging:
```python
# At start of route
logger.info(f"Processing {identifier}", extra={"id": identifier})

# On success
logger.info(f"Successfully processed {identifier}")

# On error
logger.error(f"Error: {error_message}", exc_info=exc)
```

4. Wrap in try-except:
```python
try:
    # Your code
    pass
except (StockNotFoundError, ValidationError):
    raise  # Let global handler catch it
except Exception as exc:
    logger.error(f"Error: {str(exc)}", exc_info=exc)
    raise ExternalAPIError(message=str(exc))
```

---

## 📋 Quick Reference: Exception Classes

### For 400 Bad Request Errors
```python
from app.core.exceptions import (
    ValidationError,        # Generic validation error
    InvalidTickerError,     # Invalid ticker format
    RateLimitError,         # Rate limit exceeded
)

# Usage
raise ValidationError("Invalid input", details={"field": "email"})
raise InvalidTickerError("INVALID123")
raise RateLimitError()
```

### For 401/403 Auth Errors
```python
from app.core.exceptions import (
    AuthenticationError,       # Generic auth error
    TokenExpiredError,         # JWT token expired
    InvalidCredentialsError,   # Wrong password
    AuthorizationError,        # No permission
)

# Usage
raise InvalidCredentialsError()
raise TokenExpiredError()
raise AuthorizationError("You don't have permission")
```

### For 404 Not Found Errors
```python
from app.core.exceptions import (
    NotFoundError,           # Generic not found
    StockNotFoundError,      # Stock doesn't exist
)

# Usage
raise StockNotFoundError("RELIANCE")
raise NotFoundError("User not found", details={"user_id": 123})
```

### For 409 Conflict Errors
```python
from app.core.exceptions import ConflictError

# Usage
raise ConflictError("User already exists", details={"email": "user@example.com"})
```

### For 502 External API Errors
```python
from app.core.exceptions import ExternalAPIError

# Usage
raise ExternalAPIError(
    "Failed to fetch from YFinance",
    details={"service": "yfinance", "status": 503}
)
```

### For 500 Server Errors
```python
from app.core.exceptions import (
    APIException,       # Generic server error
    DatabaseError,      # Database failure
)

# Usage
raise DatabaseError("Failed to save to database")
raise APIException("Something went wrong")
```

---

## 🔍 Logging Quick Reference

### Log Levels
```python
logger.debug("msg")    # Detailed, verbose, development only
logger.info("msg")     # Normal operations, important events
logger.warning("msg")  # Warning conditions, might need attention
logger.error("msg")    # Error conditions, something failed
logger.critical("msg") # Critical, system may crash
```

### Common Patterns
```python
# Log with extra context
logger.info(f"User {user_id} logged in", extra={"user_id": user_id})

# Log with exception details
logger.error("Query failed", exc_info=exc)

# Log performance
logger.info(f"Request completed in {time_ms}ms")

# Log security events
logger.warning(f"Failed login attempt for {email}")

# Debug detailed info
logger.debug(f"Query: {sql_query}, Params: {params}")
```

---

## ✨ What You Get

### 1. Automatic Log Rotation
```
app.log          (current logs)
app.log.1        (older logs)
app.log.2        (even older)
...
app.log.10       (oldest kept)
```

### 2. Console + File Logging
- **Console**: INFO level, colored output (during development)
- **File (app.log)**: DEBUG level, all logs
- **File (errors.log)**: ERROR level, errors only
- **File (access.log)**: Access logs for HTTP requests

### 3. Standardized Error Responses
```json
{
  "error": {
    "code": "STOCK_NOT_FOUND",
    "message": "Stock 'INVALID' not found",
    "details": {
      "ticker": "INVALID"
    }
  }
}
```

### 4. Request Tracking
```
[2026-04-01 10:30:45] [INFO] → GET /api/stock/RELIANCE/quote
[2026-04-01 10:30:46] [INFO] ← ✅ GET /api/stock/RELIANCE/quote - 200 (120ms)
```

### 5. Performance Monitoring
```
[2026-04-01 10:31:00] [WARNING] Slow response: GET /api/stock/... took 1.25s
```

---

## 🧪 Testing Checklist

### Unit Test Example
```python
def test_stock_not_found():
    """Test that StockNotFoundError is raised for invalid ticker."""
    from app.core.exceptions import StockNotFoundError
    
    with pytest.raises(StockNotFoundError):
        get_stock("INVALID")

def test_validation_error():
    """Test that ValidationError is raised for invalid input."""
    from app.core.exceptions import ValidationError
    
    with pytest.raises(ValidationError):
        add_to_portfolio(quantity=-10)

def test_successful_operation_logs():
    """Test that successful operations are logged."""
    with caplog.at_level(logging.INFO):
        get_stock("RELIANCE")
    
    assert "RELIANCE" in caplog.text
    assert "Successfully fetched" in caplog.text
```

### Manual Testing
```bash
# Test success case (200 OK)
curl http://localhost:8000/api/example/stock/RELIANCE/simple

# Test not found (404)
curl http://localhost:8000/api/example/stock/INVALID/simple

# Test validation (400)
curl http://localhost:8000/api/example/stock/validate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"ticker": ""}'

# Watch logs in real-time
tail -f logs/app.log
```

---

## 📊 Route Migration Priority

Update routes in this order:

### 🔴 Critical (Do First)
1. `auth.py` - Authentication is security-sensitive
2. `stock.py` - Main API used by frontend
3. `portfolio.py` - User data sensitive

### 🟡 Important (Do Second)
4. `watchlist.py`
5. `news.py`
6. `sentiment.py`

### 🟢 Nice-to-Have (Do Last)
7. `search.py`
8. `health.py`

---

## 🔧 Configuration

### In `.env` file
```bash
# Logging is auto-configured based on environment
ENVIRONMENT=local      # Verbose logging
DEBUG=true            # Show debug messages

# For production
ENVIRONMENT=production # INFO level console
DEBUG=false           # No debug messages
```

### To Change Log Levels
Edit `backend/app/core/logging_config.py`:
```python
# Line ~75 - Console handler level
console_handler.setLevel(logging.WARNING)  # Change to show fewer logs

# Line ~87 - File handler level  
file_handler.setLevel(logging.INFO)        # Change file verbosity
```

---

## 🐛 Troubleshooting

### Issue: No logs appearing
```bash
# Solution 1: Check logs directory exists
mkdir -p logs

# Solution 2: Check directory permissions
chmod 755 logs

# Solution 3: Check Python logging output
python -c "import logging; logging.basicConfig(level=logging.DEBUG); logging.debug('test')"
```

### Issue: Logs not rotating
```bash
# Check log file size (should be <10MB)
ls -lh logs/app.log

# Manually rotate if needed
mv logs/app.log logs/app.log.1
```

### Issue: Too many/few logs
```python
# In logging_config.py, adjust these lines:
console_handler.setLevel(logging.DEBUG)    # Change verbosity
file_handler.setLevel(logging.INFO)        # Change file verbosity
```

---

## 📈 Next Steps After Implementation

### Week 1
- [ ] Update all existing routes with error handling
- [ ] Run application with new logging
- [ ] Monitor logs for patterns

### Week 2
- [ ] Add metrics/alerts to errors
- [ ] Setup error tracking (Sentry optional)
- [ ] Document error codes for API consumers

### Week 3+
- [ ] Add distributed tracing (if multi-service)
- [ ] Setup log aggregation (ELK, Datadog, etc.)
- [ ] Add performance monitoring
- [ ] Create runbooks for common errors

---

## 📚 File Descriptions

### `logging_config.py`
Sets up rotating file handlers, console output, and structured logging format.

### `exceptions.py`
Defines custom exception classes for different error scenarios.

### `error_handlers.py`
Global middleware and exception handlers that catch all errors and return JSON responses.

### `error_responses.py`
Pydantic models for standardized error response format.

### `example_error_handling.py`
Reference implementation showing how to use the error handling in routes.

---

## ✅ Verification Steps

Run these to verify everything works:

```bash
# 1. Check imports work
python -c "from app.core.logging_config import setup_logging; print('✅ imports OK')"

# 2. Start server
uvicorn app.main:app --reload

# 3. In another terminal, test endpoint
curl http://localhost:8000/api/health | jq .

# 4. Check logs exist
[ -f logs/app.log ] && echo "✅ app.log exists" || echo "❌ missing"
[ -f logs/errors.log ] && echo "✅ errors.log exists" || echo "❌ missing"
[ -f logs/access.log ] && echo "✅ access.log exists" || echo "❌ missing"

# 5. Check for your request in logs
grep "GET /api/health" logs/access.log && echo "✅ request logged" || echo "❌ not found"
```

---

**Status**: ✅ Ready to Use  
**Complexity**: Low (all done for you)  
**Maintenance**: Minimal (automatic rotation)  
**Production Ready**: Yes  

For detailed guide, see `LOGGING_ERROR_HANDLING_GUIDE.md`
