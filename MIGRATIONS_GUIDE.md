# Database Migrations Guide for Stock Sentinel

## Overview

Stock Sentinel uses **Alembic** for database schema versioning and migrations. Migrations run **automatically on Docker container startup** before the application starts.

## Architecture

```
Docker Container Startup
    ↓
Alembic runs: alembic upgrade head
    ↓
PostgreSQL schema updated
    ↓
uvicorn starts: app.main:app
    ↓
Application ready
```

## How Migrations Run

### Automatic (Docker)
The `Dockerfile` includes this command:
```bash
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

This means:
1. Container starts
2. Alembic automatically applies all pending migrations
3. Application starts
4. **No manual intervention needed** ✅

### Manual (Local Development)
```bash
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

## Creating New Migrations

### Step 1: Modify the Model
Edit the SQLAlchemy model in `app/models/`:
```python
# Example: app/models/user.py
whatsapp_phone: Mapped[str | None] = mapped_column(
    String(20), 
    nullable=True, 
    unique=True, 
    index=True
)
```

### Step 2: Generate Migration
```bash
cd backend
.\.venv\Scripts\alembic.exe revision --autogenerate -m "describe your change"
```

Creates: `alembic/versions/XXXXX_describe_your_change.py`

### Step 3: Review the Migration File
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('whatsapp_phone', sa.String(length=20), nullable=True))
    op.create_index(op.f('ix_users_whatsapp_phone'), 'users', ['whatsapp_phone'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_users_whatsapp_phone'), table_name='users')
    op.drop_column('users', 'whatsapp_phone')
```

### Step 4: Rebuild Docker & Deploy
```bash
docker compose build backend
docker compose up -d
```

Migration runs automatically! ✅

## Migration Management Script

Use the provided `run_migrations.ps1` for common operations:

### Check Status
```powershell
.\run_migrations.ps1 -Action status
```

Output:
```
📊 Current Migration Status:
0005_add_whatsapp_phone (head)

📜 Migration History:
0004_trade_history_duration -> 0005_add_whatsapp_phone (head), Add whatsapp_phone column to users table
...
```

### Apply Migrations (Manual)
```powershell
.\run_migrations.ps1 -Action upgrade
```

### Rollback a Migration
```powershell
.\run_migrations.ps1 -Action downgrade -Revision "0004_trade_history_duration"
```

### View History
```powershell
.\run_migrations.ps1 -Action history
```

### Restart Containers (Auto-apply)
```powershell
.\run_migrations.ps1 -Action restart
```

## Docker Commands Reference

### Check migration status inside container
```bash
docker exec stocksentinel-backend alembic current
```

Output: `0005_add_whatsapp_phone (head)`

### View migration history
```bash
docker exec stocksentinel-backend alembic history
```

### Run migrations manually in container
```bash
docker exec stocksentinel-backend alembic upgrade head
```

### Check backend logs (including migration)
```bash
docker logs stocksentinel-backend | grep -i "migration"
```

## Important Notes

### ✅ DO's

1. **Always generate migrations before deploying** - Let Alembic manage the schema
2. **Review auto-generated migrations** - Ensure they do what you expect
3. **Test migrations locally first** - Before deploying to production
4. **Keep migrations focused** - One logical change per migration
5. **Provide clear descriptions** - Use meaningful migration messages

### ❌ DON'Ts

1. **Never use `Base.metadata.create_all()`** - This bypasses Alembic
2. **Don't manually edit the database schema** - Use migrations instead
3. **Don't skip migrations** - This causes schema drift
4. **Don't commit incomplete migrations** - Always test before pushing
5. **Don't delete migration files** - Keep them for historical record

## Troubleshooting

### Migration Fails on Startup
1. **Check logs:**
   ```bash
   docker logs stocksentinel-backend 2>&1 | tail -100
   ```

2. **Common issues:**
   - `type does not exist` - Enum type issue, simplify the migration
   - `column already exists` - Migration already applied, check history
   - `permission denied` - DB permissions issue, check PostgreSQL setup

### Rollback a Failed Migration
```bash
docker exec stocksentinel-backend alembic downgrade -1
```

### Reset Development Database
```bash
# WARNING: This deletes all data!
docker compose down -v
docker compose up -d
```

## Current Migrations

### Latest Migration
**Name:** `0005_add_whatsapp_phone`  
**Date:** 2026-04-10  
**Change:** Added `whatsapp_phone` column to users table  
**Status:** ✅ Applied

### Migration History
1. `0001_initial_schema` - Initial schema creation
2. `0002_add_trading_tables` - Trading, user settings, support tables
3. `0003_align_runtime_schema` - Align schema with SQLAlchemy models
4. `0004_trade_history_duration` - Make trade_history.duration nullable
5. `0005_add_whatsapp_phone` - Add WhatsApp phone support

## Production Deployment

For production deployments:

1. **Test migrations locally first**
   ```bash
   docker compose up -d
   docker exec stocksentinel-backend alembic current
   ```

2. **Create a backup**
   ```bash
   # Backup PostgreSQL database
   docker exec stocksentinel-db pg_dump -U stocksentinel stocksentinel > backup.sql
   ```

3. **Deploy with confidence**
   ```bash
   docker compose build backend
   docker compose up -d
   # Migrations run automatically!
   ```

4. **Verify**
   ```bash
   docker exec stocksentinel-backend alembic current
   ```

## Resources

-📖 [Alembic Documentation](https://alembic.sqlalchemy.org/)
- 🔗 [SQLAlchemy Models](../app/models/)
- 📝 [Migration Files](../alembic/versions/)
- ⚙️ [Alembic Config](../alembic.ini)

---

**Last Updated:** 2026-04-10  
**Maintained by:** Stock Sentinel Team
