# Hosted Deployment Guide

This guide covers deploying NodAI as a hosted service for external access.

## 🚀 Deployment Options

### Option 1: Self-Hosted (VPS/Cloud)

**Recommended Platforms:**
- AWS EC2
- Google Cloud Compute Engine
- DigitalOcean Droplets
- Linode
- Azure Virtual Machines

**Requirements:**
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.8+
- Node.js 18+ (for frontend)
- 2GB+ RAM
- 20GB+ storage

### Option 2: Containerized (Docker)

**Docker Compose Setup:**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - CORS_ORIGINS=https://yourdomain.com
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=https://api.yourdomain.com
    restart: unless-stopped
```

### Option 3: Platform-as-a-Service

**Recommended Platforms:**
- Railway
- Render
- Fly.io
- Heroku
- Vercel (frontend only)

## 🔧 Environment Configuration

### Backend Environment Variables

Create a `.env` file in the project root:

```bash
# Application
APP_NAME=NodAI
DEBUG=false
HOST=0.0.0.0
PORT=8000

# CORS (comma-separated list of allowed origins)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# API Keys (for LLM providers)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
VOYAGE_API_KEY=...

# Database (optional, for future use)
DATABASE_URL=postgresql://user:pass@localhost/nodai

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/nodai/app.log
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
VITE_API_URL=https://api.yourdomain.com
```

## 🔐 Security Best Practices

### 1. API Key Management

- Store API keys in environment variables, never in code
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly
- Use different keys for different environments

### 2. HTTPS/SSL

**Required for production!**

- Use Let's Encrypt (free SSL certificates)
- Configure reverse proxy (Nginx, Caddy)
- Enable HSTS headers
- Redirect HTTP to HTTPS

### 3. CORS Configuration

Only allow trusted origins:

```bash
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 4. Rate Limiting

Consider adding:
- Per-IP rate limiting (using middleware)
- Per-API-key rate limiting (already implemented)
- DDoS protection (Cloudflare, AWS Shield)

### 5. Authentication

For admin endpoints:
- Implement JWT authentication
- Use secure session management
- Enable 2FA for admin accounts

## 📊 Scaling Considerations

### Horizontal Scaling

**Backend:**
- Use a load balancer (Nginx, HAProxy)
- Run multiple backend instances
- Use shared storage for workflows/data
- Consider Redis for session management

**Frontend:**
- Use CDN (Cloudflare, CloudFront)
- Enable caching
- Use static hosting (Vercel, Netlify)

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Use faster storage (SSD)
- Optimize database queries (when using DB)

### Database Scaling

When migrating to a database:
- Use connection pooling
- Implement read replicas
- Use database clustering
- Consider managed databases (RDS, Cloud SQL)

## 🔄 Deployment Process

### 1. Initial Setup

```bash
# Clone repository
git clone https://github.com/yourorg/nodai.git
cd nodai

# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Build Frontend

```bash
cd frontend
npm run build
# Output in frontend/dist/
```

### 3. Run Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Serve Frontend

```bash
# Option 1: Nginx
sudo cp nginx.conf /etc/nginx/sites-available/nodai
sudo ln -s /etc/nginx/sites-available/nodai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Option 2: Serve from backend (static files)
# Copy frontend/dist/* to backend/static/
```

## 🌐 Reverse Proxy Configuration (Nginx)

```nginx
# Backend API
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    root /var/www/nodai/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 📈 Monitoring

### Application Monitoring

- **Logs**: Use centralized logging (ELK, Loki, CloudWatch)
- **Metrics**: Prometheus + Grafana
- **APM**: Sentry, New Relic, Datadog
- **Uptime**: UptimeRobot, Pingdom

### Key Metrics to Monitor

- Request rate
- Response times
- Error rates
- API key usage
- Cost per query
- Server resources (CPU, RAM, disk)

## 🔄 Backup Strategy

### What to Backup

1. **Workflows**: JSON files in `data/workflows/`
2. **Vector Stores**: FAISS indexes in `data/vectors/`
3. **Uploaded Files**: Files in `data/uploads/`
4. **API Keys**: Files in `backend/data/api_keys/`
5. **Usage Logs**: Files in `backend/data/api_usage/`

### Backup Schedule

- **Daily**: Full backup of all data
- **Hourly**: Incremental backup of workflows and usage logs
- **Real-time**: Replicate to secondary storage

### Backup Tools

- `rsync` for file backups
- Database dumps (when using DB)
- Cloud storage (S3, GCS, Azure Blob)

## 🚨 Disaster Recovery

1. **Document recovery procedures**
2. **Test backups regularly**
3. **Maintain off-site backups**
4. **Have a rollback plan**
5. **Keep recovery time objective (RTO) < 1 hour**

## 📝 Maintenance

### Regular Tasks

- **Weekly**: Review logs, check disk space
- **Monthly**: Update dependencies, review security
- **Quarterly**: Review and optimize costs
- **Annually**: Security audit, disaster recovery test

### Updates

```bash
# Pull latest code
git pull origin main

# Update dependencies
cd backend && pip install -r requirements.txt --upgrade
cd ../frontend && npm update

# Restart services
sudo systemctl restart nodai-backend
sudo systemctl restart nginx
```

## 🎯 Production Checklist

- [ ] HTTPS/SSL configured
- [ ] CORS properly configured
- [ ] Environment variables set
- [ ] API keys secured
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Logging configured
- [ ] Rate limiting enabled
- [ ] Error handling tested
- [ ] Documentation updated
- [ ] Team trained on deployment

## 📞 Support

For deployment issues:
- Check logs: `tail -f /var/log/nodai/app.log`
- Review documentation
- Open an issue on GitHub
- Contact support@nodai.io

