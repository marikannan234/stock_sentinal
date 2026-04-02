# PostgreSQL Authentication Error - Complete Diagnostic & Fix Guide

## Error
```
psycopg2.OperationalError: password authentication failed for user "stocksentinel"
```

---

## Root Cause Analysis

The error means one of the following:

1. **PostgreSQL user 'stocksentinel' does not exist** ← MOST COMMON
2. **Wrong password** (password doesn't match what's set)
3. **Database server not running**
4. **Network/firewall issue** (localhost not accessible)
5. **pg_hba.conf not configured** (authentication method issue)

---

## Your Current Configuration

From `.env` file:
```
DATABASE_URL=postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel

User:     stocksentinel
Password: password
Host:     localhost
Port:     5432
Database: stocksentinel
```

---

## Step-by-Step Diagnostic & Fix

### STEP 1: Verify PostgreSQL is Running

**Windows (PowerShell):**
```powershell
Get-Service | Where-Object { $_.Name -like "*postgres*" }
```

Expected output:
```
Status   Name                DisplayName
------   ----                -----------
Running  postgresql-x64-15   PostgreSQL Server
```

If not running, start it:
```powershell
Start-Service postgresql-x64-15  # Replace with your PostgreSQL version
```

---

### STEP 2: Test Connection as Admin (postgres user)

**Windows (PowerShell):**
```powershell
psql -U postgres -h localhost -d postgres -c "SELECT version();"
```

Expected output:
```
PostgreSQL 15.x (Windows) on ...
(1 row)
```

**If this fails:**
- PostgreSQL service not running
- postgres user password incorrect
- Port 5432 blocked by firewall
- PostgreSQL not installed

---

### STEP 3: Check if 'stocksentinel' User Exists

**Windows (PowerShell):**
```powershell
psql -U postgres -h localhost -d postgres -c "\du"
```

This lists all users. Look for `stocksentinel` in the output.

**Alternative (single query):**
```powershell
psql -U postgres -h localhost -d postgres -c "SELECT usename FROM pg_user WHERE usename='stocksentinel';"
```

Expected output if user exists:
```
 usename
-----------
 stocksentinel
(1 row)
```

**If user NOT found:** Go to STEP 5

---

### STEP 4: Check if Database Exists

**Windows (PowerShell):**
```powershell
psql -U postgres -h localhost -d postgres -c "\l"
```

Look for `stocksentinel` in the database list.

**If database NOT found:** Go to STEP 5

---

### STEP 5: Complete Setup (CREATE USER & DATABASE)

Run each command in PowerShell (as Administrator):

**Command 1: Create the user**
```powershell
psql -U postgres -h localhost -c "CREATE USER stocksentinel WITH ENCRYPTED PASSWORD 'password';"
```

Expected output: `CREATE ROLE`

**If user already exists:**
```powershell
psql -U postgres -h localhost -c "ALTER USER stocksentinel WITH ENCRYPTED PASSWORD 'password';"
```

---

**Command 2: Create the database**
```powershell
psql -U postgres -h localhost -c "CREATE DATABASE stocksentinel OWNER stocksentinel;"
```

Expected output: `CREATE DATABASE`

**If database already exists:**
```powershell
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS stocksentinel;"
psql -U postgres -h localhost -c "CREATE DATABASE stocksentinel OWNER stocksentinel;"
```

---

**Command 3: Grant privileges**
```powershell
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL PRIVILEGES ON DATABASE stocksentinel TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL ON SCHEMA public TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO stocksentinel;"
```

---

### STEP 6: Verify Connection Works

Test that the `stocksentinel` user can connect:

```powershell
psql -U stocksentinel -h localhost -d stocksentinel -c "SELECT 1;"
```

**Expected output:**
```
 ?column?
----------
        1
(1 row)
```

**If this works:** ✅ DATABASE IS FIXED

---

### STEP 7: Verify FastAPI Connection

Restart your FastAPI server:

```powershell
cd "c:\Users\acer\Downloads\stock sentinal\backend"
& ".\.venv\Scripts\Activate.ps1"
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

No database error = ✅ FIXED!

---

## Quick Fix (Copy & Paste)

**If the user and database don't exist, paste this entire block into PowerShell:**

```powershell
# Create user
psql -U postgres -h localhost -c "CREATE USER stocksentinel WITH ENCRYPTED PASSWORD 'password';"

# Create database
psql -U postgres -h localhost -c "CREATE DATABASE stocksentinel OWNER stocksentinel;"

# Grant privileges
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL PRIVILEGES ON DATABASE stocksentinel TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL ON SCHEMA public TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO stocksentinel;"

# Verify
Write-Host "Verifying connection..."
psql -U stocksentinel -h localhost -d stocksentinel -c "SELECT 1;"
Write-Host "If you see output with value '1', setup was successful!"
```

---

## Troubleshooting Matrix

| Error | Diagnosis | Fix |
|-------|-----------|-----|
| "role stocksentinel does not exist" | User wasn't created | STEP 5, Command 1 |
| "database stocksentinel does not exist" | Database wasn't created | STEP 5, Command 2 |
| "password authentication failed" | Wrong password OR user doesn't exist | STEP 5, Command 1 or reset password |
| "could not connect to database server" | PostgreSQL not running or port blocked | STEP 1, check firewall |
| "The user specified is not a valid user" | postgres user needs setup | Run commands as Administrator |
| "FATAL: pg_hba.conf rejects connection" | Authentication method misconfigured | Usually auto-configured, rarely happens |

---

## Verify Correct Configuration

### Current .env (CORRECT)
```
DATABASE_URL=postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel
```

### Connection String Format
```
postgresql+psycopg2://[user]:[password]@[host]:[port]/[database]
```

- Protocol: `postgresql+psycopg2://`
- User: `stocksentinel`
- Password: `password`
- Host: `localhost`
- Port: `5432`
- Database: `stocksentinel`

✅ Your configuration is CORRECT

---

## Advanced: Reset Everything

**If you want to start clean:**

```powershell
# DANGER: This deletes all data!

# Drop database if it exists
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS stocksentinel;"

# Drop user if it exists
psql -U postgres -h localhost -c "DROP USER IF EXISTS stocksentinel CASCADE;"

# Now run STEP 5 commands above to recreate
```

---

## Authentication Methods Reference

If you need to understand PostgreSQL authentication:

### Default Windows PostgreSQL Setup
- User: `postgres` (superuser)
- Auth method: `md5` or `scram-sha-256` (password-based)
- File: `C:\Program Files\PostgreSQL\<version>\data\pg_hba.conf`

### Our Application Setup
- User: `stocksentinel` (regular user with database privileges)
- Auth method: Password authentication (from `.env`)
- Database: `stocksentinel` (owned by the user)

---

## Files in Your Backend for Reference

- `setup_postgres.sql` - SQL commands to set up user & database
- `diagnose_postgres.py` - Python script to diagnose issues
- `POSTGRES_SETUP_WINDOWS.ps1` - Windows PowerShell setup guide
- `.env` - Your actual database configuration

---

## Next Steps After Fix

1. **Verify connection:**
   ```powershell
   psql -U stocksentinel -h localhost -d stocksentinel -c "\dt"
   ```
   Should show no tables initially (or tables if Alembic migrations ran)

2. **Run database migrations:**
   ```powershell
   cd backend
   alembic upgrade head
   ```

3. **Restart FastAPI server:**
   ```powershell
   uvicorn app.main:app --reload
   ```

4. **Check Swagger UI:**
   ```
   http://localhost:8000/docs
   ```

---

## Support

If you still get errors after following these steps:

1. Check PostgreSQL logs: `C:\Program Files\PostgreSQL\<version>\data\log\`
2. Verify firewall: Check if port 5432 is blocked
3. Check .env file: Ensure DATABASE_URL matches the user/password you created
4. Verify pg_hba.conf: Should allow password authentication (default)

