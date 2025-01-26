# Fore-Poster Deployment Guide

## Prerequisites
- Ubuntu Server
- Python 3.8+
- Nginx
- PostgreSQL
- Domain with SSL certificate

## Environment Variables
```bash
# Database
DATABASE_URL="postgresql://user:pass@localhost:5432/fore_poster"

# Authentication
JWT_SECRET="your_secret"

# X API
X_API_KEY="your_key"
X_API_SECRET="your_secret"
X_ACCESS_TOKEN="your_token"
X_ACCESS_TOKEN_SECRET="your_token_secret"

# AWS (Production)
AWS_REGION="us-east-1"
SES_SENDER="email@domain.com"
SES_RECIPIENT="email@domain.com"
```

## Installation Steps

1. Database Setup
```bash
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
```

2. Application Setup
```bash
# Create directory and venv
mkdir -p /var/www/fore-poster
python3 -m venv /var/www/fore-poster/venv

# Install dependencies
source /var/www/fore-poster/venv/bin/activate
pip install flask flask_sqlalchemy tweepy PyJWT apscheduler boto3 gunicorn psycopg2-binary

# Copy application files
cp -r * /var/www/fore-poster/

# Initialize database
FLASK_ENV=production python3 -c "from fore_poster import app, db; db.create_all()"
```

3. Service Configuration
```bash
# Create log directory
sudo mkdir -p /var/log/fore-poster
sudo chown ubuntu:ubuntu /var/log/fore-poster

# Copy and enable services
sudo cp deployment/fore-poster.service /etc/systemd/system/
sudo cp deployment/fore-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fore-poster fore-scheduler
sudo systemctl start fore-poster fore-scheduler
```

4. Nginx Configuration
```bash
sudo cp deployment/nginx.conf /etc/nginx/sites-available/fore-poster
sudo ln -s /etc/nginx/sites-available/fore-poster /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

5. Log Rotation
```bash
sudo cp deployment/logrotate.conf /etc/logrotate.d/fore-poster
```

## Verification
```bash
# Check service status
sudo systemctl status fore-poster
sudo systemctl status fore-scheduler

# View logs
tail -f /var/log/fore-poster/*.log

# Test API
curl -X GET http://localhost:8000/api/test_connection
```