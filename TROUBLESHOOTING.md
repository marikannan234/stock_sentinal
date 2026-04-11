# Troubleshooting Guide - Stock Sentinel

## Quick Reference

### 🔴 Common Issues & Solutions

| Problem | Symptoms | Solution |
|---------|----------|----------|
| **Containers not running** | 404 errors, can't connect | `docker compose up -d` |
| **Backend crashes on startup** | Logs show errors | `docker logs stocksentinel-backend` |
| **WebSocket won't connect** | Alerts not updating in UI | Check `ws://localhost:8000/ws/alerts` |
| **Migration failed** | App won't start | `docker exec stocksentinel-backend alembic current` |
| **Database connection error** | "psycopg2 connection refused" | Ensure PostgreSQL container is healthy |
| **Frontend shows 404** | `http://localhost:3000` not loading | `docker logs stocksentinel-frontend` |
| **WhatsApp alerts not sending** | No WhatsApp messages received | Check Twilio credentials in `.env` |

---

## Detailed Troubleshooting

### 1️⃣ Containers Not Running

**Symptoms:**
- `GET http://localhost:8000/health 404`
- Connection refused on port 8000 or 3000
- Docker command shows "No such container"

**Solutions:**

```bash
# Check if containers exist
docker ps -a

# Start containers
docker compose up -d

# Check specific logs
docker logs stocksentinel-backend
docker logs stocksentinel-frontend
docker logs stocksentinel-db

# Rebuild if needed
docker compose build
docker compose up -d
```

**If still failing:**
```bash
# Full reset (WARNING: loses data)
docker compose down -v
docker compose build
docker compose up -d
```

---

### 2️⃣ Backend Crashes on Startup

**Symptoms:**
- `docker logs stocksentinel-backend` shows errors
- Container exits immediately
- App doesn't start

**Debug Steps:**

```bash
# View full logs (last 100 lines)
docker logs stocksentinel-backend | tail -100

# Common errors:
# - "no such module" → missing dependency in requirements.txt
# - "database connection refused" → db not ready
# - "migration error" → see "Migration Issues" section
```

**Check if database is ready:**
```bash
docker exec stocksentinel-db pg_isready -U stocksentinel
# Output: accepting connections (✅) or rejecting connections (❌)

# If rejecting, wait and retry
Start-Sleep -Seconds 5
docker exec stocksentinel-db pg_isready -U stocksentinel
```

**Restart backend only:**
```bash
docker restart stocksentinel-backend
```

---

### 3️⃣ Migration Issues

**Symptom: "Migration did not apply"**

```bash
# Check current revision
docker exec stocksentinel-backend alembic current

# View migration history
docker exec stocksentinel-backend alembic history

# View full logs during startup
docker logs stocksentinel-backend | grep -i "migration"
```

**Most Common: Migration Syntax Error**

```bash
# View the migration file that failed
ls backend/alembic/versions/

# Check what's in the migration
cat backend/alembic/versions/0005_*.py

# If auto-generated migration is wrong:
# 1. Delete the bad migration
# 2. Fix the model
# 3. Rebuild docker image
# 4. Restart containers
```

**Solution if migration is stuck:**

```bash
# Downgrade to previous version
docker exec stocksentinel-backend alembic downgrade -1

# View current revision
docker exec stocksentinel-backend alembic current

# Then investigate why the migration failed
```

---

### 4️⃣ WebSocket Connection Failed

**Symptoms:**
- Alerts don't appear in real-time
- Browser console shows WebSocket error
- Connection refused on `ws://localhost:8000/ws/alerts`

**Check backend WebSocket endpoint:**
```bash
# Verify endpoint is responding
docker exec stocksentinel-backend curl -i http://localhost:8000/ws/alerts

# Check backend logs for connection errors
docker logs stocksentinel-backend | grep -i "websocket"
```

**Check frontend environment variable:**
```bash
# Verify frontend has correct WS URL
docker exec stocksentinel-frontend env | grep WS_URL

# Should output: NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**Fix frontend WebSocket URL:**
1. Edit `.env` or `.env.local` in frontend directory:
   ```
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

2. Rebuild frontend:
   ```bash
   docker compose build frontend
   docker compose up -d
   ```

---

### 5️⃣ Database Connection Issues

**Symptoms:**
- "psycopg2.Error: could not connect to server"
- "Connection refused on port 5432"
- Backend can't communicate with database

**Diagnose:**

```bash
# Check if DB container is healthy
docker ps | grep stocksentinel-db
# Output should show "Healthy" status

# Test connection from backend container
docker exec stocksentinel-backend psql -h stocksentinel-db -U stocksentinel -d stocksentinel -c "SELECT 1"
# Output: 1 = ✅ Connected

# If failed, check DB logs
docker logs stocksentinel-db

# Check if port 5432 is accessible
docker exec stocksentinel-backend nc -zv stocksentinel-db 5432
```

**Fix Database Issues:**

```bash
# Option 1: Restart database
docker restart stocksentinel-db

# Wait for it to be healthy (max 30 seconds)
docker exec stocksentinel-db pg_isready -U stocksentinel

# Option 2: Rebuild database volume
docker compose down -v
docker compose up -d
# ⚠️ WARNING: This deletes all data!
```

---

### 6️⃣ WhatsApp Alerts Not Sending

**Symptoms:**
- Stock alerts trigger but no WhatsApp received
- No errors in logs (silent failure)
- Twilio shows 0 messages sent

**Verify Twilio Configuration:**

```bash
# Check environment variables in backend container
docker exec stocksentinel-backend env | grep TWILIO

# Should output:
# TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxx
# TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxx
# TWILIO_WHATSAPP_NUMBER=+1xxxxxxxxxx
```

**If any are missing:**
1. Add to `.env` file in backend
2. Rebuild backend: `docker compose build backend`
3. Restart: `docker compose up -d`

**Check if alerts are triggering:**

```bash
# View alert service logs
docker logs stocksentinel-backend | grep -i "alert\|whatsapp"

# Look for:
# - "Checking alerts..." (scheduler running)
# - "Trigger alert" (alert fired)
# - "Sending WhatsApp" (WhatsApp attempt)
```

**Test WhatsApp service manually:**

```bash
# Ensure port 8000 is open
curl http://localhost:8000/health

# Create test alert and check logs
docker logs stocksentinel-backend --tail 50
```

**If still not working:**
- Check Twilio account is active (not trial/sandboxed)
- Verify phone number is registered in Twilio WhatsApp sandbox
- Test with test endpoint if available

---

### 7️⃣ Frontend Site Won't Load

**Symptoms:**
- `http://localhost:3000` shows blank page or error
- Console shows 404 or network errors
- "Cannot GET /"

**Check frontend container:**

```bash
# View logs
docker logs stocksentinel-frontend

# Look for:
# - "ready - started server on" = ✅ Running
# - "error" or "ERR!" = ❌ Issue

# Restart frontend
docker restart stocksentinel-frontend
```

**Check if Next.js built successfully:**

```bash
# Rebuild frontend
docker compose build frontend

# Check build logs for errors
docker logs --build stocksentinel-frontend
```

**Clear Next.js cache:**
```bash
# Inside docker
docker exec stocksentinel-frontend sh -c "rm -rf .next && npm run build"

# Or rebuild
docker compose down
docker compose build --no-cache frontend
docker compose up -d
```

**Check port is correct:**
- Frontend should be on `http://localhost:3000`
- Backend API on `http://localhost:8000`
- WebSocket on `ws://localhost:8000`

---

### 8️⃣ Port Already in Use

**Symptom: "Address already in use"**

**Identify what's using the port:**

```powershell
# Check port 8000 (backend)
netstat -ano | findstr ":8000"

# Check port 3000 (frontend)
netstat -ano | findstr ":3000"

# Check port 5432 (database)
netstat -ano | findstr ":5432"
```

**Solutions:**

```bash
# Option 1: Stop conflicting process
# Kill the process using PID from above
taskkill /PID 12345 /F

# Option 2: Stop all Docker containers
docker compose down

# Option 3: Use different port
docker run -p 8001:8000 stocksentinel-backend
# Then rebuild docker-compose.yml with new port
```

---

## System Health Check

**Run this to diagnose the system:**

```bash
echo "=== DOCKER STATUS ==="
docker ps -a
echo ""
echo "=== CONTAINER HEALTH ==="
docker exec stocksentinel-db pg_isready -U stocksentinel
echo ""
echo "=== BACKEND LOGS (Last 10 lines) ==="
docker logs stocksentinel-backend | tail -10
echo ""
echo "=== MIGRATION STATUS ==="
docker exec stocksentinel-backend alembic current
echo ""
echo "=== API HEALTH ==="
curl -s http://localhost:8000/health | jq .
echo ""
echo "=== CONTAINERS RESTART POLICY ==="
docker inspect stocksentinel-backend --format='{{.HostConfig.RestartPolicy}}'
```

---

## Restart Procedures

### Quick Restart (keep data)
```bash
docker compose restart
```

### Full Restart (keep data)
```bash
docker compose down
docker compose up -d
```

### Clean Restart (⚠️ loses data)
```bash
docker compose down -v
docker compose build
docker compose up -d
```

### Single Service Restart
```bash
docker compose restart stocksentinel-backend
docker compose restart stocksentinel-frontend
docker compose restart stocksentinel-db
```

---

## Log Analysis

### View Logs for Specific Service
```bash
# Last 50 lines
docker logs stocksentinel-backend | tail -50

# Follow logs in real-time (Ctrl+C to exit)
docker logs -f stocksentinel-backend

# Search for errors
docker logs stocksentinel-backend 2>&1 | grep -i "error"
```

### Search Patterns
```bash
# Migration logs
docker logs stocksentinel-backend | grep -i "migration"

# Alert logs
docker logs stocksentinel-backend | grep -i "alert"

# WebSocket logs
docker logs stocksentinel-backend | grep -i "websocket"

# WhatsApp logs
docker logs stocksentinel-backend | grep -i "whatsapp\|twilio"

# Database logs
docker logs stocksentinel-db | grep -i "error"
```

---

## Performance Troubleshooting

### High CPU Usage
```bash
# Check which container
docker stats --no-stream

# Restart heavy container
docker restart stocksentinel-backend
```

### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart container
docker restart stocksentinel-frontend
```

### Database Slow Queries
```bash
# Check database size
docker exec stocksentinel-db psql -U stocksentinel -d stocksentinel -c "SELECT pg_size_pretty(pg_database_size('stocksentinel'))"

# Vacuum database
docker exec stocksentinel-db psql -U stocksentinel -d stocksentinel -c "VACUUM ANALYZE"
```

---

## When to Contact Support

🚨 **Create an issue/contact support if:**
1. Migrations fail even after following guide
2. Database corruption errors
3. Persistent connection refused errors
4. Multiple container crashes in a row
5. Data loss or integrity issues

📋 **Provide these logs:**
1. `docker logs stocksentinel-backend 2>&1 | tail -200`
2. `docker logs stocksentinel-db 2>&1 | tail -200`
3. `docker logs stocksentinel-frontend 2>&1 | tail -200`
4. Output of: `docker ps -a` and `docker compose config`

---

**Last Updated:** 2026-04-10  
**Version:** 1.0  
**Status:** Production Ready
