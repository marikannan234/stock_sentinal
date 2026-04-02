# Docker PostgreSQL - Windows PowerShell Quick Reference

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

# 1. Verify Docker is installed
docker --version
docker-compose --version

# 2. Navigate to project root
cd c:\Users\acer\Downloads\stock sentinal

# ============================================================================
# START POSTGRESQL IN DOCKER
# ============================================================================

# Start PostgreSQL container (recommended for local development)
docker-compose up -d db

# Wait for database to be ready (usually 5-10 seconds)
Start-Sleep -Seconds 5

# Verify container is running and healthy
docker-compose ps db

# Expected status: "Up X minutes (healthy)"

# ============================================================================
# START FASTAPI BACKEND (After Docker PostgreSQL is running)
# ============================================================================

cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Expected output (no database error indicates successful connection):
# [INFO] Application startup complete
# [INFO] Uvicorn running on http://127.0.0.1:8000

# ============================================================================
# CHECK STATUS
# ============================================================================

# List all running containers
docker-compose ps

# Check PostgreSQL status specifically
docker-compose ps db

# View container logs
docker-compose logs db

# Follow logs in real-time (Ctrl+C to stop)
docker-compose logs -f db

# ============================================================================
# CONNECT TO DATABASE
# ============================================================================

# Connect via psql inside container
docker-compose exec db psql -U stocksentinel -d stocksentinel

# Inside psql prompt:
# \dt              - list tables
# \du              - list users
# \l               - list databases
# SELECT 1;        - test query
# \q               - exit

# ============================================================================
# VERIFY CONNECTION FROM LOCALHOST
# ============================================================================

# Test with pg_isready
docker-compose exec db pg_isready -U stocksentinel -d stocksentinel

# Expected output: "accepting connections"

# ============================================================================
# STOP & CLEANUP
# ============================================================================

# Stop containers (data persists)
docker-compose down

# Stop containers AND delete all data (DANGEROUS!)
docker-compose down -v

# Stop all services
docker-compose stop

# Start stopped services
docker-compose start

# Remove a specific container
docker-compose rm db

# ============================================================================
# USEFUL COMMANDS
# ============================================================================

# View PostgreSQL health status
docker-compose exec db pg_isready -U stocksentinel

# Create database backup
docker-compose exec db pg_dump -U stocksentinel stocksentinel > backup.sql

# Restore from backup
docker-compose exec -T db psql -U stocksentinel stocksentinel < backup.sql

# View specific number of log lines
docker-compose logs --tail=50 db

# Clear all Docker containers and images (DANGEROUS!)
# docker system prune -a

# Remove only stopped containers
docker container prune -f

# ============================================================================
# DATABASE INFORMATION
# ============================================================================

# Connection details:
# User:     stocksentinel
# Password: password
# Database: stocksentinel
# Host:     localhost (from your machine)
#           db (from inside Docker)
# Port:     5432

# .env connection string:
# DATABASE_URL=postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel

# Docker connection string (in backend container):
# DATABASE_URL=postgresql+psycopg2://stocksentinel:password@db:5432/stocksentinel

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Port 5432 already in use?
# Check: Get-NetTCPConnection -LocalPort 5432
# Or use port 5433 in docker-compose.yml

# Container won't start?
docker-compose logs db

# Reset container (deletes all data!)
docker-compose down -v
docker-compose up -d db

# Container exited?
docker-compose logs db
docker-compose up -d db --force-recreate

# ============================================================================
# START ALL SERVICES (Optional - for full Docker stack)
# ============================================================================

# Start everything: PostgreSQL + Backend + Frontend
docker-compose up --build -d

# Access:
# - Backend: http://localhost:8000
# - Swagger: http://localhost:8000/docs
# - Frontend: http://localhost:3000
# - Database: localhost:5432

# ============================================================================
# WORKFLOW EXAMPLE
# ============================================================================

# 1. Start PostgreSQL
docker-compose up -d db
Start-Sleep -Seconds 5

# 2. Verify it's healthy
docker-compose ps db

# 3. Start your FastAPI backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# 4. Open browser to http://localhost:8000/docs

# 5. When done, stop PostgreSQL:
docker-compose down

