# Docker PostgreSQL Setup Guide for Stock Sentinel

## Overview

This guide explains how to use Docker to run PostgreSQL for the Stock Sentinel backend.

**Advantages of Docker:**
- ✅ No local PostgreSQL installation needed
- ✅ Isolated, reproducible environment
- ✅ Easy to start/stop/reset
- ✅ Same environment for all developers
- ✅ Production-ready PostgreSQL 15

---

## Prerequisites

1. **Docker Desktop** installed and running
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version` and `docker-compose --version`

2. **docker-compose.yml** in your project root (already provided)

---

## Quick Start

### Option 1: Start Only PostgreSQL (Recommended for Development)

Start just the database container:

```powershell
cd c:\Users\acer\Downloads\stock sentinal

# Start PostgreSQL in background
docker-compose up -d db

# Wait for database to be ready (about 5-10 seconds)
Start-Sleep -Seconds 5

# Verify it's running
docker-compose logs db
```

**Expected output:**
```
stocksentinel-db  | LOG:  database system is ready to accept connections
```

Then run your FastAPI server locally:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

---

### Option 2: Start All Services (Backend + Frontend + PostgreSQL)

Start everything in Docker:

```powershell
cd c:\Users\acer\Downloads\stock sentinal

# Build and start all services
docker-compose up --build

# Or in background mode
docker-compose up --build -d
```

**Access your application:**
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432

---

## Essential Docker Commands

### Start & Stop

```powershell
# Start services in background
docker-compose up -d

# Start only PostgreSQL
docker-compose up -d db

# Start and build (if Dockerfile changed)
docker-compose up --build -d

# Stop all services
docker-compose down

# Stop and remove all data (DANGEROUS!)
docker-compose down -v
```

### Check Status

```powershell
# List running containers
docker-compose ps

# Check if PostgreSQL is healthy
docker-compose ps db

# Example output:
# NAME                    STATUS
# stocksentinel-db        Up 2 minutes (healthy)
```

### View Logs

```powershell
# View PostgreSQL logs
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f db

# View all service logs
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail=50 db
```

### Connect to PostgreSQL

**From command line:**

```powershell
# Connect to PostgreSQL inside the container
docker-compose exec db psql -U stocksentinel -d stocksentinel

# Then you can run SQL:
# \dt              (list tables)
# \du              (list users)
# SELECT * FROM ...

# Exit:
# \q or Ctrl+D
```

**From outside (using psql on your machine):**

```powershell
# If you have psql installed locally:
psql -U stocksentinel -h localhost -d stocksentinel -W

# (It will ask for password: type 'password')
```

---

## Verify PostgreSQL Connection

### Method 1: Check Container Health

```powershell
docker-compose ps
```

Look for the `STATUS` column. Should show: `Up ... (healthy)`

### Method 2: Run Health Check

```powershell
docker-compose exec db pg_isready -U stocksentinel -d stocksentinel
```

Expected output: `accepting connections`

### Method 3: Test from FastAPI

When your FastAPI server starts, it will try to connect to PostgreSQL. If it succeeds, you'll see:

```
[INFO] [app.main] - Exception handlers configured
[INFO] [app.main] - CORS configured with origins: [...]
[INFO] [app.main] - All routes registered (StockSentinel API is ready to serve requests)
```

No database errors = ✅ Connected!

---

## Database Configuration

### Current Setup (from docker-compose.yml)

| Setting | Value |
|---------|-------|
| User | `stocksentinel` |
| Password | `password` |
| Database | `stocksentinel` |
| Port | `5432` |
| Host (from Docker) | `db` |
| Host (from localhost) | `localhost` |

### Connection Strings

**From inside Docker (backend container):**
```
postgresql+psycopg2://stocksentinel:password@db:5432/stocksentinel
```

**From your local machine:**
```
postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel
```

**In your .env file:**
```
DATABASE_URL=postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel
```
(Uses `localhost` because you're running from outside Docker)

---

## Common Tasks

### Create a Database Backup

```powershell
# Create a backup of the database
docker-compose exec db pg_dump -U stocksentinel stocksentinel > backup.sql

# File 'backup.sql' is created in current directory
```

### Restore from Backup

```powershell
# Restore database from backup
docker-compose exec -T db psql -U stocksentinel stocksentinel < backup.sql
```

### Reset Database (Delete All Data)

```powershell
# Stop and remove the container and volume
docker-compose down -v

# Start fresh (new empty database)
docker-compose up -d db
```

### Run Database Migration

```powershell
# Connect to running database
cd backend
.\.venv\Scripts\Activate.ps1

# Run Alembic migrations
alembic upgrade head
```

### View Database Tables

```powershell
# Connect to PostgreSQL
docker-compose exec db psql -U stocksentinel -d stocksentinel

# Inside psql:
\dt                    # List all tables
\d users               # Describe 'users' table structure
SELECT * FROM users;   # Query data
\q                     # Exit
```

---

## Troubleshooting

### Error: "Cannot connect to Docker daemon"

**Cause:** Docker Desktop is not running

**Fix:** Start Docker Desktop application

---

### Error: "Port 5432 is already in use"

**Cause:** PostgreSQL already running locally or container already running

**Options:**

1. Stop the local PostgreSQL: 
   ```powershell
   # Check what's using port 5432
   Get-NetTCPConnection -LocalPort 5432
   ```

2. Or use a different port in docker-compose.yml:
   ```yaml
   ports:
     - "5433:5432"  # Use 5433 instead of 5432
   ```

3. Or stop the Docker container:
   ```powershell
   docker-compose down
   ```

---

### Error: "database stocksentinel does not exist"

**Cause:** Container started but initialization incomplete

**Fix:**

```powershell
# Check container status
docker-compose ps db

# If not healthy, check logs
docker-compose logs db

# Wait 10-15 seconds and try again
Start-Sleep -Seconds 15
docker-compose ps db
```

---

### Error: "password authentication failed"

**Cause:** Wrong password or environment mismatch

**Check:**
1. Verify password in docker-compose.yml matches .env
2. Check docker-compose.yml:
   ```yaml
   POSTGRES_PASSWORD: password
   ```
3. Check .env:
   ```
   DATABASE_URL=...password@localhost:5432...
   ```

If mismatch: Update both, then `docker-compose down -v && docker-compose up -d db`

---

### Error: "Container exited with code 1"

**Cause:** Database initialization failed

**Fix:**

```powershell
# Check logs
docker-compose logs db

# If initialization error, reset:
docker-compose down -v

# Remove image to force rebuild
docker rmi postgres:15-alpine

# Start fresh
docker-compose up -d db
```

---

### Check PostgreSQL Logs

```powershell
# View logs
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f db

# View last 100 lines
docker-compose logs --tail=100 db
```

---

## Advanced: PostgreSQL Configuration

### Custom PostgreSQL Settings

Edit docker-compose.yml to add PostgreSQL command flags:

```yaml
services:
  db:
    image: postgres:15-alpine
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"
    # ... rest of config
```

### Custom Initialization Scripts

Create `docker/init-db/init.sql`:

```sql
-- Initialize custom schemas or data
CREATE SCHEMA IF NOT EXISTS custom;
GRANT ALL ON SCHEMA custom TO stocksentinel;
```

Then update docker-compose.yml:

```yaml
volumes:
  - ./docker/init-db/:/docker-entrypoint-initdb.d/
```

---

## Docker Compose File Breakdown

```yaml
version: '3.8'                    # Docker Compose version

services:                         # Define services
  db:                            # Service name
    image: postgres:15-alpine    # Use official PostgreSQL image
    container_name: stocksentinel-db  # Human-readable name
    
    ports:                       # Map ports: host:container
      - "5432:5432"
    
    environment:                 # Set environment variables
      POSTGRES_DB: stocksentinel       # Database name
      POSTGRES_USER: stocksentinel     # User
      POSTGRES_PASSWORD: password      # Password
    
    volumes:                     # Mount volumes for persistence
      - postgres_data:/var/lib/postgresql/data
    
    healthcheck:                 # Check if service is healthy
      test: ["CMD-SHELL", "pg_isready -U stocksentinel -d stocksentinel"]
      interval: 10s              # Check every 10 seconds
      timeout: 5s                # Timeout after 5 seconds
      retries: 5                 # Fail after 5 failed checks
    
    restart: unless-stopped      # Auto-restart on failure

volumes:                         # Define named volumes
  postgres_data:
    driver: local

networks:                        # Define Docker networks
  stocksentinel-network:
    driver: bridge
```

---

## Switching Between Docker and Local PostgreSQL

### Use Local PostgreSQL:
1. Run PostgreSQL locally: `psql -U postgres`
2. Update docker-compose.yml: comment out `db` service
3. Keep `.env` with: `DATABASE_URL=postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel`

### Use Docker PostgreSQL:
1. Keep docker-compose.yml as is
2. Run: `docker-compose up -d db`
3. Keep `.env` unchanged

---

## Production Deployment Considerations

For production, you should:

1. **Use strong passwords** (not `password`)
   ```yaml
   POSTGRES_PASSWORD: ${DB_PASSWORD}  # Use environment variable
   ```

2. **Enable backups:**
   ```powershell
   # Automated daily backup script
   docker-compose exec db pg_dump -U stocksentinel stocksentinel > backups/stocksentinel_$(date +%Y%m%d).sql
   ```

3. **Set resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

4. **Use health checks** (already configured)

5. **Enable persistent volumes** (already configured)

---

## Useful Links

- PostgreSQL Docker Hub: https://hub.docker.com/_/postgres
- Docker Compose Documentation: https://docs.docker.com/compose/
- PostgreSQL Documentation: https://www.postgresql.org/docs/15/

