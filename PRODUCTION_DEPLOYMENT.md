# Production Deployment Guide - Stock Sentinel

## Pre-Deployment Checklist

### ✅ Configuration

- [ ] `.env` file in root with all required variables
- [ ] Backend Twilio credentials configured (if WhatsApp enabled)
- [ ] Frontend environment variables set
- [ ] Database credentials strong and unique
- [ ] CORS origins configured for production domain
- [ ] Email SMTP credentials verified

### ✅ Security

- [ ] All secrets stored in `.env`, NOT in code
- [ ] `.env` added to `.gitignore` (committed to .gitignore)
- [ ] JWT secret is strong (random 32+ characters)
- [ ] Database password meets complexity requirements
- [ ] SSL/TLS enabled for production
- [ ] API rate limiting configured

### ✅ Database

- [ ] All migrations applied successfully
- [ ] Database backed up before deployment
- [ ] Migration scripts tested locally
- [ ] PostgreSQL version compatible (12+)
- [ ] Backup retention policy established

### ✅ Testing

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] API endpoints tested
- [ ] WebSocket connectivity verified
- [ ] Email alerts tested
- [ ] WhatsApp alerts tested (if enabled)
- [ ] Mobile responsiveness verified
- [ ] Load testing completed

### ✅ Monitoring

- [ ] Application logs configured
- [ ] Error tracking (e.g., Sentry) set up
- [ ] Performance monitoring enabled
- [ ] Alerting configured
- [ ] Database monitoring set up
- [ ] Uptime monitoring configured

---

## Environment Variables Reference

### Backend `.env`

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@host:5432/stocksentinel
SQLALCHEMY_ECHO=False

# Security
JWT_SECRET=your-strong-random-secret-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
REFRESH_TOKEN_EXPIRATION_DAYS=7

# API Configuration
API_TITLE=Stock Sentinel API
API_VERSION=1.0.0
ENVIRONMENT=production

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_NAME=Stock Sentinel
SENDER_EMAIL=alerts@yourcompany.com

# Twilio WhatsApp Configuration
ENABLE_WHATSAPP_NOTIFICATIONS=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token-here
TWILIO_WHATSAPP_NUMBER=+1234567890

# CORS Configuration
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Feature Flags
ENABLE_PORTFOLIO_SYNC=true
ENABLE_TRADING_ALERTS=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_ALERTS_SCHEDULER=true

# Logging
LOG_LEVEL=INFO

# Optional: Sentry Error Tracking
SENTRY_DSN=your-sentry-dsn-if-used
```

### Frontend `.env.local`

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com

# Feature Flags
NEXT_PUBLIC_ENABLE_DEMO_MODE=false

# Analytics (Optional)
NEXT_PUBLIC_GA_ID=your-google-analytics-id
```

---

## Production Deployment Steps

### Step 1: Prepare Infrastructure

#### Option A: AWS (Recommended)
- Create RDS PostgreSQL instance (Multi-AZ for HA)
- Create ECS Fargate cluster
- Set up ALB for load balancing
- Create CloudWatch log groups
- Set up RDS backups (automated daily)

#### Option B: DigitalOcean/Linode
- Create PostgreSQL managed database
- Create Docker droplet/node
- Configure firewall rules
- Set up automated backups

#### Option C: Self-Hosted
- Ensure PostgreSQL 12+ server available
- Set up SSL certificates (Let's Encrypt)
- Configure firewall for ports 443 (HTTPS), 5432 (DB if needed)
- Set up automated backups

### Step 2: Prepare Docker Images

```bash
# Pull latest code
git pull origin main

# Build production images with cache busting
docker compose build --no-cache

# Tag images for registry
docker tag stocksentinel-backend myregistry.com/stocksentinel-backend:v1.0.0
docker tag stocksentinel-frontend myregistry.com/stocksentinel-frontend:v1.0.0

# Push to registry
docker push myregistry.com/stocksentinel-backend:v1.0.0
docker push myregistry.com/stocksentinel-frontend:v1.0.0
```

### Step 3: Database Preparation

```bash
# Create production database
createdb -U postgres stocksentinel_prod

# Set strong password
psql -U postgres -c "ALTER USER stocksentinel WITH PASSWORD 'strong-random-password-here';"

# Backup before migration
pg_dump -U postgres stocksentinel_prod > backup_pre_migration.sql

# Run migrations (Alembic will auto-run in Docker)
# This happens automatically when container starts with:
# CMD ["sh", "-c", "alembic upgrade head && uvicorn ..."]
```

### Step 4: Deploy Containers

#### AWS ECS Example

```bash
# Create task definition for backend
aws ecs register-task-definition \
  --family stocksentinel-backend \
  --container-definitions '[{
    "name": "backend",
    "image": "myregistry.com/stocksentinel-backend:v1.0.0",
    "portMappings": [{"containerPort": 8000}],
    "environment": [
      {"name": "DATABASE_URL", "value": "postgresql://..."},
      {"name": "ENVIRONMENT", "value": "production"}
    ],
    "secrets": [
      {"name": "JWT_SECRET", "valueFrom": "arn:aws:secretsmanager:..."}
    ]
  }]'

# Create service
aws ecs create-service \
  --cluster stocksentinel \
  --service-name backend \
  --task-definition stocksentinel-backend \
  --desired-count 2 \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...
```

#### Docker Swarm Example

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml stocksentinel
```

#### Kubernetes Example

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stocksentinel-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stocksentinel
  template:
    metadata:
      labels:
        app: stocksentinel
    spec:
      containers:
      - name: backend
        image: myregistry.com/stocksentinel-backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: stocksentinel-secrets
              key: database-url
```

### Step 5: Post-Deployment Verification

```bash
# Verify migrations applied
docker exec stocksentinel-backend alembic current
# Output should show: 0005_add_whatsapp_phone (head)

# Test health endpoint
curl https://api.yourdomain.com/health

# Check logs for errors
docker logs stocksentinel-backend --tail 100

# Test API endpoints
curl https://api.yourdomain.com/api/v1/auth/health

# Test frontend
curl https://yourdomain.com
```

---

## Scaling Configuration

### Backend Scaling

```yaml
# docker-compose.yml for multiple backend instances
services:
  backend:
    build: ./backend
    deploy:
      replicas: 3  # 3 instances
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://...
```

### Load Balancing

**NGINX Configuration:**
```nginx
upstream backend {
    server backend:8000;
    server backend:8001;
    server backend:8002;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Database Connection Pooling

```python
# app/config.py - Update for production
DATABASE_URL = os.getenv("DATABASE_URL")

# Add connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,        # Increase for production
    max_overflow=20,     # Additional connections if needed
    pool_recycle=3600,   # Recycle connections every hour
    pool_pre_ping=True   # Check connections before using
)
```

---

## Monitoring & Health Checks

### Application Health Endpoint

```bash
# Backend health check
curl https://api.yourdomain.com/health
# Response: {"status": "healthy", "database": "connected", ...}
```

### Database Health

```bash
# Check connection pool
SELECT count(*) FROM pg_stat_activity WHERE datname='stocksentinel_prod';

# Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables ORDER BY pg_total_relation_size DESC;

# Monitor slow queries (add logging)
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

### Logging Setup

**Structured Logging (JSON):**
```python
# app/main.py
import logging
import json_logging

json_logging.init_flask(app)
logger = logging.getLogger(__name__)

# Docker will collect these structured logs
logger.info("User registered", extra={"user_id": 123, "email": "user@example.com"})
```

### Alerting Rules

**Key Metrics to Alert On:**
- Backend 500+ errors: Alert if > 5/minute
- API response time: Alert if > 2s avg
- Database connection pool: Alert if > 80% used
- WebSocket disconnects: Alert if > 10/minute
- WhatsApp send failures: Alert if > 50/day
- Disk usage: Alert if > 80%
- Memory usage: Alert if > 85%

---

## Backup & Disaster Recovery

### Daily Automated Backup

```bash
#!/bin/bash
# backup.sh - Run via cron daily at 1 AM
BACKUP_DIR="/backups/stocksentinel"
DATE=$(date +%Y%m%d)

# PostgreSQL backup
pg_dump -U postgres stocksentinel_prod | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Docker volume backup (optional)
docker run --rm -v stocksentinel_data:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/volumes_$DATE.tar.gz -C /data .

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR s3://my-backups/stocksentinel/ --recursive
```

### Restore from Backup

```bash
# Restore PostgreSQL
gunzip < /backups/stocksentinel/db_20260410.sql.gz | psql -U postgres stocksentinel_prod

# Verify restore
psql -U postgres -d stocksentinel_prod -c "SELECT COUNT(*) FROM users;"
```

---

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renew (runs daily)
sudo certbot renew --quiet

# Verify
certbot certificates
```

### HTTPS Redirect

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

---

## Performance Optimization

### Frontend Optimization
- [ ] Enable gzip compression in NGINX
- [ ] Cache static assets (1 year)
- [ ] Minify CSS/JS (Next.js does automatically)
- [ ] Lazy load images
- [ ] CDN for static assets (Cloudflare, CloudFront)

### Backend Optimization
- [ ] Database connection pooling (10+ connections)
- [ ] Redis for caching (optional but recommended)
- [ ] Database query optimization and indexing
- [ ] Async operations for long-running tasks
- [ ] API response caching headers

### Database Optimization
- [ ] Index frequently queried columns
- [ ] Partition large tables
- [ ] Vacuum and analyze regularly
- [ ] Monitor and optimize slow queries

```python
# Add indexes for performance
# In migration file:
op.create_index('ix_alerts_symbol', 'alerts', ['symbol'])
op.create_index('ix_alerts_user_id', 'alerts', ['user_id'])
op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])
```

---

## Rollback Procedures

### If Deployment Fails

```bash
# Revert to previous version
docker service update --image myregistry.com/stocksentinel-backend:v1.0.0-rollback backend

# Or restart previous container
docker compose up -d stocksentinel-backend
```

### If Database Migration Fails

```bash
# Check what went wrong
docker exec stocksentinel-backend alembic current

# Downgrade to previous version
docker exec stocksentinel-backend alembic downgrade -1

# Fix migration and try again
# Then rebuild and redeploy
```

---

## Production Runbook

### Daily Tasks
- [ ] Monitor application logs
- [ ] Check database health
- [ ] Verify all containers running
- [ ] Test critical user workflows

### Weekly Tasks
- [ ] Check backups completed successfully
- [ ] Review and analyze metrics
- [ ] Update security patches if available
- [ ] Test disaster recovery procedure

### Monthly Tasks
- [ ] Review and optimize database
- [ ] Analyze costs and usage
- [ ] Update dependencies
- [ ] Full backup verification and test restore

### Quarterly Tasks
- [ ] Security audit
- [ ] Capacity planning
- [ ] Performance review
- [ ] Update documentation

---

## Support Resources

- 📚 [Migrations Guide](./MIGRATIONS_GUIDE.md)
- 🔧 [Troubleshooting Guide](./TROUBLESHOOTING.md)
- 📖 [API Documentation](./BACKEND_API_REFERENCE.md)
- 🐳 [Docker Setup](./DOCKER_SETUP_SUMMARY.md)

---

**Last Updated:** 2026-04-10  
**Version:** 1.0  
**Status:** Production Ready
