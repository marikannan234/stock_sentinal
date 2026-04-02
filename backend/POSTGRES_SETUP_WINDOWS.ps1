# PostgreSQL Database Setup for Stock Sentinel - Windows PowerShell Guide
# 
# This guide provides step-by-step instructions to:
# 1. Check PostgreSQL installation
# 2. Create the database user
# 3. Create the database
# 4. Grant privileges
# 5. Verify connection

# ============================================================================
# PRE-REQUISITES
# ============================================================================
# 
# 1. PostgreSQL must be installed on your system
#    - Download from: https://www.postgresql.org/download/windows/
#    - Default port: 5432
#    - Default admin user: postgres
#
# 2. PostgreSQL service must be running
#    - Check: Services app -> PostgreSQL -> Status
#    - Or: Get-Service postgresql-x64-<version>
#
# 3. You need the 'postgres' user password
#    - Set during PostgreSQL installation

# ============================================================================
# STEP 1: Verify PostgreSQL is Running
# ============================================================================
Write-Host "`n=== STEP 1: Check PostgreSQL Service ===" -ForegroundColor Cyan

# Check if PostgreSQL service exists and is running
Get-Service | Where-Object { $_.Name -like "*postgres*" } | Select-Object Name, Status

# If not running, start it:
# Start-Service -Name <PostgreSQL-Service-Name>

# ============================================================================
# STEP 2: Check PostgreSQL is Accessible
# ============================================================================
Write-Host "`n=== STEP 2: Test PostgreSQL Connection ===" -ForegroundColor Cyan

# Test connection to default postgres database
Write-Host "Testing connection as 'postgres' user..."
Write-Host "Command: psql -U postgres -h localhost -d postgres -c 'SELECT version();'"
Write-Host "If this fails, you may need to:"
Write-Host "  1. Enter the postgres password when prompted"
Write-Host "  2. Ensure PostgreSQL service is running"
Write-Host "  3. Check port 5432 is not blocked by firewall`n"

# ============================================================================
# STEP 3: Create the Database User (as postgres)
# ============================================================================
Write-Host "=== STEP 3: Create Database User ===" -ForegroundColor Cyan
Write-Host "Run this command in PowerShell:"
Write-Host @"
psql -U postgres -h localhost -c `
  "CREATE USER stocksentinel WITH ENCRYPTED PASSWORD 'password';"
"@
Write-Host ""
Write-Host "Alternative (if user already exists):"
Write-Host @"
psql -U postgres -h localhost -c `
  "ALTER USER stocksentinel WITH ENCRYPTED PASSWORD 'password';"
"@

# ============================================================================
# STEP 4: Create the Database
# ============================================================================
Write-Host "`n=== STEP 4: Create Database ===" -ForegroundColor Cyan
Write-Host "Run this command in PowerShell:"
Write-Host @"
psql -U postgres -h localhost -c `
  "CREATE DATABASE stocksentinel OWNER stocksentinel;"
"@
Write-Host ""
Write-Host "If database already exists, drop it first:"
Write-Host @"
psql -U postgres -h localhost -c `
  "DROP DATABASE IF EXISTS stocksentinel;"
"@

# ============================================================================
# STEP 5: Grant Privileges
# ============================================================================
Write-Host "`n=== STEP 5: Grant Database Privileges ===" -ForegroundColor Cyan
Write-Host "Run this command in PowerShell:"
Write-Host @"
psql -U postgres -h localhost -d stocksentinel -c `
  "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO stocksentinel;"
"@

# ============================================================================
# STEP 6: Verify the Connection
# ============================================================================
Write-Host "`n=== STEP 6: Verify Connection ===" -ForegroundColor Cyan
Write-Host "Test that the stocksentinel user can connect:"
Write-Host @"
psql -U stocksentinel -h localhost -d stocksentinel -c "SELECT 1;"
"@
Write-Host ""
Write-Host "If successful, you should see:"
Write-Host "  ?column?"
Write-Host "  ----------"
Write-Host "         1"
Write-Host "(1 row)`n"

# ============================================================================
# COMPLETE SETUP SCRIPT (Copy and run in PowerShell)
# ============================================================================
Write-Host "=== COMPLETE SETUP SCRIPT ===" -ForegroundColor Yellow
Write-Host "Copy this entire block and paste into PowerShell:`n"

$setupScript = @"
# Step 1: Create user
psql -U postgres -h localhost -c "CREATE USER stocksentinel WITH ENCRYPTED PASSWORD 'password';"

# Step 2: Create database
psql -U postgres -h localhost -c "CREATE DATABASE stocksentinel OWNER stocksentinel;"

# Step 3: Grant privileges
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO stocksentinel;"
psql -U postgres -h localhost -d stocksentinel -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO stocksentinel;"

# Step 4: Verify
Write-Host "Verifying connection..."
psql -U stocksentinel -h localhost -d stocksentinel -c "SELECT 1;"
Write-Host "If you see output with a single value '1', setup was successful!"
"@

Write-Host $setupScript -ForegroundColor Green

# ============================================================================
# TROUBLESHOOTING
# ============================================================================
Write-Host "`n=== TROUBLESHOOTING ===" -ForegroundColor Yellow

Write-Host @"

ERROR: "role stocksentinel does not exist"
FIX: Run Step 3 to create the user

ERROR: "database stocksentinel does not exist"  
FIX: Run Step 4 to create the database

ERROR: "password authentication failed"
FIX: 
  1. Check the password in .env matches 'password'
  2. Reset password: ALTER USER stocksentinel WITH PASSWORD 'password';
  3. Check pg_hba.conf allows password authentication (usually does)

ERROR: "could not connect to database server"
FIX:
  1. Check PostgreSQL service is running
  2. Verify port 5432 is not blocked
  3. Check firewall settings

ERROR: "The user specified is not a valid user" (psql)
FIX: PostgreSQL user 'postgres' doesn't have login permission
  - Use: psql -U postgres (if asking for password, postgres user is set up)

"@

# ============================================================================
# DIRECT SQL FILE EXECUTION (Alternative)
# ============================================================================
Write-Host "`n=== ALTERNATIVE: Use SQL File ===" -ForegroundColor Cyan
Write-Host @"
If you have both setup_postgres.sql and diagnose_postgres.py in your backend:

psql -U postgres -h localhost -f setup_postgres.sql

This executes all SQL commands in the file automatically.
"@

Write-Host "`n=== SETUP COMPLETE ===" -ForegroundColor Green
Write-Host "After running the commands above, restart your FastAPI server:"
Write-Host "  cd backend"
Write-Host "  .venv\Scripts\Activate.ps1"
Write-Host "  uvicorn app.main:app --reload`n"
