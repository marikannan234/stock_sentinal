# Docker - Standalone Command Reference
#
# Use these commands if you prefer not to use docker-compose
# (Not recommended, but provided for reference)

# ============================================================================
# PULL THE POSTGRESQL IMAGE
# ============================================================================

docker pull postgres:15-alpine

# ============================================================================
# CREATE DOCKER VOLUME FOR PERSISTENT DATA
# ============================================================================

docker volume create stocksentinel-postgres-data

# Verify volume was created
docker volume ls | Select-String stocksentinel

# ============================================================================
# RUN POSTGRESQL CONTAINER (Standalone)
# ============================================================================

# Option 1: Minimal (Just exposes port)
docker run `
  --name stocksentinel-postgres `
  -e POSTGRES_DB=stocksentinel `
  -e POSTGRES_USER=stocksentinel `
  -e POSTGRES_PASSWORD=password `
  -p 5432:5432 `
  -v stocksentinel-postgres-data:/var/lib/postgresql/data `
  -d `
  postgres:15-alpine

# Option 2: Production-ready (with restart policy and health check)
docker run `
  --name stocksentinel-postgres `
  -e POSTGRES_DB=stocksentinel `
  -e POSTGRES_USER=stocksentinel `
  -e POSTGRES_PASSWORD=password `
  -p 5432:5432 `
  -v stocksentinel-postgres-data:/var/lib/postgresql/data `
  --restart unless-stopped `
  --health-cmd="pg_isready -U stocksentinel -d stocksentinel" `
  --health-interval=10s `
  --health-timeout=5s `
  --health-retries=5 `
  -d `
  postgres:15-alpine

# ============================================================================
# VERIFY CONTAINER IS RUNNING
# ============================================================================

docker ps | Select-String stocksentinel

# Expected output:
# CONTAINER ID | IMAGE | PORTS | STATUS
# xxxxx | postgres:15-alpine | 0.0.0.0:5432->5432/tcp | Up X seconds (healthy)

# ============================================================================
# VIEW LOGS
# ============================================================================

docker logs stocksentinel-postgres

# Follow logs in real-time
docker logs -f stocksentinel-postgres

# ============================================================================
# CONNECT TO POSTGRESQL
# ============================================================================

# Using psql inside container
docker exec -it stocksentinel-postgres psql -U stocksentinel -d stocksentinel

# Inside psql:
# \dt              - list tables
# SELECT 1;        - test query
# \q               - exit

# ============================================================================
# VERIFY CONNECTION
# ============================================================================

# Test database connection
docker exec stocksentinel-postgres pg_isready -U stocksentinel -d stocksentinel

# Expected output: "accepting connections"

# ============================================================================
# STOP & REMOVE CONTAINER
# ============================================================================

# Stop container (data persists in volume)
docker stop stocksentinel-postgres

# Start stopped container
docker start stocksentinel-postgres

# Remove container (data still in volume)
docker rm stocksentinel-postgres

# Remove container AND delete all data (DANGEROUS!)
docker rm stocksentinel-postgres
docker volume rm stocksentinel-postgres-data

# ============================================================================
# USEFUL PATTERN: Start and Keep Running
# ============================================================================

# In one PowerShell window, start the container
docker run `
  --name stocksentinel-postgres `
  -e POSTGRES_DB=stocksentinel `
  -e POSTGRES_USER=stocksentinel `
  -e POSTGRES_PASSWORD=password `
  -p 5432:5432 `
  -v stocksentinel-postgres-data:/var/lib/postgresql/data `
  postgres:15-alpine

# Then in another window, run your FastAPI app:
# cd backend
# .\.venv\Scripts\Activate.ps1
# uvicorn app.main:app --reload

# When done, Ctrl+C in Docker window to stop container

# ============================================================================
# WHY USE docker-compose INSTEAD?
# ============================================================================

<#
docker-compose is RECOMMENDED because:

1. Easier to manage (single file vs. long commands)
2. Can manage multiple services (PostgreSQL + Backend + Frontend)
3. Automatic restart and health checks configured
4. Version control friendly (check docker-compose.yml into git)
5. Environment isolation via services and networks
6. Standardized across team members

Use standalone docker commands only if:
- You're just learning Docker
- You need very simple, one-off containers
- You have specific Docker-only requirements
#>

# ============================================================================
# COMPARISON: Standalone vs docker-compose
# ============================================================================

<#
STANDALONE COMMAND (what we show above):
  docker run -name stocksentinel-postgres -e POSTGRES_DB=... -p 5432:5432 ...

DOCKER-COMPOSE (RECOMMENDED):
  docker-compose up -d db
  
  Advantages:
  ✓ Shorter command
  ✓ All config in docker-compose.yml (version controlled)
  ✓ Easy to add more services
  ✓ Automatic networks and volumes
  ✓ Health checks built-in
  ✓ Better team coordination
#>

# ============================================================================
# RECOMMENDATION
# ============================================================================

# Use docker-compose instead:
# 
# docker-compose up -d db
# 
# It's cleaner, more maintainable, and production-ready!

