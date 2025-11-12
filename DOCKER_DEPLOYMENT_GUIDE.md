# Docker Deployment Guide for Todo API

## 🐳 Quick Start

### Development Environment
```bash
# Start development environment with hot reload
docker-compose -f docker-compose.dev.yml up --build

# Run tests in development container
docker-compose -f docker-compose.dev.yml exec todo-api-dev pytest

# Access the API
curl http://localhost:8000/health
```

### Production Environment
```bash
# Build and start production containers
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f todo-api

# Stop services
docker-compose down
```

## 🔧 Configuration

### Environment Variables
Create `.env` file in project root:

```bash
# Production Environment Variables
SECRET_KEY=your-super-secure-secret-key-minimum-32-characters
POSTGRES_PASSWORD=your-secure-database-password
REDIS_PASSWORD=your-redis-password

# Optional: Database Configuration
DATABASE_URL=postgresql://todouser:password@postgres:5432/todoapi

# Optional: External URLs
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

### Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Auto-reload | ✅ Yes | ❌ No |
| Debug mode | ✅ On | ❌ Off |
| Database | SQLite/PostgreSQL | PostgreSQL |
| Logging | Console + File | JSON + File |
| Security | Relaxed | Strict |
| Performance | Basic | Optimized |

## 📊 Container Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   Todo API      │    │   PostgreSQL    │
│   (Port 80/443) │───▶│   (Port 8000)   │───▶│   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Port 6379)   │
                       └─────────────────┘
```

## 🔍 Health Checks

All containers include health checks:

```bash
# Check API health
curl http://localhost:8000/health

# Check all container health
docker-compose ps

# Detailed health status
docker inspect --format='{{.State.Health.Status}}' todo-api-prod
```

## 📝 Logging

### Access Logs
```bash
# View API logs
docker-compose logs -f todo-api

# View specific log files
docker-compose exec todo-api tail -f logs/todo_api.log
docker-compose exec todo-api tail -f logs/todo_api_errors.log
docker-compose exec todo-api tail -f logs/todo_api_access.log
```

### Log Rotation
- Logs are automatically rotated at 10MB
- 5 backup files are kept
- JSON format in production for structured logging

## 🚀 Deployment Strategies

### 1. Development Deployment
```bash
# Start development stack
docker-compose -f docker-compose.dev.yml up -d

# Run tests
docker-compose -f docker-compose.dev.yml exec todo-api-dev pytest -v

# Code changes are auto-reloaded
```

### 2. Production Deployment
```bash
# Pull latest code
git pull origin main

# Build and deploy
docker-compose up --build -d

# Verify deployment
curl -f http://localhost:8000/health
```

### 3. Zero-Downtime Deployment
```bash
# Build new image
docker-compose build todo-api

# Rolling update
docker-compose up -d --no-deps todo-api

# Verify health
docker-compose exec todo-api curl -f http://localhost:8000/health
```

## 🔒 Security

### Container Security
- ✅ Non-root user (appuser)
- ✅ Read-only filesystem where possible
- ✅ Limited capabilities
- ✅ Security headers in responses
- ✅ Regular security updates

### Network Security
```bash
# Internal network isolation
docker network ls

# Only expose necessary ports
# API: 8000, Database: Internal only
```

### Secrets Management
```bash
# Use Docker secrets for production
echo "your-secret-key" | docker secret create api_secret_key -

# Mount secrets in compose file
secrets:
  api_secret_key:
    external: true
```

## 📈 Monitoring

### Built-in Monitoring
```bash
# Health endpoint with metrics
curl http://localhost:8000/health

# Container resource usage
docker stats

# Container logs
docker-compose logs --tail=100 -f
```

### Production Monitoring Stack
```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

## 🛠️ Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs todo-api

# Check configuration
docker-compose config

# Rebuild with no cache
docker-compose build --no-cache
```

#### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test database connectivity
docker-compose exec todo-api python -c "import aiosqlite; print('SQLite OK')"

# For PostgreSQL
docker-compose exec postgres psql -U todouser -d todoapi -c "SELECT 1;"
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check container health
docker-compose ps

# Scale services if needed
docker-compose up -d --scale todo-api=3
```

### Debugging Commands
```bash
# Enter container shell
docker-compose exec todo-api /bin/bash

# Run Python shell
docker-compose exec todo-api python

# Check file permissions
docker-compose exec todo-api ls -la /app

# Test API endpoints
docker-compose exec todo-api python -m pytest test_comprehensive.py -v
```

## 🔄 Backup & Recovery

### Database Backup
```bash
# SQLite backup
docker-compose exec todo-api cp data/todos.db data/todos_backup_$(date +%Y%m%d).db

# PostgreSQL backup
docker-compose exec postgres pg_dump -U todouser todoapi > backup_$(date +%Y%m%d).sql
```

### Volume Backup
```bash
# Create volume backup
docker run --rm \
  -v todo_data:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/todo_data_backup.tar.gz -C /source .
```

## 📱 API Testing

### Quick API Tests
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Create todo (use token from login)
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"title":"Test Todo","description":"Docker deployment test","completed":false}'
```

## 🚀 Production Checklist

Before deploying to production:

- [ ] Update SECRET_KEY in .env
- [ ] Set ENVIRONMENT=production
- [ ] Configure proper CORS origins
- [ ] Set up SSL certificates
- [ ] Configure database backups
- [ ] Set up monitoring and alerting
- [ ] Test health checks
- [ ] Verify all endpoints work
- [ ] Run security scan
- [ ] Load test the API
- [ ] Document rollback procedure

---

**Your Todo API is now fully containerized and production-ready! 🎉**