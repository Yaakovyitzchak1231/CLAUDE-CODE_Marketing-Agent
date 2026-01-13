# B2B Marketing Automation Platform - Setup Guide

Complete guide to set up and deploy the B2B Marketing Automation Platform.

## Prerequisites

### Required Software

- **Docker**: 20.10+ ([Download](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ (included with Docker Desktop)
- **Git**: For version control
- **16GB+ RAM**: Recommended for running all services
- **50GB+ Storage**: For Docker images, models, and data

### Optional

- **NVIDIA GPU**: For faster LLM inference (with CUDA drivers)
- **Domain name**: For production deployment
- **SSL Certificate**: For HTTPS (Let's Encrypt recommended)

## Quick Start (5 minutes)

### 1. Clone Repository

```bash
git clone <repository-url>
cd Marketing\ System
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# At minimum, set secure passwords:
nano .env  # or use your preferred editor
```

**Required settings:**
```bash
# Database
POSTGRES_PASSWORD=<your-secure-password>

# Redis
REDIS_PASSWORD=<your-secure-password>

# n8n
N8N_PASSWORD=<your-secure-password>
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Wait for initialization (2-3 minutes)
# Check status
docker-compose ps
```

### 4. Test Connectivity

**Linux/Mac:**
```bash
chmod +x test-services.sh
./test-services.sh
```

**Windows:**
```powershell
.\test-services.ps1
```

### 5. Access Services

- **Dashboard**: http://localhost/dashboard
- **n8n**: http://localhost/n8n (login with N8N_USER/N8N_PASSWORD)
- **Analytics**: http://localhost/analytics
- **Database**: http://localhost/adminer

## Detailed Setup

### Step 1: Environment Configuration

Edit `.env` file and configure:

#### API Keys (for media generation)

```bash
# Image Generation (required for Image Agent)
OPENAI_API_KEY=sk-your_key_here          # For DALL-E 3
# OR
MIDJOURNEY_API_KEY=your_key_here         # Alternative

# Video Generation (required for Video Agent)
RUNWAY_API_KEY=your_key_here             # For Runway ML
# OR
PIKA_API_KEY=your_key_here               # Alternative
```

#### Publishing APIs (optional)

```bash
# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_token

# WordPress
WORDPRESS_URL=https://yourblog.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=your_app_password

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

#### Security Keys

```bash
# Generate secure keys
openssl rand -base64 32  # For passwords
openssl rand -hex 32     # For secret keys

# Update in .env
SEARXNG_SECRET=<generated-key>
```

### Step 2: Start Infrastructure

```bash
# Pull images (first time only)
docker-compose pull

# Start all services
docker-compose up -d

# Follow logs (optional)
docker-compose logs -f
```

**Services startup order:**
1. PostgreSQL, Redis (immediate)
2. n8n, Chroma, Ollama (30-60 seconds)
3. Other services (60-90 seconds)

### Step 3: Initialize Databases

#### PostgreSQL

```bash
# Database schema is auto-created via init-scripts/init.sql
# Verify
docker exec postgres psql -U marketing_user -d marketing -c "\dt"
```

#### Chroma Vector DB

```bash
# Run initialization script
docker exec -it langchain_service python /app/chroma-init/init_collections.py
```

Expected output:
```
✓ Created collection: user_profiles
✓ Created collection: content_library
✓ Created collection: market_segments
✓ Created collection: competitor_content
```

### Step 4: Pull LLM Models

**Linux/Mac:**
```bash
chmod +x ollama/pull-models.sh
./ollama/pull-models.sh
```

**Windows:**
```powershell
.\ollama\pull-models.ps1
```

This will download:
- Llama 3 8B (4.7GB) - primary model
- Mistral 7B (4.1GB) - alternative

**⏱ Estimated time**: 10-20 minutes depending on internet speed

### Step 5: Configure Matomo Analytics

1. Open http://localhost/analytics
2. Follow installation wizard:
   - Database: PostgreSQL
   - Host: `postgres`
   - Database: `matomo`
   - User: Value from `POSTGRES_USER` in .env
   - Password: Value from `POSTGRES_PASSWORD` in .env
3. Create admin account
4. Add website to track
5. Save authentication token to `.env`:
   ```bash
   MATOMO_AUTH_TOKEN=<your-token>
   ```

### Step 6: Set Up n8n

1. Open http://localhost/n8n
2. Login with credentials from `.env`:
   - User: `N8N_USER`
   - Password: `N8N_PASSWORD`
3. (Optional) Import starter workflows from `n8n-workflows/`

### Step 7: Run Tests

```bash
# Test all services
./test-services.sh  # Linux/Mac
.\test-services.ps1  # Windows
```

Expected result:
```
✓ All services are operational!
```

## Verification Checklist

- [ ] All Docker containers running
- [ ] PostgreSQL database created with tables
- [ ] Chroma vector collections initialized
- [ ] At least one Ollama model pulled
- [ ] Dashboard accessible at http://localhost/dashboard
- [ ] n8n accessible and logged in
- [ ] Matomo configured with tracking token
- [ ] All health checks passing

## Common Issues

### Services Not Starting

**Issue**: Container exits immediately

**Solution**:
```bash
# Check logs
docker-compose logs [service-name]

# Common fixes:
# 1. Port already in use
docker ps  # Check for conflicts
# 2. Insufficient memory
docker system df  # Check Docker disk usage
docker system prune  # Clean up if needed
# 3. Missing .env file
cp .env.example .env
```

### Database Connection Errors

**Issue**: `Could not connect to postgres`

**Solution**:
```bash
# Wait for PostgreSQL to fully start
docker-compose logs postgres

# Verify it's ready
docker exec postgres pg_isready -U marketing_user

# Restart dependent services
docker-compose restart langchain_service streamlit_dashboard
```

### Ollama Model Not Found

**Issue**: `model 'llama3:8b' not found`

**Solution**:
```bash
# Pull models manually
docker exec ollama ollama pull llama3:8b
docker exec ollama ollama pull mistral:7b

# Verify
docker exec ollama ollama list
```

### Nginx 502 Bad Gateway

**Issue**: Nginx can't reach upstream service

**Solution**:
```bash
# Check upstream service is running
docker-compose ps

# Check network connectivity
docker exec nginx ping [service-name]

# Restart Nginx
docker-compose restart nginx
```

### Out of Memory

**Issue**: System runs out of RAM

**Solution**:
```bash
# Stop non-essential services temporarily
docker-compose stop matomo adminer

# Use smaller Ollama model
docker exec ollama ollama pull phi:2  # Only 1.7GB

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 8GB+
```

## Production Deployment

### 1. Security Hardening

```bash
# Use strong passwords (all services)
openssl rand -base64 32

# Enable firewall
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Disable root SSH (if using cloud server)
# Edit /etc/ssh/sshd_config:
# PermitRootLogin no
```

### 2. SSL/HTTPS Setup

```bash
# Install certbot
apt-get install certbot

# Generate certificate
certbot certonly --standalone -d your-domain.com

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# Uncomment HTTPS server block in nginx/nginx.conf
# Restart Nginx
docker-compose restart nginx
```

### 3. Backups

```bash
# Database backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec postgres pg_dump -U marketing_user marketing > backup_${DATE}.sql
docker exec postgres pg_dump -U marketing_user matomo > backup_matomo_${DATE}.sql
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### 4. Monitoring

```bash
# Install monitoring stack (optional)
docker run -d --name prometheus -p 9090:9090 prom/prometheus
docker run -d --name grafana -p 3000:3000 grafana/grafana

# Set up alerts for:
# - Service downtime
# - High memory usage
# - Disk space
# - Failed requests
```

### 5. Environment Variables

For production, use secrets management:

```bash
# Docker secrets (Swarm mode)
echo "my_secret_password" | docker secret create postgres_password -

# Or use .env with restricted permissions
chmod 600 .env
chown root:root .env
```

## Scaling

### Vertical Scaling (More Resources)

```yaml
# docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 16G
```

### Horizontal Scaling (More Instances)

```yaml
# Add more LangChain workers
services:
  langchain_service:
    deploy:
      replicas: 3

  nginx:
    # Update upstream in nginx.conf
    # upstream langchain {
    #   server langchain_service_1:8001;
    #   server langchain_service_2:8001;
    #   server langchain_service_3:8001;
    # }
```

## Next Steps

After successful setup:

1. **Create LangChain Agents** (Phase 2)
   - [ ] Implement agent base class
   - [ ] Build Supervisor Agent
   - [ ] Build specialist agents (Research, Content, etc.)

2. **Build n8n Workflows** (Phase 4)
   - [ ] User onboarding workflow
   - [ ] Content generation pipeline
   - [ ] Publishing automation

3. **Develop Streamlit Dashboard** (Phase 5)
   - [ ] Content review interface
   - [ ] Analytics dashboard
   - [ ] Campaign management

## Support

### Documentation

- [Docker Compose](docker-compose.yml)
- [Environment Variables](.env.example)
- [Database Schema](init-scripts/init.sql)
- [Implementation Plan](.claude/plans/swirling-prancing-rose.md)

### Service-Specific Docs

- [Ollama](ollama/README.md)
- [SearXNG](searxng/README.md)
- [Redis](redis/README.md)
- [Matomo](matomo/README.md)
- [Nginx](nginx/README.md)

### Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs [service-name]

# Follow logs in real-time
docker-compose logs -f [service-name]

# Last 100 lines
docker-compose logs --tail=100 [service-name]
```

### Container Shell Access

```bash
# Execute commands in container
docker exec -it [container-name] bash

# Examples:
docker exec -it postgres psql -U marketing_user
docker exec -it redis redis-cli
docker exec -it ollama ollama list
```

## Maintenance

### Regular Tasks

**Daily:**
- Check service health: `./test-services.sh`
- Monitor logs for errors
- Review Matomo analytics

**Weekly:**
- Database vacuum: `docker exec postgres vacuumdb -U marketing_user -d marketing -z`
- Clear old Redis keys
- Archive Matomo old data

**Monthly:**
- Update Docker images: `docker-compose pull && docker-compose up -d`
- Backup databases
- Review disk usage: `docker system df`
- Update Ollama models: `docker exec ollama ollama pull llama3:8b`

### Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Clean Docker system
docker system prune -a --volumes
```

## Resources

- **Official Docs**:
  - [n8n](https://docs.n8n.io/)
  - [LangChain](https://python.langchain.com/)
  - [Ollama](https://github.com/ollama/ollama)
  - [SearXNG](https://docs.searxng.org/)

- **Community**:
  - [LangChain Discord](https://discord.gg/langchain)
  - [n8n Forum](https://community.n8n.io/)

- **AI Models**:
  - [Llama 3](https://ai.meta.com/llama/)
  - [Mistral](https://docs.mistral.ai/)
