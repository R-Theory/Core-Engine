# Production Deployment Guide

This guide covers deploying the Core Engine MVP to production using Docker Compose with security best practices.

## Prerequisites

- Docker and Docker Compose installed
- Domain name with SSL certificates
- Production environment variables configured

## Security Checklist

### 1. Environment Variables

Copy the production environment template:
```bash
cp .env.prod.example .env.prod
```

**CRITICAL:** Update these values before deployment:

```bash
# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
NEXTAUTH_SECRET=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)

# Update .env.prod with generated values
sed -i "s/MUST_GENERATE_WITH_openssl_rand_hex_32/$SECRET_KEY/" .env.prod
sed -i "s/MUST_GENERATE_WITH_openssl_rand_base64_32/$NEXTAUTH_SECRET/" .env.prod
sed -i "s/YOUR_PRODUCTION_DB_PASSWORD/$POSTGRES_PASSWORD/" .env.prod
```

### 2. Domain Configuration

Update these values in `.env.prod`:
- `NEXT_PUBLIC_API_URL=https://your-domain.com`
- `NEXTAUTH_URL=https://your-domain.com`
- `ALLOWED_HOSTS=["https://your-domain.com"]`

### 3. SSL Certificates

Place your SSL certificates in:
```
nginx/ssl/
├── cert.pem
└── key.pem
```

## Deployment Steps

### 1. Build Production Images

```bash
# Build all production images
docker-compose -f docker-compose.prod.yml build

# Or build specific services
docker-compose -f docker-compose.prod.yml build backend frontend
```

### 2. Deploy Services

```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Check service health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

### 3. Initialize Database

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Verify database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connection successful')
asyncio.run(test())
"
```

### 4. Health Checks

Test all services:

```bash
# Backend health
curl -f http://localhost:8000/health

# Frontend health (after setting up nginx)
curl -f https://your-domain.com/health

# Database health
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U postgres

# Redis health
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

## Monitoring

### Resource Usage

Monitor container resources:
```bash
# View resource usage
docker stats

# Check specific service logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs postgres
```

### Performance Tuning

The production configuration includes:

**Backend:**
- 4 Uvicorn workers
- Memory limit: 1GB
- CPU limit: 1.0 cores

**Database:**
- Connection pool: 10 connections
- Memory limit: 1GB
- Automated backups enabled

**Redis:**
- Memory limit: 512MB
- LRU eviction policy
- AOF persistence enabled

### Backup Strategy

Database backups are automatically configured:

```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres core_engine > backup.sql

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres core_engine < backup.sql
```

## Security Hardening

### Network Security

- Services are isolated in Docker network
- Only necessary ports exposed
- Database and Redis not exposed to host

### Application Security

- Non-root users in all containers
- Read-only file systems where possible
- Security headers enabled
- Rate limiting configured

### Secrets Management

- All secrets in environment variables
- No hardcoded credentials
- Secure defaults with strong passwords

## Scaling

### Horizontal Scaling

Scale services independently:

```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=3
```

### Database Scaling

For high traffic, consider:
- Read replicas for PostgreSQL
- Redis clustering
- External managed databases (AWS RDS, etc.)

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database logs
   docker-compose -f docker-compose.prod.yml logs postgres

   # Verify environment variables
   docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE
   ```

2. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats

   # Adjust resource limits in docker-compose.prod.yml
   ```

3. **SSL Certificate Issues**
   ```bash
   # Verify certificate files
   ls -la nginx/ssl/

   # Test certificate validity
   openssl x509 -in nginx/ssl/cert.pem -text -noout
   ```

### Log Management

Centralized logging setup:

```bash
# View all service logs
docker-compose -f docker-compose.prod.yml logs -f

# Export logs for analysis
docker-compose -f docker-compose.prod.yml logs --since 24h > production.log
```

## Maintenance

### Updates

1. **Application Updates**
   ```bash
   # Pull latest changes
   git pull origin main

   # Rebuild and deploy
   docker-compose -f docker-compose.prod.yml build
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Database Migrations**
   ```bash
   # Run new migrations
   docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

3. **Dependency Updates**
   ```bash
   # Update Python dependencies
   pip-compile requirements.in

   # Update Node.js dependencies
   npm update

   # Rebuild containers
   docker-compose -f docker-compose.prod.yml build --no-cache
   ```

### Health Monitoring

Set up automated health checks:

```bash
# Add to crontab for automated monitoring
0 */6 * * * curl -f https://your-domain.com/health || echo "Service down" | mail admin@your-domain.com
```

## Emergency Procedures

### Service Recovery

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Full system recovery
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Data Recovery

```bash
# Restore from backup
docker-compose -f docker-compose.prod.yml down
docker volume rm workspace_postgres_data
docker-compose -f docker-compose.prod.yml up -d postgres
# Wait for postgres to initialize
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres core_engine < backup.sql
docker-compose -f docker-compose.prod.yml up -d
```

---

## Support

For production issues:
1. Check service logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify resource usage: `docker stats`
3. Check health endpoints: `/health`
4. Review environment variables
5. Consult the infrastructure review documentation

Remember to keep this guide updated with your specific production configuration and procedures.