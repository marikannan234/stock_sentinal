# Stock Sentinel Database Fix - Quick Reference Card

## 🎯 What Was Wrong

| Issue | Root Cause | Impact |
|-------|-----------|--------|
| `DuplicateTable: ix_alert_history_user_id already exists` | `Base.metadata.create_all()` + Alembic both creating objects | Cannot start app |
| Migration downgrade fails with NULL constraint error | NULL values exist in `condition` column | Cannot rollback migrations |
| Indexes created twice in AlertHistory model | Both `index=True` AND explicit `Index()` | Duplicate index definitions |

---

## ✅ What Was Fixed

### 1. app/main.py (CRITICAL)
```diff
- if settings.ENVIRONMENT != "production":
-     logger.info("Creating database tables...")
-     Base.metadata.create_all(bind=engine)
+ # DO NOT use Base.metadata.create_all() with Alembic!
+ # Let Alembic migrations handle all schema management
```

### 2. app/models/alert.py
```diff
class AlertHistory(Base):
    __table_args__ = (
        Index("ix_alert_history_alert_id", "alert_id"),
        Index("ix_alert_history_user_id", "user_id"),
    )
    
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id"),
-       index=True  # ❌ REMOVED - Avoid duplication
    )
```

### 3. Migration: 25e65135c38c_allow_null_condition
```python
def downgrade():
    # Update NULL values to safe default first
    op.execute(sa.text("UPDATE alerts SET condition = 'GREATER_THAN' WHERE condition IS NULL"))
    # Then make NOT NULL
    op.alter_column('alerts', 'condition', nullable=False)
```

### 4. Migration: add_alert_tracking_and_history
```diff
- op.create_index('idx_alert_history_user_id', ...)
- op.create_index('idx_alert_history_alert_id', ...)
# Let model define indexes via __table_args__
```

---

## 🚀 How to Fix Your Database

### Option 1: Automated (Recommended)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
.\reset-database.ps1
```

### Option 2: Manual
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic downgrade base
alembic upgrade head
alembic current
```

---

## ✨ Verify It Works

```powershell
# Terminal 1: Start FastAPI
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Test API
curl http://localhost:8000/health
```

✅ Should see: `{"status":"ok"}` + no create_all() messages

---

## 📋 Best Practices Going Forward

### ✅ DO THIS

```python
# 1. Define indexes only in model
class MyModel(Base):
    __table_args__ = (
        Index("ix_my_table_col1", "col1"),
        Index("ix_my_table_col1_col2", "col1", "col2"),
    )
    
    col1: Mapped[str] = mapped_column(...)  # NO index=True
    col2: Mapped[str] = mapped_column(...)  # NO index=True

# 2. Generate migration from model
alembic revision --autogenerate -m "add columns to my_model"

# 3. Let Alembic handle the schema
alembic upgrade head
```

### ❌ DON'T DO THIS

```python
# ❌ WRONG: Duplicate indexes
col1: Mapped[str] = mapped_column(..., index=True)
__table_args__ = (Index("ix_table_col1", "col1"),)  # Duplicate!

# ❌ WRONG: Manual index creation
op.create_index('idx_table', ...)  # If already in model

# ❌ WRONG: Using create_all()
Base.metadata.create_all(bind=engine)  # Never! Use Alembic only

# ❌ WRONG: Making NOT NULL without handling NULLs
op.alter_column('table', 'col', nullable=False)  # Will fail if NULLs exist!
```

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| `alembic: command not found` | `.\.venv\Scripts\Activate.ps1` |
| `relation already exists` | `alembic downgrade base && alembic upgrade head` |
| `contains null values` | See migration file - already fixed |
| FastAPI says `Creating database tables` | You still have old code - review app/main.py |
| psycopg2 connection error | PostgreSQL not running OR wrong credentials |

---

## 📚 Documentation Files Created

1. **DATABASE_FIX_GUIDE.md** - Complete step-by-step guide with troubleshooting
2. **ALEMBIC_FASTAPI_BEST_PRACTICES.md** - Detailed explanations + examples
3. **backend/reset-database.ps1** - Automated reset script
4. **backend/DATABASE_EMERGENCY_SQL.sql** - Diagnostic SQL + emergency tools

---

## ⚡ Quick Command Reference

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Check migration status
alembic current

# See migration history
alembic history --verbose

# Create new migration
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Go back to initial state (dev only!)
alembic downgrade base

# Reset everything (automated)
.\reset-database.ps1
```

---

## 🎓 Key Learning

**The Golden Rule:**
```
Alembic is the DATABASE source of truth
Models define STRUCTURE only
Never call Base.metadata.create_all() with Alembic active
```

**Why?**
- Alembic tracks schema history (migrations folder)
- Alembic can rollback changes
- Multiple developers can stay in sync
- Production deployments are auditable

---

## 📞 Next Steps

1. ✅ Code changes applied
2. ⏭️ Run: `.\reset-database.ps1`
3. ⏭️ Start FastAPI: `python -m uvicorn app.main:app --reload`
4. ⏭️ Test: `curl http://localhost:8000/health`
5. ✨ Done! Database is clean and working

