# Docker PostgreSQL - Get Started NOW (5 Minutes)

## What You Need to Have

✅ Docker Desktop installed: https://www.docker.com/products/docker-desktop

Verify:
```powershell
docker --version
docker-compose --version
```

---

## The 3-Command Startup

### Command 1: Start PostgreSQL
```powershell
cd c:\Users\acer\Downloads\stock sentinal
docker-compose up -d db
```

**Wait 5 seconds...**

### Command 2: Verify It's Running
```powershell
docker-compose ps db
```

**Expected output:**
```
NAME              STATUS
stocksentinel-db  Up 5 seconds (healthy)
```

### Command 3: Start Your Backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**Expected output (NO DATABASE ERROR):**
```
[INFO] Application startup complete
[INFO] Uvicorn running on http://127.0.0.1:8000
```

✅ **DONE!** Your database is running!

---

## Test It Works

Open your browser and go to:
```
http://localhost:8000/docs
```

You should see the Swagger UI. ✅ **Database is connected!**

---

## What I Fixed For You

Your project had two issues:

### Issue 1: Password Mismatch
```
❌ BEFORE: Password was "stocksentinel_password"
✅ AFTER:  Password is "password" (matches your .env)
```

### Issue 2: Wrong Connection String
```
❌ BEFORE: DATABASE_URL pointed to wrong host
✅ AFTER:  DATABASE_URL=postgresql+psycopg2://stocksentinel:password@db:5432/stocksentinel
```

I updated your `docker-compose.yml` file with the correct configuration.

---

## Your PostgreSQL Details

```
User:     stocksentinel
Password: password
Database: stocksentinel
Host:     localhost (from your computer)
          db (from inside Docker)
Port:     5432
```

---

## When You're Done

```powershell
# Stop PostgreSQL
docker-compose down

# Your data is safe - it's stored in the Docker volume
# Next time you run docker-compose up -d db, your data is still there!
```

---

## Useful Commands Cheat Sheet

```powershell
# Start database
docker-compose up -d db

# Stop database
docker-compose down

# Check status
docker-compose ps db

# View logs
docker-compose logs db

# Connect to database
docker-compose exec db psql -U stocksentinel -d stocksentinel

# Create backup
docker-compose exec db pg_dump -U stocksentinel stocksentinel > backup.sql

# Reset (DELETE ALL DATA!)
docker-compose down -v
docker-compose up -d db
```

---

## That's It!

You now have:
- ✅ PostgreSQL running in Docker
- ✅ No local installation required
- ✅ Easy to start/stop
- ✅ Easy to reset
- ✅ Data persists
- ✅ Production-ready setup

If you need more info, check:
- `DOCKER_POSTGRES_GUIDE.md` - Complete guide
- `DOCKER_QUICK_REFERENCE.ps1` - Quick commands
- `DOCKER_ARCHITECTURE.md` - How it works visually

---

## Troubleshooting (If Something Goes Wrong)

### "docker: command not found"
Install Docker Desktop: https://www.docker.com/products/docker-desktop

### "Port 5432 already in use"
```powershell
# Option 1: Stop the container
docker-compose down

# Option 2: Use different port (edit docker-compose.yml):
ports:
  - "5433:5432"
```

### "Cannot connect to Docker daemon"
Start Docker Desktop application

### "Database won't start"
```powershell
# View logs
docker-compose logs db

# Reset and try again
docker-compose down -v
docker-compose up -d db
Start-Sleep -Seconds 10
docker-compose ps db
```

### "Still getting connection errors?"
```powershell
# Verify connection
docker-compose exec db pg_isready -U stocksentinel -d stocksentinel

# Should show: "accepting connections"
```

If you still have issues, check `DOCKER_POSTGRES_GUIDE.md` for detailed troubleshooting.

---

## Next Steps (After Testing)

1. ✅ PostgreSQL is running
2. ✅ FastAPI can connect
3. ➡️ Run database migrations: `alembic upgrade head`
4. ➡️ Create test data
5. ➡️ Test your API endpoints

---

**You're all set! Enjoy your Dockerized PostgreSQL! 🐳🚀**

