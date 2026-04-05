## 🚀 QUICK START - Get Stock Sentinel Running

> Get from zero to fully functional trading platform in 5 minutes

---

## Prerequisites

- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- PostgreSQL 13+ (via Docker recommended)
- Git

---

## Option 1: Docker (Recommended for Production)

### 1. Start All Services
```bash
cd stock\ sentinal
docker-compose up --build
```

This starts:
- PostgreSQL database on port 5432
- FastAPI backend on port 8000
- Frontend on port 3000

### 2. Verify Services
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Database: localhost:5432

**Done!** 🎉 Skip to "Testing" section below.

---

## Option 2: Local Development Setup

### Backend Setup (Terminal 1)

```bash
cd backend

# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
alembic upgrade head

# 5. Run backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Output should show:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Frontend Setup (Terminal 2)

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Run development server
npm run dev
```

**Output should show:**
```
  ▲ Next.js 15.5.14
  - Local:        http://localhost:3000
```

---

## Option 3: PostgreSQL Setup (If Not Using Docker)

### Windows
```bash
# Install PostgreSQL (if not already installed)
# Download from https://www.postgresql.org/download/windows/

# Create database
psql -U postgres -c "CREATE DATABASE stock_sentinel;"

# Verify connection
psql -U postgres -d stock_sentinel -c "\dt"
```

### macOS
```bash
# Install via Homebrew
brew install postgresql

# Start service
brew services start postgresql

# Create database
createdb stock_sentinel
```

### Linux
```bash
sudo apt-get install postgresql postgresql-contrib

sudo -u postgres createdb stock_sentinel
```

---

## Testing the Installation

### 1. Check Backend API
```bash
curl http://localhost:8000/docs
# Should open Swagger UI with all endpoints
```

### 2. Check Frontend
```
Open browser to http://localhost:3000
# Should show Stock Sentinel login page
```

### 3. Test Authentication Flow

#### Register
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'
```

#### Login
```bash
curl -X POST "http://localhost:8000/api/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Copy the "access_token" from response
export TOKEN="<paste_token_here>"
```

#### Test API
```bash
# Get user settings
curl -X GET "http://localhost:8000/api/user/settings" \
  -H "Authorization: Bearer $TOKEN"

# Get stock quote
curl -X GET "http://localhost:8000/api/stocks/AAPL" \
  -H "Authorization: Bearer $TOKEN"

# Get market summary
curl -X GET "http://localhost:8000/api/stocks/market-summary/overview" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Test in Frontend

1. Navigate to http://localhost:3000
2. Click "Register" tab
3. Enter credentials:
   - Email: test@example.com
   - Password: testpass123
   - Full Name: Test User
4. Click "Sign Up"
5. Login with the same credentials
6. Should see dashboard with portfolio, alerts, news

---

## Common Issues & Solutions

### Issue: "Connection refused" on localhost:8000

**Solution:**
```bash
# Make sure backend is running
cd backend
python -m uvicorn app.main:app --reload

# Or check if port 8000 is in use
# Windows:
netstat -ano | findstr :8000

# Kill the process if needed
taskkill /PID <pid> /F
```

### Issue: "PostgreSQL connection failed"

**Solution:**
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT 1;"

# If not running, start it:
# Docker:
docker-compose up postgres

# Local:
# Windows:
psql -U postgres

# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql
```

### Issue: "Database migrations failed"

**Solution:**
```bash
cd backend

# Check migration status
alembic current

# Apply migrations
alembic upgrade head

# Verify tables exist
# In psql:
psql -U postgres -d stock_sentinel -c "\dt"
```

### Issue: "Module not found" error

**Solution:**
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

---

## Environment Configuration

### Backend (.env in `/backend`)
```
DATABASE_URL=postgresql://postgres:password@localhost/stock_sentinel
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here
```

### Frontend (.env.local in `/frontend`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## File Structure Quick Reference

```
stock-sentinal/
├── backend/
│   ├── app/
│   │   ├── api/routes/          [14 API modules]
│   │   ├── models/              [Database models]
│   │   └── main.py              [FastAPI app]
│   ├── alembic/
│   │   └── versions/            [Database migrations]
│   └── requirements.txt          [Python dependencies]
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/premium/      [Login/Register page]
│   │   ├── dashboard/           [Main dashboard]
│   │   └── layout.tsx           [Auth wrapper]
│   ├── components/              [React components]
│   └── package.json             [Node dependencies]
│
└── Documentation files (BACKEND_EXTENSION_COMPLETE.md, etc.)
```

---

## Quick Command Reference

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
python -m uvicorn app.main:app --reload

# Stop server
Ctrl+C
```

### Frontend
```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Stop server
Ctrl+C
```

### Database (PostgreSQL)
```bash
# Connect to database
psql -U postgres -d stock_sentinel

# List tables
\dt

# Show table structure
\d table_name

# Exit
\q
```

---

## Verify Everything Works

### Checklist
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Swagger UI shows 40+ endpoints: http://localhost:8000/docs
- [ ] Can register new user
- [ ] Can login with registered account
- [ ] Dashboard loads after login
- [ ] Can create support ticket
- [ ] Can create trade
- [ ] Can view stock details
- [ ] Can view market summary

---

## Next Steps After Setup

1. **Read Documentation**
   - BACKEND_EXTENSION_COMPLETE.md - Feature overview
   - BACKEND_API_REFERENCE.md - API cookbook with examples
   - PROJECT_COMPLETE_STATUS.md - Full project status

2. **Explore Features**
   - Create some test trades
   - Create support tickets
   - View market data and indicators
   - Update user settings

3. **Customize (Optional)**
   - Replace mock stock data with real API
   - Add email notifications
   - Implement real-time WebSocket updates
   - Add more trading strategies

4. **Deploy to Production**
   - Use Docker for consistent environment
   - Set up database backups
   - Configure monitoring and logging
   - Setup CI/CD pipeline

---

## Useful URLs

| Resource | URL |
|----------|-----|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Frontend** | http://localhost:3000 |
| **OpenAPI Schema** | http://localhost:8000/openapi.json |

---

## Support & Debugging

### Enable Debug Logging
```bash
# Set environment variable
export LOGLEVEL=DEBUG

# Then run backend
python -m uvicorn app.main:app --reload --log-level debug
```

### View Database Logs
```bash
# Connect and run query
psql -U postgres -d stock_sentinel

# View all tables
\dt

# View all migrations
SELECT * FROM alembic_version;

# Check table structure
\d users
\d trades
\d support_tickets
```

### Browser Console
Open DevTools (F12) in frontend and check:
- Network tab for API calls
- Console for JavaScript errors
- Application tab for localStorage token

---

## Troubleshooting Terminal Commands

### Reset Everything
```bash
# Backend
cd backend
rm -rf venv __pycache__ .pytest_cache
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd frontend
rm -rf node_modules .next
npm install
```

### Check Service Ports
```bash
# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# macOS/Linux
lsof -i :3000
lsof -i :8000
lsof -i :5432
```

### Kill Process on Port
```bash
# Windows
taskkill /PID <PID> /F

# macOS/Linux
kill -9 <PID>
```

---

## Performance Notes

- First build is slower (compiling TypeScript, Python dependencies)
- Subsequent runs are faster (cached)
- Use `--reload` flag in development for instant updates
- Production builds require `npm run build` and `docker-compose up`

---

## Success Indicators ✅

You know everything is working when:

1. ✅ You can navigate to http://localhost:3000
2. ✅ Registration form appears without errors
3. ✅ You can create a new account
4. ✅ Dashboard loads after login
5. ✅ You can see the trading interface
6. ✅ API calls show in browser Network tab
7. ✅ No errors in browser console
8. ✅ Backend logs show incoming requests

If any of these fail, check the **Troubleshooting** section above.

---

## Environment Variables Summary

### Backend Required
```
DATABASE_URL=postgresql://user:password@host:port/dbname
SECRET_KEY=your-secret-key-minimum-32-chars
ENVIRONMENT=development|production
DEBUG=true|false
```

### Backend Optional
```
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
```

### Frontend Required
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Document References

For more detailed information, see:

| Document | Purpose |
|----------|---------|
| BACKEND_EXTENSION_COMPLETE.md | Detailed feature implementation |
| BACKEND_API_REFERENCE.md | Complete API cookbook |
| PROJECT_COMPLETE_STATUS.md | Full project overview |
| ARCHITECTURE_DIAGRAMS.md | System architecture |
| DOCKER_QUICK_REFERENCE.ps1 | Docker commands |

---

## Ready to Start? 🚀

Choose your setup option above and follow the steps. You should be up and running in 5 minutes!

**Questions?** Check the documentation files listed above.

**Issue?** See the **Common Issues** section.

**Ready to test?** See the **Testing** section.

**Happy trading!** 📈
