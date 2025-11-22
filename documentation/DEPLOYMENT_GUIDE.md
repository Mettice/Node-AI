# NodAI Deployment Guide

Complete guide to deploying NodAI in production.

---

## 🚀 Production Deployment

### Prerequisites

- **Server:** Linux/macOS server (Ubuntu 20.04+ recommended)
- **Python:** 3.10+
- **Node.js:** 18+ (for building frontend)
- **Database:** PostgreSQL (optional, for production)
- **Reverse Proxy:** Nginx (recommended)

---

## 📦 Step 1: Environment Setup

### 1.1 Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install nginx -y
```

### 1.2 Clone and Setup

```bash
# Clone repository
git clone <your-repo-url>
cd Nodeflow

# Create production user
sudo useradd -m -s /bin/bash nodai
sudo chown -R nodai:nodai /path/to/Nodeflow
```

---

## 🔧 Step 2: Backend Configuration

### 2.1 Environment Variables

Create `/etc/nodai/.env`:

```env
# Environment
ENVIRONMENT=production
DEBUG=False

# API Keys
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
GEMINI_API_KEY=your-key

# Server
HOST=0.0.0.0
PORT=8000

# CORS (IMPORTANT: Set your production domain)
CORS_ORIGINS_STR=https://yourdomain.com,https://www.yourdomain.com

# Sentry (Recommended)
SENTRY_DSN=https://your-sentry-dsn
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# JWT Secret (CHANGE THIS!)
JWT_SECRET_KEY=generate-a-strong-random-secret-key

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost/nodai
```

### 2.2 Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.3 Create Systemd Service

Create `/etc/systemd/system/nodai-backend.service`:

```ini
[Unit]
Description=NodAI Backend API
After=network.target

[Service]
Type=simple
User=nodai
WorkingDirectory=/path/to/Nodeflow/backend
Environment="PATH=/path/to/Nodeflow/backend/venv/bin"
EnvironmentFile=/etc/nodai/.env
ExecStart=/path/to/Nodeflow/backend/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nodai-backend
sudo systemctl start nodai-backend
sudo systemctl status nodai-backend
```

---

## 🎨 Step 3: Frontend Build

### 3.1 Build Frontend

```bash
cd frontend
npm install
npm run build
```

This creates a `dist/` folder with production-ready files.

### 3.2 Configure Nginx

Create `/etc/nginx/sites-available/nodai`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    root /path/to/Nodeflow/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support (for SSE)
    location /api/v1/executions/stream {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/nodai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3.3 SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 🔒 Step 4: Security Hardening

### 4.1 Firewall

```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 4.2 File Permissions

```bash
# Secure .env file
sudo chmod 600 /etc/nodai/.env
sudo chown nodai:nodai /etc/nodai/.env

# Secure data directories
sudo chown -R nodai:nodai /path/to/Nodeflow/backend/data
sudo chmod -R 750 /path/to/Nodeflow/backend/data
```

### 4.3 Environment Variables

**CRITICAL:** Never commit `.env` files. Use environment variables or secrets management:

```bash
# Option 1: Environment file (secure location)
/etc/nodai/.env

# Option 2: Systemd environment file
/etc/systemd/system/nodai-backend.service.d/override.conf

# Option 3: Secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
```

---

## 📊 Step 5: Monitoring

### 5.1 Sentry Setup

1. **Create Sentry account:** https://sentry.io
2. **Create project:** Select "FastAPI"
3. **Get DSN:** Copy from project settings
4. **Add to .env:**
   ```env
   SENTRY_DSN=https://your-dsn@sentry.io/project-id
   SENTRY_ENVIRONMENT=production
   ```

### 5.2 Logging

Logs are available at:
- **Systemd logs:** `sudo journalctl -u nodai-backend -f`
- **Nginx logs:** `/var/log/nginx/access.log` and `/var/log/nginx/error.log`

### 5.3 Health Checks

Monitor backend health:
```bash
curl http://localhost:8000/api/v1/health
```

---

## 🔄 Step 6: Updates and Maintenance

### 6.1 Update Backend

```bash
cd /path/to/Nodeflow
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart nodai-backend
```

### 6.2 Update Frontend

```bash
cd frontend
git pull
npm install
npm run build
sudo systemctl reload nginx
```

### 6.3 Backup Strategy

```bash
# Backup workflows
tar -czf backups/workflows-$(date +%Y%m%d).tar.gz backend/data/workflows/

# Backup database (if using)
pg_dump nodai > backups/db-$(date +%Y%m%d).sql

# Automated backup script (add to crontab)
0 2 * * * /path/to/backup-script.sh
```

---

## 🐳 Docker Deployment (Alternative)

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .

# Run
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
    volumes:
      - ./backend/data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

---

## ✅ Production Checklist

- [ ] Environment variables configured
- [ ] CORS origins set to production domain
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Sentry configured
- [ ] Systemd service running
- [ ] Nginx configured and running
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Logs accessible
- [ ] Health checks passing

---

## 🆘 Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u nodai-backend -n 50

# Check environment
sudo systemctl show nodai-backend | grep Environment

# Test manually
cd backend
source venv/bin/activate
python -m backend.main
```

### Frontend not loading

```bash
# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check file permissions
ls -la frontend/dist/

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### API errors

- Check CORS configuration
- Verify API keys
- Check Sentry for error details
- Review backend logs

---

## 📚 Additional Resources

- **Nginx Documentation:** https://nginx.org/en/docs/
- **Systemd Guide:** https://www.freedesktop.org/software/systemd/man/systemd.service.html
- **Let's Encrypt:** https://letsencrypt.org/docs/
- **Sentry Docs:** https://docs.sentry.io/platforms/python/guides/fastapi/

---

**Your NodAI instance is now production-ready! 🚀**

