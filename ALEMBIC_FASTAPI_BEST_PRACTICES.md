# Alembic + FastAPI Best Practices Guide

## Critical Rules

### ❌ DO NOT USE `Base.metadata.create_all()` WITH ALEMBIC

**Problem:**
```python
# ❌ WRONG - App startup code that conflicts with Alembic
if settings.ENVIRONMENT != "production":
    Base.metadata.create_all(bind=engine)
```

**Why it breaks:**
1. Creates tables/indexes directly from SQLAlchemy models
2. Migrations try to create the same objects again
3. Duplicate index errors: `psycopg2.errors.DuplicateTable: relation already exists`
4. Schema gets out of sync between code and database
5. Team members have inconsistent databases

**Solution:**
- Remove `Base.metadata.create_all()` completely
- **Always** use `alembic upgrade head` to apply migrations
- Migrations are the single source of truth

### ✅ CORRECT APPROACH

```python
# ✅ CORRECT - Let Alembic handle schema
# app/main.py - NO create_all()
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}")
    # DO NOT call Base.metadata.create_all()
    # Alembic migrations handle all DDL
    start_scheduler()
    yield
    stop_scheduler()
```

---

## Index Definition Strategy

### Rule 1: No Duplicate Indexes

**❌ WRONG - Duplicate definitions:**
```python
class AlertHistory(Base):
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id"),
        index=True  # Creates auto-index
    )
    __table_args__ = (
        Index("ix_alert_history_alert_id", "alert_id"),  # DUPLICATE!
    )
```

**✅ CORRECT - Define once in `__table_args__`:**
```python
class AlertHistory(Base):
    __table_args__ = (
        Index("ix_alert_history_alert_id", "alert_id"),
        Index("ix_alert_history_user_id", "user_id"),
        Index("ix_alert_history_alert_user", "alert_id", "user_id"),
    )
    
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id"),
        # NO index=True - using __table_args__ instead
    )
```

### Rule 2: Index Naming Convention

Use consistent naming:
- Single-column: `ix_tablename_columnname`
- Composite: `ix_tablename_col1_col2`
- Avoid: `idx_`, `pk_`, `fk_` prefixes for regular indexes

### Rule 3: Only Define Indexes in Model

- **Model defines**: Indexes in `__table_args__`, relationships, constraints
- **Migration applies**: Model changes to database
- **Never in migration**: Manual `op.create_index()` for model-defined indexes

---

## NULL Value Handling in Migrations

### Safe Downgrade with Existing NULL Values

**❌ WRONG - Fails if NULL values exist:**
```python
def downgrade():
    # FAILS: Cannot set NOT NULL if column has NULL values!
    op.alter_column('alerts', 'condition', nullable=False)
```

**✅ CORRECT - Update NULL values first:**
```python
def downgrade():
    # Update NULL values to a safe default
    op.execute(
        sa.text("UPDATE alerts SET condition = 'GREATER_THAN' WHERE condition IS NULL")
    )
    # Now safely make NOT NULL
    op.alter_column('alerts', 'condition', nullable=False)
```

---

## Migration Workflow

### 1. Making Schema Changes

```bash
# Edit your model
# Example: app/models/alert.py

# Auto-generate migration
cd backend
alembic revision --autogenerate -m "clear description of changes"

# Review the generated migration file
# alembic/versions/xxx_clear_description.py

# IMPORTANT: Review auto-generated migration for accuracy!
# - Verify index names are correct
# - Check for NULL handling if making columns NOT NULL
# - Test downgrade logic

# Apply migration
alembic upgrade head
```

### 2. Development Database Reset

```bash
# ONLY in development - never in production!
# Drop all tables and reset to initial state
alembic downgrade base  # Go to initial state

# Verify database is rebuilt
alembic upgrade head    # Apply all migrations fresh
```

### 3. Production Safe Migration

```bash
# 1. Create migration for your changes
alembic revision --autogenerate -m "descriptive name"

# 2. Test in development first
alembic downgrade base  # Reset
alembic upgrade head    # Re-apply

# 3. Review migration for data loss
# Edit migration if needed

# 4. In production:
# - First: Backup database
# - Then: alembic upgrade head
# - Verify app works
# - Keep downgrade path clear for quick rollback
```

---

## Common Issues and Fixes

### Issue: "relation already exists"

**Cause:** `Base.metadata.create_all()` + Alembic both creating objects

**Fix:**
1. Remove `Base.metadata.create_all()` from app
2. Drop and recreate database: `alembic downgrade base && alembic upgrade head`
3. Verify migrations are the only DDL source

### Issue: "column contains null values" on downgrade

**Cause:** Setting column to NOT NULL without handling existing NULLs

**Fix:**
```python
def downgrade():
    op.execute(sa.text("UPDATE table SET column = 'default' WHERE column IS NULL"))
    op.alter_column('table', 'column', nullable=False)
```

### Issue: Duplicate indexes

**Cause:** Both `index=True` AND `Index()` on same column

**Fix:**
1. In model: Define indexes ONLY in `__table_args__`
2. Remove `index=True` from mapped_column if index is in `__table_args__`
3. Regenerate migration: `alembic downgrade base && alembic upgrade head`

---

## Production Checklist

- [ ] No `Base.metadata.create_all()` in app code
- [ ] All schema changes go through migrations
- [ ] Migrations tested locally: `downgrade` → `upgrade`
- [ ] No duplicate index definitions
- [ ] NULL handling for non-nullable columns
- [ ] Backup database before running migrations
- [ ] Downgrade path verified for quick rollback
- [ ] Log all migration runs in production

---

## Files Modified in This Fix

### app/main.py
- ❌ Removed: `Base.metadata.create_all(bind=engine)`
- ✅ Added: Clear comment why it's dangerous

### app/models/alert.py
- ❌ Removed: `index=True` from `alert_id`, `user_id`, `triggered_at` in AlertHistory
- ✅ Result: Indexes defined only in `__table_args__`

### alembic/versions/25e65135c38c_allow_null_condition.py
- ✅ Updated: `downgrade()` now safely handles NULL values

### alembic/versions/add_alert_tracking_and_history.py
- ❌ Removed: All `op.create_index()` calls
- ✅ Result: Indexes come from model via Alembic auto-generation

---

## Next Steps After Applying This Fix

1. ✅ Apply fixes to code (done)
2. ⏭️ Reset development database
   ```bash
   cd backend
   alembic downgrade base
   alembic upgrade head
   ```
3. ⏭️ Start FastAPI - should not show `create_all()` message
4. ⏭️ Verify all tables and indexes created correctly
5. ⏭️ Run application tests

