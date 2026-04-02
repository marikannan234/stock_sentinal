# Production-Level Logging & Error Handling Guide

## 📁 Folder Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging_config.py      ✨ NEW - Centralized logging setup
│   │   ├── exceptions.py           ✨ NEW - Custom exception classes
│   │   └── error_handlers.py       ✨ NEW - Middleware & exception handlers
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── error_responses.py      ✨ NEW - Standardized error schemas
│   │   └── ...
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── example_error_handling.py  ✨ NEW - Example routes
│   │   │   ├── stock.py            📝 UPDATE - Add error handling
│   │   │   ├── auth.py             📝 UPDATE - Add error handling
│   │   │   └── ...
│   │
│   ├── main.py                      📝 UPDATE - Integrated logging
│   └── ...
│
├── logs/                            ✨ NEW - Auto-created directory
│   ├── app.log                      (All application logs)
│   ├── errors.log                   (Errors only)
│   ├── access.log                   (HTTP requests)
│   └── app.log.1, app.log.2 ...    (Rotated files)
│
└── requirements.txt                 (No changes needed)
```

---

## 🚀 Quick Start (Copy-Paste Instructions)

### 1. Files Already Created ✅
The following files have been created for you:
- ✅ `backend/app/core/logging_config.py`
- ✅ `backend/app/core/exceptions.py`
- ✅ `backend/app/core/error_handlers.py`
- ✅ `backend/app/schemas/error_responses.py`
- ✅ `backend/app/main.py` (updated)
- ✅ `backend/app/api/routes/example_error_handling.py`

### 2. Test the Setup

```bash
# Navigate to backend
cd backend

# Run the application
uvicorn app.main:app --reload

# In another terminal, test an endpoint
curl http://localhost:8000/api/health

# Check logs directory
ls logs/
```

### 3. View Logs

```bash
# Stream application logs (all levels)
tail -f logs/app.log

# Stream errors only
tail -f logs/errors.log

# Stream HTTP access logs
tail -f logs/access.log

# View colored logs in real-time
tail -f logs/app.log | less -R
```

---

## 📝 How to Use in Your Routes

### Pattern 1: Simple Route with Error Handling

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.core.exceptions import StockNotFoundError, ExternalAPIError
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/{ticker}/quote")
async def get_stock_quote(ticker: str, current_user = Depends(get_current_user)):
    """Get stock quote with error handling."""
    
    ticker = ticker.strip().upper()
    logger.info(f"Fetching quote for {ticker}", extra={"ticker": ticker})
    
    try:
        # Your code here
        if not ticker:
            raise StockNotFoundError(ticker)
        
        price = 2850.50  # Get from API
        logger.info(f"Successfully fetched {ticker}: ${price}")
        
        return {"ticker": ticker, "price": price}
    
    except StockNotFoundError:
        raise  # Will be caught by global handler
    
    except Exception as exc:
        logger.error(f"Error fetching {ticker}: {str(exc)}", exc_info=exc)
        raise ExternalAPIError(
            message=f"Failed to fetch {ticker}",
            details={"error": str(exc)}
        )
```

### Pattern 2: Validation with Custom Exception

```python
from app.core.exceptions import ValidationError

@router.post("/portfolio/add")
async def add_to_portfolio(quantity: int, price: float):
    """Add stock to portfolio with validation."""
    
    logger.info("Adding to portfolio", extra={"quantity": quantity, "price": price})
    
    if quantity <= 0:
        raise ValidationError(
            message="Quantity must be greater than 0",
            details={"field": "quantity", "value": quantity}
        )
    
    if price <= 0:
        raise ValidationError(
            message="Price must be greater than 0",
            details={"field": "price", "value": price}
        )
    
    logger.info(f"Successfully added: qty={quantity}, price={price}")
    return {"success": True}
```

### Pattern 3: With Retry Logic

```python
from app.core.exceptions import ExternalAPIError
import time

@router.get("/{ticker}/with-retry")
async def get_stock_with_retry(ticker: str, max_retries: int = 3):
    """Get stock with automatic retry on failure."""
    
    ticker = ticker.strip().upper()
    logger.info(f"Fetching {ticker} (retry enabled)")
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Attempt {attempt}/{max_retries}")
            
            # Your code here
            price = 2850.50
            
            logger.info(f"Success on attempt {attempt}")
            return {"ticker": ticker, "price": price}
        
        except Exception as exc:
            logger.warning(f"Attempt {attempt} failed: {str(exc)}")
            
            if attempt < max_retries:
                time.sleep(1)  # Wait before retry
                continue
            
            # All retries failed
            logger.error(f"Failed after {max_retries} attempts")
            raise ExternalAPIError(
                message=f"Failed to fetch {ticker} after {max_retries} attempts",
                details={"last_error": str(exc)}
            )
```

---

## 🔍 Log Examples

### Successful Request
```
[2026-04-01 10:30:45] [INFO    ] [app.main:lifespan:<lambda>:59] - Starting StockSentinel API (Environment: local)
[2026-04-01 10:30:45] [INFO    ] [app.api.routes.stock:get_stock_quote:42] - Fetching quote for RELIANCE
[2026-04-01 10:30:45] [INFO    ] [app.core.error_handlers:request_logging_middleware:65] - → GET /api/stock/RELIANCE/quote
[2026-04-01 10:30:46] [INFO    ] [app.api.routes.stock:get_stock_quote:48] - Successfully fetched RELIANCE: $2850.50
[2026-04-01 10:30:46] [INFO    ] [app.core.error_handlers:request_logging_middleware:88] - ← ✅ GET /api/stock/RELIANCE/quote - 200 (120ms)
```

### Validation Error
```
[2026-04-01 10:31:10] [INFO    ] [app.core.error_handlers:request_logging_middleware:65] - → POST /api/portfolio/add
[2026-04-01 10:31:10] [WARNING ] [app.api.routes.portfolio:add_to_portfolio:35] - Validation failed
[2026-04-01 10:31:10] [INFO    ] [app.core.error_handlers:request_logging_middleware:88] - ← ⚠️ POST /api/portfolio/add - 400 (45ms)
```

### Error with Retry
```
[2026-04-01 10:32:00] [INFO    ] [app.api.routes.stock:get_with_retry:10] - Fetching INFY (retry enabled)
[2026-04-01 10:32:00] [DEBUG   ] [app.api.routes.stock:get_with_retry:15] - Attempt 1/3
[2026-04-01 10:32:01] [WARNING ] [app.api.routes.stock:get_with_retry:25] - Attempt 1 failed: Connection timeout
[2026-04-01 10:32:02] [DEBUG   ] [app.api.routes.stock:get_with_retry:15] - Attempt 2/3
[2026-04-01 10:32:03] [WARNING ] [app.api.routes.stock:get_with_retry:25] - Attempt 2 failed: Connection timeout
[2026-04-01 10:32:04] [DEBUG   ] [app.api.routes.stock:get_with_retry:15] - Attempt 3/3
[2026-04-01 10:32:05] [INFO    ] [app.api.routes.stock:get_with_retry:20] - Success on attempt 3
```

---

## 📋 Exception Classes Reference

### Available Exceptions

```python
# Import
from app.core.exceptions import (
    APIException,              # Base class
    ValidationError,           # 400 - Input validation failed
    StockNotFoundError,        # 404 - Stock not found
    InvalidTickerError,        # 400 - Invalid ticker format
    RateLimitError,            # 429 - Rate limit exceeded
    AuthenticationError,       # 401 - Auth failed
    TokenExpiredError,         # 401 - JWT expired
    InvalidCredentialsError,   # 401 - Wrong password
    AuthorizationError,        # 403 - No permission
    NotFoundError,             # 404 - Resource not found
    ConflictError,             # 409 - Duplicate entry
    ExternalAPIError,          # 502 - External API failed
    DatabaseError,             # 500 - Database error
)

# Usage
raise StockNotFoundError("RELIANCE")
raise ValidationError("Invalid email", details={"field": "email"})
raise RateLimitError()
raise TokenExpiredError()
raise ExternalAPIError("YFinance API failed")
```

### Custom Response Format

All exceptions return this JSON format:

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

---

## 🎯 Logging Best Practices

### ✅ DO

```python
# Good: Clear, informative messages
logger.info(f"User {user_id} created portfolio", extra={"user_id": user_id})

# Good: Include relevant context
logger.error(f"Failed to fetch {ticker}", exc_info=exc, extra={"ticker": ticker})

# Good: Use appropriate levels
logger.debug("Database query: SELECT * FROM stocks")  # DEBUG
logger.info("Processing batch of 1000 stocks")         # INFO
logger.warning("API response slower than expected")     # WARNING
logger.error("Failed after 3 retries")                  # ERROR
```

### ❌ DON'T

```python
# Bad: Too generic
logger.info("Error occurred")

# Bad: Leaking sensitive info
logger.error(f"Database password: {db_password}")

# Bad: Wrong log level
logger.error("Processed 100 records")  # Should be INFO

# Bad: No context
logger.warning("Something went wrong")
```

---

## 📊 Rotating Logs

Logs are automatically rotated when they exceed size limits:

| Log File | Max Size | Backup Files | Duration |
|----------|----------|--------------|----------|
| app.log | 10 MB | 10 files | ~100 MB total |
| errors.log | 5 MB | 5 files | ~25 MB total |
| access.log | 10 MB | 10 files | ~100 MB total |

Old log files are named: `app.log.1`, `app.log.2`, etc.

To clean up old logs:
```bash
find logs/ -name "*.log.*" -mtime +30 -delete  # Delete logs older than 30 days
```

---

## 🔧 Configuration

### Environment Variables (in .env)

```bash
# Logging configuration
ENVIRONMENT=local        # local | staging | production
DEBUG=true              # Enable debug logging

# In production:
ENVIRONMENT=production
DEBUG=false
```

### Log Levels by Environment

```python
# Local/Development
- Console: DEBUG level (very verbose)
- File: DEBUG level

# Production
- Console: INFO level (important events only)
- File: DEBUG level (detailed troubleshooting)
- Error File: ERROR level (problems only)
```

---

## 🧪 Testing Error Handling

### Test Scripts

```bash
# Test validation error
curl -X POST http://localhost:8000/api/example/stock/validate \
  -H "Content-Type: application/json" \
  -d '{"ticker": ""}'

# Test not found error
curl -X GET http://localhost:8000/api/example/stock/INVALID/simple

# Test success
curl -X GET http://localhost:8000/api/example/stock/RELIANCE/simple

# Check logs
tail -f logs/app.log
tail -f logs/errors.log
```

---

## 📚 Integration Checklist

- [ ] Files created:
  - [ ] `backend/app/core/logging_config.py`
  - [ ] `backend/app/core/exceptions.py`
  - [ ] `backend/app/core/error_handlers.py`
  - [ ] `backend/app/schemas/error_responses.py`
  - [ ] `backend/app/api/routes/example_error_handling.py`

- [ ] Files updated:
  - [ ] `backend/app/main.py` (logging integrated)

- [ ] Testing:
  - [ ] Run `uvicorn app.main:app --reload`
  - [ ] Check `logs/` directory exists
  - [ ] Test endpoints (should see logs)
  - [ ] Test error cases (should see error logs)

- [ ] Update your routes:
  - [ ] Add `from app.core.logging_config import get_logger`
  - [ ] Replace `print()` statements with `logger.info()`
  - [ ] Replace generic exceptions with specific ones
  - [ ] Add `exc_info=exc` to error logs

---

## 🎓 Migration Guide (Updating Existing Routes)

### Before (Old Way)
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/{ticker}")
def get_stock(ticker: str):
    try:
        data = fetch_data(ticker)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error")
```

### After (New Way)
```python
from fastapi import APIRouter
from app.core.logging_config import get_logger
from app.core.exceptions import StockNotFoundError, ExternalAPIError

router = APIRouter()
logger = get_logger(__name__)

@router.get("/{ticker}")
def get_stock(ticker: str):
    logger.info(f"Fetching {ticker}")
    
    try:
        if not ticker:
            raise StockNotFoundError(ticker)
        
        data = fetch_data(ticker)
        logger.info(f"Successfully fetched {ticker}")
        return data
    
    except (StockNotFoundError, ExternalAPIError):
        raise
    
    except Exception as exc:
        logger.error(f"Error fetching {ticker}: {str(exc)}", exc_info=exc)
        raise ExternalAPIError(
            message=f"Failed to fetch {ticker}",
            details={"error": str(exc)}
        )
```

---

## 📞 Support & Troubleshooting

### Q: Logs not appearing?
**A**: Check that `logs/` directory exists and is writable:
```bash
ls -la logs/
chmod 755 logs/
```

### Q: Want more detailed logs?
**A**: Set log level in `logging_config.py`:
```python
console_handler.setLevel(logging.DEBUG)  # Change INFO to DEBUG
```

### Q: How to disable colored output?
**A**: Set `TERM=dumb` environment variable:
```bash
TERM=dumb uvicorn app.main:app --reload
```

### Q: Can I send logs to external service?
**A**: Yes! Add a custom handler in `logging_config.py`:
```python
# Example: Send to Sentry
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn="https://...",
    integrations=[LoggingIntegration()]
)
```

---

## 🚀 What's Next?

1. **Update existing routes** with error handling (use migration guide)
2. **Add monitoring** (track error rates, response times)
3. **Setup alerts** (notify on errors in production)
4. **Add request tracing** (track requests across services)
5. **Setup log aggregation** (ELK stack, Datadog, etc.)

---

## 📖 Quick Reference

```python
# Import in your route
from app.core.logging_config import get_logger
from app.core.exceptions import (
    ValidationError,
    StockNotFoundError,
    ExternalAPIError,
)

logger = get_logger(__name__)

# Logging
logger.debug("Detailed debug info")
logger.info("Important event happened")
logger.warning("Something concerning")
logger.error("Error occurred", exc_info=exc)
logger.critical("Critical system issue")

# Exceptions
raise ValidationError("Invalid input")
raise StockNotFoundError("INVALID")
raise ExternalAPIError("API failed")
```

---

**Version**: 1.0  
**Created**: April 1, 2026  
**Status**: Production Ready ✅  
**Last Updated**: April 1, 2026
