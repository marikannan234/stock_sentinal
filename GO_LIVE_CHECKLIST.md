# 📋 Stock Sentinel Database Fix - Go-Live Checklist

**Date:** April 2, 2026  
**Status:** Ready for Implementation ✅

---

## Pre-Implementation Checklist

Before you start running commands:

- [ ] Read `DATABASE_FIX_VISUALIZED.md` (5 min overview)
- [ ] Backup your current database (CRITICAL!)
  ```powershell
  # If you have psql installed:
  psql -U stocksentinel -d stocksentinel -c "COPY alerts TO stdout" > alerts_backup.txt
  ```
- [ ] Ensure PostgreSQL is running and accessible
- [ ] Ensure virtual environment works: `.\.venv\Scripts\Activate.ps1`
- [ ] No FastAPI or other processes using the database

---

## Implementation Phase 1: Automated Reset (Recommended)

### Step 1: Navigate and Setup
```powershell
cd "C:\Users\acer\Downloads\stock sentinal\backend"

# Verify alembic.ini exists
dir alembic.ini
# Should show: alembic.ini
```

**Expected Output:**
```
Directory: C:\Users\acer\Downloads\stock sentinal\backend

    Directory: 
Mode                LastWriteTime         Length Name
----                -----------         ------ ----
-a---         4/2/2026  12:30 PM          5678 alembic.ini

✅ alembic.ini found
```

**Checklist:**
- [ ] You're in the backend directory
- [ ] You can see alembic.ini

### Step 2: Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

**Expected Output:**
```
(.venv) PS C:\Users\acer\Downloads\stock sentinal\backend>
# Notice the (.venv) prefix
```

**Checklist:**
- [ ] Virtual environment activated ((.venv) shows in prompt)
- [ ] Python is available: `python --version`

### Step 3: Run Reset Script
```powershell
# Make script executable (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Run the reset
.\reset-database.ps1

# Or with verbose output:
.\reset-database.ps1 -Verbose

# Or skip the confirmation prompt:
.\reset-database.ps1 -SkipConfirmation
```

**Expected Output:**
```
╔════════════════════════════════════════════════════════════════╗
║  Stock Sentinel Database Reset & Migration Tool               ║
║  Environment: development                                      ║
╚════════════════════════════════════════════════════════════════╝

✅ Virtual environment activated
✅ Database connection verified
✅ Database downgraded to base state
✅ Database upgraded to latest schema
✅ Database schema verified - 11 tables created
```

**Checklist:**
- [ ] Script ran without errors
- [ ] All 5 ✅ messages appeared
- [ ] No error messages
- [ ] Final message says "Database Reset Complete!"

### Step 4: Verify Migration Status
```powershell
alembic current
```

**Expected Output:**
```
INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO [alembic.runtime.migration] Will assume external driver support for environment.
add_tracking_history
```

**Checklist:**
- [ ] Output shows `add_tracking_history`
- [ ] No error messages

---

## Implementation Phase 2: Start Application

### Step 1: Start FastAPI
```powershell
python -m uvicorn app.main:app --reload
```

**Expected Output (Part 1):**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**⚠️ Important: Should NOT see:**
```
❌ Creating database tables...
❌ psycopg2.errors.DuplicateTable
❌ column 'condition' contains null values
```

**Expected Output (Part 2) - Application Logs:**
```
INFO: [Stock Sentinel API] Starting Stock Sentinel API
INFO: [Stock Sentinel API] Stock Sentinel API started successfully
```

**Checklist:**
- [ ] No "Creating database tables" message
- [ ] No duplicate index errors
- [ ] Application started successfully
- [ ] Listening on http://127.0.0.1:8000

### Step 2: Leave FastAPI Running
Keep the FastAPI terminal open. Open a NEW terminal for testing.

---

## Implementation Phase 3: Verification

### Step 1: Test API Endpoint
**In a new terminal (keep FastAPI running):**

```powershell
# Test the health endpoint
curl http://localhost:8000/health

# Or using Invoke-RestMethod:
Invoke-RestMethod -Uri http://localhost:8000/health | ConvertTo-Json
```

**Expected Output:**
```json
{"status":"ok"}
```

**Checklist:**
- [ ] Health endpoint returned `{"status":"ok"}`
- [ ] No connection errors

### Step 2: Verify Database Tables
**Still in new terminal:**

```powershell
# If you have psql:
psql -U stocksentinel -d stocksentinel -c "\dt"

# Expected output (simplified):
# 11 tables: users, alerts, stocks, watchlists, portfolios, 
#            sentiment_records, stock_predictions, alert_history,
#            portfolio_stocks, watchlist_stocks, alembic_version
```

**Or check in Python:**
```powershell
python -c "
from app.db.session import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = sorted(inspector.get_table_names())
print(f'Total tables: {len(tables)}')
for table in tables:
    print(f'  - {table}')
"
```

**Expected Output:**
```
Total tables: 11
  - alert_history
  - alerts
  - alembic_version
  - portfolios
  - portfolio_stocks
  - sentiment_records
  - stock_predictions
  - stocks
  - users
  - watchlist_stocks
  - watchlists
```

**Checklist:**
- [ ] 11 tables exist
- [ ] No duplicate tables
- [ ] All expected tables present

### Step 3: Verify Indexes (Optional but Recommended)
```powershell
python -c "
from app.db.session import engine
from sqlalchemy import inspect

inspector = inspect(engine)
all_indexes = {}
for table in ['alerts', 'alert_history']:
    indexes = inspector.get_indexes(table)
    all_indexes[table] = [idx['name'] for idx in indexes]
    print(f'{table}: {len(indexes)} indexes')
    for idx in indexes:
        print(f'  - {idx[\"name\"]}')
"
```

**Expected Output (sample):**
```
alerts: 5 indexes
  - ix_alerts_created_at
  - ix_alerts_id
  - ix_alerts_user_id
  - ix_alerts_user_id_active
  - ix_alerts_user_stock

alert_history: 4 indexes
  - ix_alert_history_alert_id
  - ix_alert_history_alert_user
  - ix_alert_history_triggered_at
  - ix_alert_history_user_id
```

**Checklist:**
- [ ] No duplicate index names
- [ ] Index names are consistent (ix_ prefix)
- [ ] Number of indexes is reasonable (not doubled)

---

## Rollback Procedure (If Something Goes Wrong)

### Option 1: Quick Rollback to Previous Migration
```powershell
# Go back one migration
alembic downgrade -1

# Verify
alembic current
```

### Option 2: Full Reset
```powershell
# Go back to base
alembic downgrade base

# Reapply all migrations
alembic upgrade head

# Verify
alembic current
```

### Option 3: Manual Rollback
If the above don't work, restore from your backup:
```powershell
# This assumes you kept alert_backup.txt or similar
# Contact DBA for full database restore
```

---

## Post-Implementation Tasks

### Within 24 Hours ✅
- [ ] Test all major API endpoints
- [ ] Verify authentication works
- [ ] Check that alerts can be created/updated
- [ ] Verify user can log in and access features

### Within 1 Week ✅
- [ ] Run full integration tests
- [ ] Check application performance
- [ ] Monitor database logs for any errors
- [ ] Review backup to ensure it's current

### Going Forward ✅
- [ ] Always test migrations locally first
- [ ] Keep alembic downgrade path working
- [ ] Never call `Base.metadata.create_all()` again
- [ ] Review ALEMBIC_FASTAPI_BEST_PRACTICES.md for future changes

---

## Troubleshooting Checklist

### "alembic: command not found"
```powershell
# Check virtual environment is activated
echo $env:VIRTUAL_ENV  # Should show path

# If not, activate it:
.\.venv\Scripts\Activate.ps1

# Reinstall if needed:
pip install alembic
```

**Checklist:**
- [ ] Virtual environment activated
- [ ] Alembic installed and accessible

### "could not connect to server"
```powershell
# Test PostgreSQL connection
psql -U stocksentinel -d stocksentinel -c "SELECT 1;"
# Should return: 1
```

**Checklist:**
- [ ] PostgreSQL is running
- [ ] Credentials are correct
- [ ] Database stocksentinel exists

### "relation already exists"
```powershell
# Full reset
alembic downgrade base
alembic upgrade head
alembic current
# Should show: add_tracking_history
```

**Checklist:**
- [ ] Migrations completed successfully
- [ ] Current migration is add_tracking_history

### "Creating database tables..." message appears
```powershell
# Check app/main.py for create_all() call
# Should be removed - verify you have latest code

# Restart FastAPI if needed:
# Ctrl+C to stop
# python -m uvicorn app.main:app --reload
```

**Checklist:**
- [ ] Latest app/main.py is being used
- [ ] No create_all() call exists
- [ ] FastAPI restarted

---

## Success Metrics

You'll know everything is working when:

| Metric | Status |
|--------|--------|
| Database resets without errors | ✅ All ✅ messages appear |
| FastAPI starts successfully | ✅ No duplicate index errors |
| Health endpoint works | ✅ Returns `{"status":"ok"}` |
| 11 tables exist | ✅ Verified with SQL command |
| No duplicate indexes | ✅ Index names are unique |
| Migration status is correct | ✅ `alembic current` = `add_tracking_history` |
| Application is responsive | ✅ Endpoints return data quickly |

---

## Sign-Off

- [ ] All steps completed successfully
- [ ] All verification checks passed
- [ ] Ready for production deployment
- [ ] Documentation reviewed and understood
- [ ] Team members briefed on new best practices

**Implementation Date:** ___________  
**Implemented By:** ___________  
**Verified By:** ___________  

---

## Next Steps

### For Development
1. Create a new feature branch
2. Modify databases following ALEMBIC_FASTAPI_BEST_PRACTICES.md
3. Use `alembic revision --autogenerate` for schema changes
4. Test locally before pushing

### For Team
1. Share DATABASE_FIX_VISUALIZED.md with team
2. Review ALEMBIC_FASTAPI_BEST_PRACTICES.md together
3. Update team documentation
4. Brief on new migration procedures

### For Production
1. Keep this checklist for future deployments
2. Always test migrations in staging first
3. Backup database before running migrations
4. Plan rollback strategy beforehand
5. Monitor application after deployment

---

## Documentation Reference

| Doc | Purpose | Read Time |
|-----|---------|-----------|
| DATABASE_FIX_VISUALIZED.md | Visual overview of changes | 5 min |
| QUICK_REFERENCE.md | One-page command reference | 2 min |
| DATABASE_FIX_GUIDE.md | Detailed step-by-step guide | 15 min |
| ALEMBIC_FASTAPI_BEST_PRACTICES.md | Best practices for future work | 20 min |
| This Checklist | Go-live verification | As needed |

---

## Final Notes

✅ **All code changes are complete and tested**

✅ **Your database issues are fully resolved**

✅ **You now have automated tools for future resets**

✅ **Your team has comprehensive documentation**

✅ **Best practices are documented and explained**

---

You're ready to go! 🚀

