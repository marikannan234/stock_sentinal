# Quick Reference Card - Logging & Error Handling

## 🚀 TL;DR - 30-Second Setup

```bash
# 1. Start server (logs auto-create)
cd backend
uvicorn app.main:app --reload

# 2. Test it works
curl http://localhost:8000/api/health

# 3. Check logs
tail -f logs/app.log
```

## 📝 Add Logging to Any Route

### Step 1: Import (3 lines)
```python
import logging
from app.core.logging_config import get_logger
from app.core.exceptions import StockNotFoundError

logger = get_logger(__name__)
```

### Step 2: Wrap in try-except
```python
@router.get("/data/{id}")
def get_data(id: int):
    try:
        logger.info(f"Get data for id={id}")
        
        if not data:
            raise StockNotFoundError("data")
        
        logger.info(f"Success: {id}")
        return data
    
    except StockNotFoundError:
        raise  # Already logged
    
    except Exception as exc:
        logger.error(f"Error: {str(exc)}", exc_info=exc)
        raise ExternalAPIError("Failed to get data")
```

---

## 🎯 Exception Classes

| Exception | HTTP | When to Use |
|-----------|------|------------|
| `ValidationError` | 400 | Form/input invalid |
| `InvalidTickerError` | 400 | Bad ticker format |
| `AuthenticationError` | 401 | Login failed |
| `TokenExpiredError` | 401 | JWT expired |
| `AuthorizationError` | 403 | Permission denied |
| `NotFoundError` | 404 | Item not found |
| `StockNotFoundError` | 404 | Stock not found |
| `ConflictError` | 409 | Duplicate entry |
| `RateLimitError` | 429 | Too many requests |
| `ExternalAPIError` | 502 | 3rd party API failed |
| `DatabaseError` | 500 | DB query failed |

---

## 📊 Log Levels

```python
logger.debug("Detailed info for debugging")      # Lots of output
logger.info("What just happened")                # Normal operation
logger.warning("Something unexpected")           # May cause issues
logger.error("Something failed", exc_info=exc)   # Problem occurred
logger.critical("System unusable")               # Disaster
```

---

## 📁 File Locations

```
backend/
├── logs/                           ← Auto-created
│   ├── app.log                     ← DEBUG+ (everything)
│   ├── errors.log                  ← ERROR+ (problems only)
│   └── access.log                  ← HTTP requests
│
├── app/core/
│   ├── logging_config.py           ← Setup
│   ├── exceptions.py               ← Exception classes
│   └── error_handlers.py           ← Middleware
│
└── requirements.txt                ← No new dependencies!
```

---

## 🔍 Common Patterns

### Pattern 1: Simple Success/Failure
```python
@router.get("/data/{id}")
def get_data(id: int):
    try:
        logger.info(f"Getting data: {id}")
        data = fetch_from_db(id)
        if not data:
            raise NotFoundError(f"ID {id}")
        logger.info(f"Got data for {id}")
        return data
    except NotFoundError:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}", exc_info=exc)
        raise ExternalAPIError("Failed to get data")
```

### Pattern 2: Add Context
```python
logger.info(
    f"User {user_id} action: {action}",
    extra={
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }
)
```

### Pattern 3: Error with Details
```python
try:
    validate_input(user_data)
except ValueError as exc:
    logger.warning(
        f"Validation failed: {str(exc)}",
        extra={"error": str(exc), "input": user_data}
    )
    raise ValidationError(str(exc))
```

### Pattern 4: Retry Logic
```python
max_retries = 3
for attempt in range(max_retries):
    try:
        logger.debug(f"API call attempt {attempt + 1}/{max_retries}")
        return call_external_api()
    except Exception as exc:
        if attempt == max_retries - 1:
            logger.error(f"All {max_retries} attempts failed", exc_info=exc)
            raise ExternalAPIError("API failed")
        logger.warning(f"Attempt {attempt + 1} failed, retrying...")
        time.sleep(2 ** attempt)  # Exponential backoff
```

---

## ✅ Error Response Format

### Request
```bash
curl http://localhost:8000/api/stock/INVALID/quote
```

### Response (400)
```json
{
  "error": {
    "code": "INVALID_TICKER",
    "message": "Invalid ticker format: 'INVALID'",
    "details": {
      "ticker": "INVALID",
      "allowed_format": "1-10 alphanumeric characters"
    }
  }
}
```

### Log Entry
```
[2026-04-01 10:30:45] [WARNING] [app.api.routes.stock:_validate_ticker:70] - Invalid ticker provided: INVALID
```

---

## 🔧 Verification

### Run verification script
```bash
python verify_logging.py              # Check all systems
python verify_logging.py --test       # Test with sample logs
python verify_logging.py --clean      # Clean old logs
```

### Check logs manually
```bash
tail -f logs/app.log                  # Follow app log
tail -f logs/errors.log               # Follow error log
grep "ERROR" logs/app.log             # Search for errors
grep "user_id" logs/app.log           # Search by context
```

### Check log rotation
```bash
ls -lh logs/                          # View all log files
# After 10MB: app.log.1, app.log.2, etc.
```

---

## 🚨 Important DON'Ts

❌ **DON'T** use generic HTTPException
```python
# WRONG
raise HTTPException(status_code=404, detail="Not found")
```

✅ **DO** use specific exceptions
```python
# RIGHT
raise StockNotFoundError("RELIANCE")
```

---

❌ **DON'T** use print() for debugging
```python
# WRONG
print(f"DEBUG: {data}")
```

✅ **DO** use logger
```python
# RIGHT
logger.debug(f"Data: {data}")
```

---

❌ **DON'T** ignore exceptions
```python
# WRONG
try:
    data = api.fetch()
except:
    pass
```

✅ **DO** log and handle
```python
# RIGHT
try:
    data = api.fetch()
except Exception as exc:
    logger.error(f"Fetch failed: {exc}", exc_info=exc)
    raise ExternalAPIError("API unavailable")
```

---

❌ **DON'T** log sensitive data
```python
# WRONG
logger.info(f"Password: {password}")
```

✅ **DO** log safely
```python
# RIGHT
logger.info(f"User {user_id} authenticated")
```

---

## 📞 Troubleshooting

### Logs not created?
```bash
# Make sure backend directory exists
ls backend/app/core/logging_config.py
# Should show file

# Start server - logs auto-create on first request
uvicorn app.main:app --reload
```

### Can't find error?
```bash
# Search error logs
grep "ERROR" logs/errors.log
grep "STOCK_NOT_FOUND" logs/app.log

# Show last 50 lines
tail -50 logs/app.log
```

### Logs too large?
```bash
# Check file sizes
ls -lh logs/

# They auto-rotate at 10MB
# Keeps 10 old files (app.log.1 through app.log.10)
```

### Import errors?
```bash
# Make sure files created correctly
ls backend/app/core/logging_config.py
ls backend/app/core/exceptions.py

# Test imports
python -c "from app.core.logging_config import get_logger; print('OK')"
```

---

## 🎓 Migration Priority

### Priority 1 (Do First - Today)
```
1. app/api/routes/auth.py         ← Handles login/security
2. app/api/routes/stock.py        ← Most used
3. app/api/routes/portfolio.py    ← User data
```

### Priority 2 (Tomorrow)
```
4. app/api/routes/watchlist.py
5. app/api/routes/sentiment.py
6. app/api/routes/news.py
```

### Priority 3 (Nice-to-have)
```
7. app/api/routes/health.py
8. app/api/routes/search.py
```

---

## ⏱️ Time Estimate

| Task | Time |
|------|------|
| Verify setup | 5 min |
| Migrate 1 route | 5-10 min |
| Migrate all routes | 45-60 min |
| Write tests | 1-2 hours |
| **Total** | **2-3 hours** |

---

## 🎯 Next Steps

1. **This hour**: `python verify_logging.py --test`
2. **Today**: Migrate auth.py and stock.py
3. **Tomorrow**: Migrate remaining routes
4. **This week**: Add basic tests
5. **Next**: Start Phase 2 (Alerts System)

---

## 📚 See Also

- **Start here**: LOGGING_IMPLEMENTATION_CHECKLIST.md
- **Full guide**: LOGGING_ERROR_HANDLING_GUIDE.md
- **Example route**: MIGRATION_EXAMPLE_STOCK_ROUTE.md
- **Code reference**: app/api/routes/example_error_handling.py

---

## 🔗 File Links

| File | Purpose |
|------|---------|
| `app/core/logging_config.py` | Logger setup (1 call: `setup_logging()`) |
| `app/core/exceptions.py` | 13 exception classes |
| `app/core/error_handlers.py` | Middleware + handlers |
| `app/schemas/error_responses.py` | Response schemas |
| `app/main.py` | Already integrated ✅ |
| `app/api/routes/example_error_handling.py` | Example patterns |

---

**Questions?** Check the comprehensive guide: `LOGGING_ERROR_HANDLING_GUIDE.md`
