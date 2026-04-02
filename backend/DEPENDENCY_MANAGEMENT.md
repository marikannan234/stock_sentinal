# Dependency Management Guide - FastAPI Backend

## Current Installation Status ✅

**Installed Core Dependencies:**
- `fastapi==0.115.0` - Web framework
- `uvicorn[standard]==0.30.5` - ASGI server with extra features
- `pydantic==2.9.2` - Data validation
- `pydantic-settings==2.5.2` - Settings management from .env
- `python-dotenv==1.0.1` - Environment variable loading
- `SQLAlchemy==2.0.36` - ORM
- `psycopg2-binary==2.9.10` - PostgreSQL driver
- `alembic==1.13.3` - Database migrations
- `httpx==0.28.1` - Async HTTP client (NEW)
- `APScheduler==3.11.2` - Task scheduling (NEW)
- `requests>=2.31.0` - HTTP library
- `yfinance>=0.2.40` - Stock data fetching
- `python-jose[cryptography]==3.3.0` - JWT authentication
- `passlib[bcrypt]==1.7.4` - Password hashing
- `email-validator==2.2.0` - Email validation
- `python-multipart>=0.0.6` - Form data parsing

---

## Virtual Environment Commands

### Windows

**Activate virtual environment:**
```powershell
.venv\Scripts\Activate.ps1
```

**If you get an execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

**Deactivate virtual environment:**
```powershell
deactivate
```

### Linux / macOS

**Activate virtual environment:**
```bash
source .venv/bin/activate
```

**Deactivate virtual environment:**
```bash
deactivate
```

---

## Dependency Management Workflow

### 1. **Install All Requirements (Fresh Setup)**

**Windows:**
```powershell
.venv\Scripts\pip install -r backend/requirements.txt
```

**Linux/macOS:**
```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. **Install a New Package**

Always install within the virtual environment, then update requirements.txt:

```powershell
.venv\Scripts\pip install package-name
.venv\Scripts\pip freeze > backend/requirements-pinned.txt  # For reference
```

Then manually add to `requirements.txt` with a version constraint (don't overwrite it):
```
package-name==X.Y.Z
```

### 3. **Update requirements.txt with Current Environment**

**Option A:** Manually pin critical packages (Recommended)
```powershell
.venv\Scripts\pip freeze | findstr /V "setuptools wheel pip" > temp.txt
# Review temp.txt and merge with existing requirements.txt
```

**Option B:** Get all packages with versions for reference
```powershell
.venv\Scripts\pip freeze > backend/requirements-full.txt
```

### 4. **Upgrade a Package**

```powershell
.venv\Scripts\pip install --upgrade package-name
```

Then update `requirements.txt`:
```
package-name==NEW.VERSION
```

### 5. **Check for Outdated Packages**

```powershell
.venv\Scripts\pip list --outdated
```

### 6. **Remove Unused Packages**

```powershell
.venv\Scripts\pip uninstall package-name
.venv\Scripts\pip freeze > backend/requirements-check.txt
```

---

## Best Practices for FastAPI Projects

### 1. **Version Pinning Strategy**

**For production-critical packages (use exact versions):**
```
fastapi==0.115.0
uvicorn[standard]==0.30.5
pydantic==2.9.2
SQLAlchemy==2.0.36
```

**For flexible dependencies (use >= for bugfix releases):**
```
requests>=2.31.0
yfinance>=0.2.40
python-multipart>=0.0.6
```

### 2. **Organize requirements.txt Structure**

Consider splitting requirements into environments:

**requirements-base.txt:**
```
# Core FastAPI dependencies
fastapi==0.115.0
uvicorn[standard]==0.30.5
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
```

**requirements-dev.txt:**
```
-r requirements-base.txt
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.28.1  # For testing
black==24.1.1
flake8==7.0.0
mypy==1.8.0
```

**requirements-prod.txt:**
```
-r requirements-base.txt
gunicorn==21.2.0
```

### 3. **Security Best Practices**

- **Always use exact versions in production requirements**
- **Regularly check for security vulnerabilities:**
  ```powershell
  .venv\Scripts\pip install safety
  .venv\Scripts\safety check
  ```
- **Review poetry/pip audit for known vulnerabilities:**
  ```powershell
  .venv\Scripts\pip install pip-audit
  .venv\Scripts\pip-audit
  ```

### 4. **Database Migration Management**

Your project uses Alembic. Always test migrations:
```powershell
.venv\Scripts\alembic upgrade head  # Apply migrations
.venv\Scripts\alembic downgrade -1  # Rollback
```

### 5. **Environment-Specific Settings**

Your `.env` file should never be committed. Create `.env.example`:
```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
JWT_SECRET_KEY=your-secret-key-here
FINNHUB_API_KEY=your-api-key-here
ENVIRONMENT=local
DEBUG=True
```

### 6. **Running the Application**

**Development:**
```powershell
.venv\Scripts\uvicorn app.main:app --reload
```

**Production (with Gunicorn):**
```powershell
.venv\Scripts\gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

---

## Recommended Additional Libraries

### For Future Features

#### **1. WebSocket Support**
```
python-engineio==4.8.0      # WebSocket abstraction
python-socketio==5.10.0     # Real-time notifications
```
**Use case:** Live price updates, push notifications

#### **2. Caching**
```
redis==5.0.1                # Redis client
aioredis==2.0.1             # Async Redis
```
**Use case:** Cache stock prices, user sessions

#### **3. Message Queue / Background Jobs**
```
celery==5.3.4               # Task queue
flower==2.0.1               # Celery monitoring
```
**Use case:** Async stock price fetching, email alerts, sentiment analysis jobs

#### **4. Monitoring & Logging**
```
prometheus-client==0.19.0   # Metrics
sentry-sdk==1.43.0          # Error tracking
structlog==24.1.0           # Structured logging
```
**Use case:** Production monitoring, error tracking, structured logs

#### **5. Data Validation & Serialization**
```
marshmallow==3.21.0         # Alternative to Pydantic (if needed)
pydantic-extra-types==2.4.1 # Extended Pydantic types
```

#### **6. Testing**
```
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
faker==22.0.0              # Generate test data
```
**Use case:** Unit tests, integration tests, coverage reports

#### **7. API Documentation Extras**
```
pydantic-openapi-schema==0.0.1  # Enhanced OpenAPI support
```

#### **8. Environment & Configuration**
Already covered with `pydantic-settings` and `python-dotenv` ✅

---

## Installation Commands Reference

### Install All Base Dependencies (First Time)
```powershell
cd "c:\Users\acer\Downloads\stock sentinal"
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### Add WebSockets & Caching
```powershell
.venv\Scripts\pip install python-engineio python-socketio redis aioredis
# Then update requirements.txt
```

### Add Celery for Background Jobs
```powershell
.venv\Scripts\pip install celery flower
# Then update requirements.txt
```

### Add Monitoring Stack
```powershell
.venv\Scripts\pip install prometheus-client sentry-sdk structlog
# Then update requirements.txt
```

### Full Testing Setup
```powershell
.venv\Scripts\pip install pytest pytest-asyncio pytest-cov faker
# Create requirements-dev.txt with these
```

---

## Troubleshooting

### Issue: Module not found after pip install
**Solution:** Ensure virtual environment is activated
```powershell
.venv\Scripts\Activate.ps1
python -c "import module_name"
```

### Issue: Requirements.txt is outdated
**Solution:** Generate fresh pinned versions
```powershell
.venv\Scripts\pip freeze > temp-freeze.txt
# Review and merge with requirements.txt
```

### Issue: Conflicts between package versions
**Solution:** Use pip to check compatibility
```powershell
.venv\Scripts\pip install pipdeptree
.venv\Scripts\pipdeptree
```

### Issue: PostgreSQL driver won't install
**Solution:** Ensure PostgreSQL dev headers are installed (Windows usually includes psycopg2-binary automatically)

---

## Summary Checklist

- ✅ Virtual environment created and activated
- ✅ Core FastAPI dependencies installed
- ✅ Database (PostgreSQL + SQLAlchemy + Alembic) configured
- ✅ Authentication (JWT + Passlib) installed
- ✅ HTTP client (httpx) for external APIs
- ✅ Task scheduling (APScheduler) for background jobs
- ✅ Environment configuration (.env + pydantic-settings)
- ✅ Stock data fetching (yfinance)
- ✅ requirements.txt updated
- ⭐ Ready for production deployment

---

## Production Deployment Checklist

Before deploying to production:

1. **Security:**
   - Change `DEBUG=False`
   - Generate strong `JWT_SECRET_KEY`
   - Use environment variables for all secrets
   - Run security check: `pip-audit`

2. **Database:**
   - Run migrations: `alembic upgrade head`
   - Verify connection to production DB

3. **Dependencies:**
   - All packages pinned to exact versions
   - No dev dependencies in production

4. **Server:**
   - Use Gunicorn with multiple workers
   - Configure CORS properly
   - Set up proper logging

5. **Monitoring:**
   - Set up error tracking (Sentry recommended)
   - Configure performance monitoring
   - Set up alerts for critical errors

---

**Last Updated:** 2026-04-01  
**Python Version:** 3.x (recommend 3.9+)  
**FastAPI Version:** 0.115.0  
**Virtual Environment:** `.venv` (located at project root)
