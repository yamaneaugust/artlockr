# ArtLockr Deployment Guide

Complete deployment guide for ArtLockr AI-powered copyright detection system.

## Table of Contents

1. [Quick Start (Local Development)](#quick-start-local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

## Quick Start (Local Development)

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/artlockr.git
cd artlockr
```

### Step 2: Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, set DATABASE_URL and SECRET_KEY
```

### Step 3: Database Setup

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Initialize database
cd ..
python scripts/init_database.py --seed-data

# This creates:
# - PostgreSQL database
# - All tables via Alembic migrations
# - Sample seed data for testing
```

### Step 4: Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Backend will be available at http://localhost:8000
API docs at http://localhost:8000/docs

### Step 5: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:3000

### Step 6: Test the System

- Login with seed account: `artist1@example.com` / `password`
- Upload an artwork
- View detection results

## Docker Deployment

### Docker Compose (Recommended for Development)

The easiest way to run ArtLockr locally with all services:

```bash
# Create .env file
cp .env.example .env

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Services started:**
- **db**: PostgreSQL database on port 5432
- **backend**: FastAPI backend on port 8000
- **frontend**: React frontend on port 3000
- **worker**: Background scanning worker

### Individual Docker Services

Build and run services individually:

```bash
# Build backend
cd backend
docker build -t artlockr-backend .

# Run backend
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  artlockr-backend

# Build frontend
cd frontend
docker build -t artlockr-frontend \
  --build-arg VITE_API_URL=http://localhost:8000/api/v1 \
  .

# Run frontend
docker run -p 3000:80 artlockr-frontend
```

### Docker Compose Override (Production)

For production, create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    restart: always
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - /var/lib/postgresql/data:/var/lib/postgresql/data

  backend:
    restart: always
    environment:
      ENVIRONMENT: production
      DEBUG: false
      LOG_LEVEL: WARNING

  frontend:
    restart: always
```

Run with: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

## Production Deployment

### Option 1: VPS / Cloud Server (DigitalOcean, AWS EC2, etc.)

#### Step 1: Server Setup

```bash
# SSH to server
ssh user@your-server.com

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install nginx (reverse proxy)
sudo apt install nginx -y
```

#### Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/artlockr.git
cd artlockr

# Create production .env
cp .env.example .env
nano .env  # Edit with production values
```

**Critical production settings:**

```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-with-secrets.token_urlsafe-32>
DATABASE_URL=postgresql://artlockr:<strong-password>@db:5432/artlockr_db
DB_PASSWORD=<strong-password>
```

#### Step 3: Initialize Database

```bash
docker-compose up -d db
sleep 10  # Wait for database to start
python scripts/init_database.py
```

#### Step 4: Start Services

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### Step 5: Configure Nginx

```nginx
# /etc/nginx/sites-available/artlockr
server {
    listen 80;
    server_name artlockr.com www.artlockr.com;

    client_max_body_size 10M;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/artlockr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 6: SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d artlockr.com -d www.artlockr.com
```

### Option 2: Kubernetes (AWS EKS, GKE, AKS)

See `k8s/README.md` for Kubernetes deployment manifests.

### Option 3: Platform as a Service

**Heroku:**
```bash
heroku create artlockr
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set SECRET_KEY=...
git push heroku main
```

**Railway/Render:**
- Connect GitHub repository
- Set environment variables
- Deploy automatically on push

## CI/CD Pipeline

### GitHub Actions

The repository includes a complete CI/CD pipeline (`.github/workflows/ci-cd.yml`):

**Workflow:**
1. **Test** (on all pushes):
   - Backend tests with pytest
   - Frontend linting and type checking
   - Security scanning with Trivy

2. **Build & Push** (on main/develop):
   - Build Docker images
   - Push to GitHub Container Registry (ghcr.io)
   - Tag with branch name and SHA

3. **Deploy**:
   - **Develop → Staging**: Auto-deploy to staging environment
   - **Main → Production**: Auto-deploy to production environment

### Required GitHub Secrets

Set these in your GitHub repository settings:

```bash
# GitHub Container Registry (automatically available)
GITHUB_TOKEN

# Production server (if using SSH deployment)
PRODUCTION_SSH_KEY
PRODUCTION_HOST
PRODUCTION_USER

# Staging server
STAGING_SSH_KEY
STAGING_HOST
STAGING_USER

# Database credentials
DB_PASSWORD
SECRET_KEY
```

### Deployment Environments

Configure GitHub Environments for approval workflows:

1. Go to **Settings → Environments**
2. Create environments: `staging`, `production`
3. Enable **Required reviewers** for production
4. Set **Environment secrets**

### Manual Deployment

Trigger manual deployment:

```bash
# Via GitHub Actions UI
# Go to Actions → CI/CD → Run workflow

# Or via gh CLI
gh workflow run ci-cd.yml -f environment=production
```

## Environment Configuration

### Required Environment Variables

```bash
# Security (CRITICAL - Change in production!)
SECRET_KEY=<generate-strong-key>
DB_PASSWORD=<strong-database-password>

# Database
DATABASE_URL=postgresql://artlockr:password@host:5432/artlockr_db

# Environment
ENVIRONMENT=production  # development, staging, production
DEBUG=false  # MUST be false in production
```

### Optional but Recommended

```bash
# Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=app-password

# Error tracking
SENTRY_DSN=https://...@sentry.io/...

# S3 backups
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=artlockr-backups
```

### Secrets Management

**For Production:**

- **AWS Secrets Manager**: `aws secretsmanager get-secret-value --secret-id artlockr-secrets`
- **HashiCorp Vault**: `vault kv get secret/artlockr`
- **Docker Secrets**: Use Docker Swarm secrets
- **Kubernetes Secrets**: Use sealed secrets or external secrets operator

## Monitoring & Maintenance

### Health Checks

All services include health check endpoints:

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000/health

# Database (via Docker)
docker exec artlockr-db pg_isready -U artlockr
```

### Logging

**View logs:**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

**Log files:**
- Backend: `backend/logs/artlockr.log`
- Nginx: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`

### Backups

**Automated backups via cron:**

```bash
# Edit crontab
crontab -e

# Add daily backup at 2am
0 2 * * * cd /home/user/artlockr && ./scripts/backup_database.sh
```

**Manual backup:**

```bash
./scripts/backup_database.sh my_backup_name
```

**Restore from backup:**

```bash
./scripts/restore_database.sh backup_20241216_120000
```

### Updates

**Update to latest version:**

```bash
# Pull latest code
git pull origin main

# Rebuild and restart services
docker-compose build
docker-compose up -d

# Run new migrations
docker-compose exec backend alembic upgrade head
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check logs
docker-compose logs db

# Test connection
docker exec artlockr-db psql -U artlockr -d artlockr_db -c "SELECT 1"
```

### Backend Crashes

```bash
# View logs
docker-compose logs --tail=50 backend

# Check for migration issues
docker-compose exec backend alembic current

# Restart service
docker-compose restart backend
```

### Frontend Not Loading

```bash
# Check if backend is accessible
curl http://localhost:8000/api/v1/health

# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Limit memory in docker-compose.yml
services:
  backend:
    mem_limit: 2g
    mem_reservation: 1g
```

### Disk Space Issues

```bash
# Clean Docker images
docker system prune -a

# Clean old backups (keeps last 10)
cd data/backups
ls -t backup_*.dump | tail -n +11 | xargs rm -f
```

## Performance Optimization

### Database

```sql
-- Add indexes (already in migration 002)
-- Vacuum database regularly
VACUUM ANALYZE;

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Backend

```python
# Use connection pooling (already configured)
# Enable Redis caching for frequent queries
# Use FAISS for vector search (already implemented)
```

### Frontend

```bash
# Build optimized production bundle
cd frontend
npm run build

# Serves minified, compressed assets
```

## Security Checklist

- [ ] Change `SECRET_KEY` from default
- [ ] Use strong database passwords
- [ ] Enable SSL/TLS (Let's Encrypt)
- [ ] Set `DEBUG=false` in production
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up firewall (UFW)
- [ ] Regular security updates
- [ ] Enable automated backups
- [ ] Monitor logs for suspicious activity

## Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Review health checks: `/health` endpoints
3. Verify environment variables
4. Check disk space: `df -h`
5. Review documentation: DATABASE.md, PRIVACY.md, etc.

---

**Need Help?** Open an issue at https://github.com/yourusername/artlockr/issues
