# Docker Architecture Diagram for Stock Sentinel

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        YOUR COMPUTER                                │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Docker Environment                        │  │
│  │                                                              │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │        stocksentinel-network (Docker Network)        │   │  │
│  │  │                                                      │   │  │
│  │  │  ┌──────────────────┐   ┌──────────────────────┐   │   │  │
│  │  │  │  PostgreSQL      │   │   FastAPI Backend    │   │   │  │
│  │  │  │  Container       │   │   Container          │   │   │  │
│  │  │  │                  │   │                      │   │   │  │
│  │  │  │  Service: db     │◄──┤   service: backend   │   │   │  │
│  │  │  │  Port: 5432      │   │   Port: 8000         │   │   │  │
│  │  │  │  User: stock...  │   │                      │   │   │  │
│  │  │  │  Pass: password  │   │   DATABASE_URL:      │   │   │  │
│  │  │  │                  │   │   postgresql+...@db  │───┼───┼─►│  │
│  │  │  └──────────────────┘   └──────────────────────┘   │   │  │
│  │  │            ▲                                         │   │  │
│  │  │            │            ┌──────────────────────┐    │   │  │
│  │  │            │            │   Frontend (Next.js) │    │   │  │
│  │  │            │            │   Container          │    │   │  │
│  │  │            │            │   Port: 3000         │    │   │  │
│  │  │            │            └──────────────────────┘    │   │  │
│  │  │                                                      │   │  │
│  │  └──────────────────────────────────────────────────────┘   │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  External Ports Exposed:                                           │
│  - 5432 ◄─── PostgreSQL Port                                      │
│  - 8000 ◄─── FastAPI Port (http://localhost:8000)               │
│  - 3000 ◄─── Frontend Port (http://localhost:3000)              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
┌──────────────────┐
│  Your Browser    │
│  localhost:8000  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│  FastAPI Backend             │
│  docker-compose service:     │
│  'backend'                   │
│                              │
│  DATABASE_URL:               │
│  postgresql+...@db:5432      │
└────────┬─────────────────────┘
         │
         │ Uses hostname 'db'
         │ (Docker service name)
         │
         ▼
┌──────────────────────────────┐
│  PostgreSQL Database         │
│  docker-compose service:     │
│  'db'                        │
│                              │
│  Connection Info:            │
│  - Host: db (internal)       │
│  - Port: 5432               │
│  - User: stocksentinel       │
│  - Password: password        │
│  - Database: stocksentinel   │
└──────────────────────────────┘
         ▲
         │
         ▼
   ┌──────────────────────┐
   │  postgres_data       │
   │  Volume (Disk)       │
   │                      │
   │ Data persists here   │
   │ even if container    │
   │ stops                │
   └──────────────────────┘
```

---

## docker-compose.yml Service Definitions

```
┌─ docker-compose.yml ─────────────────────────────────────────┐
│                                                              │
│  services:                                                   │
│    db:                        (PostgreSQL)                   │
│      image: postgres:15-alpine                               │
│      ports: 5432:5432                                        │
│      environment:                                            │
│        POSTGRES_USER: stocksentinel                          │
│        POSTGRES_PASSWORD: password                           │
│        POSTGRES_DB: stocksentinel                            │
│      volumes:                                                │
│        - postgres_data:/var/lib/postgresql/data              │
│      networks:                                               │
│        - stocksentinel-network                               │
│                                                              │
│    backend:                   (FastAPI)                      │
│      build: ./backend                                        │
│      ports: 8000:8000                                        │
│      environment:                                            │
│        DATABASE_URL: postgresql+...@db:5432                  │
│      depends_on:                                             │
│        db: { condition: service_healthy }                    │
│      networks:                                               │
│        - stocksentinel-network                               │
│                                                              │
│    frontend:                  (Next.js)                      │
│      build: ./frontend                                       │
│      ports: 3000:3000                                        │
│      depends_on: [backend]                                   │
│      networks:                                               │
│        - stocksentinel-network                               │
│                                                              │
│  networks:                                                   │
│    stocksentinel-network:                                    │
│      driver: bridge                                          │
│                                                              │
│  volumes:                                                    │
│    postgres_data:                                            │
│      driver: local                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Startup Sequence

```
Command: docker-compose up -d db

            ▼
    ┌───────────────┐
    │  Start Docker │
    │  compose      │
    └───────┬───────┘
            │
            ▼
    ┌─────────────────────────┐
    │  Parse                  │
    │  docker-compose.yml     │
    └───────┬─────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │  Create Network:        │
    │  stocksentinel-network  │
    └───────┬─────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │  Create Volume:         │
    │  postgres_data          │
    └───────┬─────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │  Pull Image:            │
    │  postgres:15-alpine     │
    └───────┬─────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │  Create Container       │
    │  stocksentinel-db       │
    └───────┬─────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │  Start PostgreSQL       │
    │  (initializes database) │
    └───────┬─────────────────┘
            │
            ▼
    ┌─────────────────────────┐
    │  Health Check Pass?     │
    │  (pg_isready)           │
    └───────┬─────────────────┘
            │
            ▼
        ✅ READY!
        Container is running
        Port 5432 accessible
        Database initialized
        Data volume mounted
```

---

## Comparison: Before vs After

### BEFORE (Local PostgreSQL)
```
Your Computer CPU:
┌──────────────────────────────────────┐
│  PostgreSQL (installed locally)       │  ← Takes disk space
│  - Database files on C://Program...   │  ← Hard to reset
│  - Manual startup required            │  ← Easy to forget
│  - Port conflicts possible            │  ← Can't uninstall easily
│  - System-wide impact                 │  ← Affects other projects
└──────────────────────────────────────┘
```

### AFTER (Docker PostgreSQL)
```
Docker Container:
┌──────────────────────────────────────┐
│  PostgreSQL (in container)            │  ✓ Isolated
│  - Clean: nothing installed locally   │  ✓ Easy to reset
│  - One command to start               │  ✓ Reproducible
│  - No port conflicts                  │  ✓ Can use different port
│  - Project-specific                   │  ✓ Won't affect other projects
│  - Data in volume (persistent)        │  ✓ Data survives restarts
└──────────────────────────────────────┘
```

---

## Health Check Flow

```
┌─────────────────────────────┐
│  PostgreSQL starts          │
│  (initialization phase)     │
└────────┬────────────────────┘
         │
    Every 10 seconds:
         │
         ▼
    ┌─────────────────────────────────────┐
    │  Run health check:                  │
    │  pg_isready -U stocksentinel        │
    │                    -d stocksentinel │
    └──────────────┬──────────────────────┘
                   │
        Returns: yes?
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    ✅ READY              ⏳ RETRYING
    (healthy)            (retry count++)
        │                     │
        │                     │ Max 5 retries?
        │                     │
        │                ┌────┴────┐
        │                │          │
        │                ▼          ▼
        │              ✅ READY  ❌ FAILED
        │                         (container exits)
        │
        ▼
    Backend can now
    connect to database!
```

---

## Volume Organization

```
Your Computer File System:
┌─────────────────────────────────────────────┐
│  docker/                                    │
│    └─ storage/                              │
│       └─ postgres_data/               ◄─────┼──── Named Volume
│          ├─ postgresql.conf                 │
│          ├─ pg_hba.conf                     │
│          ├─ base/                           │
│          │  ├─ 1/                           │
│          │  │  └─ [system tables]           │
│          │  └─ 16541/                       │
│          │     └─ [your database]           │
│          └─ pg_Version                      │
│                                             │
│  (This persists even if container stops)    │
└─────────────────────────────────────────────┘
```

---

## Network Communication

```
Inside Docker Network: stocksentinel-network

Container 1: db (PostgreSQL)
 │
 │ ◀─────────► Container 2: backend (FastAPI)
 │              Can use hostname 'db' to connect
 │
 ◀─────────► Container 3: frontend (Next.js)
              Can reach backend via 'backend' hostname

Outside Docker:
 │
 ├──── localhost:5432   ◀─► PostgreSQL
 ├──── localhost:8000   ◀─► FastAPI
 └──── localhost:3000   ◀─► Frontend

Benefits:
✓ Containers can talk to each other by service name
✓ Your computer sees them on localhost
✓ No need for IP addresses
✓ Automatic DNS resolution
```

---

## Key Concepts

| Concept | What It Is | Why It Matters |
|---------|-----------|---|
| **Volume** | Persistent storage (postgres_data) | Data survives container restart |
| **Network** | Docker bridge network | Services communicate by name |
| **Environment Variables** | POSTGRES_USER, POSTGRES_PASSWORD, etc. | Initializes database on first run |
| **Health Check** | pg_isready command | Ensures DB is ready before backend starts |
| **Depends_on** | Backend waits for healthy db | Prevents connection errors |
| **Port Mapping** | 5432:5432 | Maps container port to your computer |

---

## File Structure

```
c:\Users\acer\Downloads\stock sentinal\
├── docker-compose.yml              ◄─── Updated ✅
│
├── backend\
│   ├── .env
│   │   └── DATABASE_URL=postgresql+psycopg2://...@localhost:5432/...
│   ├── app\
│   │   ├── main.py
│   │   ├── config.py
│   │   └── db\
│   │       └── session.py
│   └── Dockerfile
│
├── frontend\
│   └── Dockerfile
│
└── [Documentation]
    ├── DOCKER_SETUP_SUMMARY.md
    ├── DOCKER_POSTGRES_GUIDE.md     ◄─── Created ✅
    ├── DOCKER_QUICK_REFERENCE.ps1   ◄─── Created ✅
    └── DOCKER_STANDALONE_COMMANDS.ps1
```

