# Fore-Poster

A social media automation tool designed for technical content creators. Schedule and manage posts across platforms with a focus on technical education content.

## Features
- Post scheduling and management
- Multi-platform support (currently X/Twitter)
- Development/Production environment handling
- AWS SES integration for notifications
- Secure authentication with JWT
- Background job processing

## Tech Stack
### Backend
- Flask API with SQLAlchemy
- PostgreSQL (production) / SQLite (development)
- APScheduler for job management
- AWS SES for email notifications
- Tweepy for X/Twitter integration

### Frontend
- React with TypeScript
- Vite build system
- TailwindCSS for styling
- React Query for state management

## Project Structure
```
fore-poster/
├── backend/             # Flask backend
│   ├── config.py       # Configuration management
│   ├── env_handler.py  # Environment variable handling
│   ├── fore_poster.py  # Main API application
│   ├── fore_scheduler.py # Background job scheduler
│   └── wsgi.py        # WSGI entry point
├── frontend/           # React/TypeScript frontend
│   ├── src/           # Source code
│   └── ...            # Frontend configuration files
├── deployment/         # Deployment configurations
│   ├── fore-poster.service    # Systemd service for API
│   ├── fore-scheduler.service # Systemd service for scheduler
│   └── ...            # Additional deployment files
└── requirements.txt    # Python dependencies
```

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Local Environment Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd fore-poster
```

2. Create and activate Python virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install backend dependencies:
```bash
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
```

5. Configure environment:
- Copy `.env.example` to `.env`
- Update with your development settings
- Required variables are documented in the example file

### Running for Development

```bash
# Terminal 1 - Backend API
python backend/fore_poster.py

# Terminal 2 - Scheduler (if needed)
python backend/fore_scheduler.py

# Terminal 3 - Frontend
cd frontend
npm run dev
```

## Production Deployment

### Server Prerequisites
- Ubuntu Server (or similar Linux)
- Python 3.8+
- PostgreSQL
- Nginx
- SSL certificate
- Domain name

### Installation Steps

1. Database Setup:
```bash
sudo -u postgres psql
CREATE DATABASE fore_poster;
CREATE USER fpuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fore_poster TO fpuser;
```

2. Application Setup:
```bash
# Create application directory
sudo mkdir -p /var/www/fore-poster
sudo chown $USER:$USER /var/www/fore-poster

# Clone and setup
git clone <repository-url>
cd fore-poster
python3 -m venv /var/www/fore-poster/venv
source /var/www/fore-poster/venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
npm run build
cd ../
cp -r public backend/* /var/www/fore-poster/
```

3. Configure Services:
```bash
# Create log directory
sudo mkdir -p /var/log/fore-poster
sudo chown $USER:$USER /var/log/fore-poster

# Copy and modify service files
sudo cp deployment/fore-poster.service /etc/systemd/system/
sudo cp deployment/fore-scheduler.service /etc/systemd/system/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable fore-poster fore-scheduler
sudo systemctl start fore-poster fore-scheduler

# Verify services are running
sudo systemctl status fore-poster
sudo systemctl status fore-scheduler

# View logs:
journalctl -u fore-poster -f
journalctl -u fore-scheduler -f
```

4. Configure Web Server:
```bash
# Copy nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/fore-poster
sudo ln -s /etc/nginx/sites-available/fore-poster /etc/nginx/sites-enabled/

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

5. Set Up Log Rotation:
```bash
# Copy logrotate configuration
sudo cp deployment/logrotate.conf /etc/logrotate.d/fore-poster
```

6. Verify Installation:
```bash
# Check API connectivity
curl -X GET http://localhost:8000/api/test_connection

# Check logs for any errors
tail -f /var/log/fore-poster/*.log

# Monitor service logs
journalctl -u fore-poster -f
journalctl -u fore-scheduler -f
```

### Environment Variables
Key variables required for production:
- Database configuration (DB_NAME, DB_USER, DB_PASSWORD, etc.)
- JWT secret for authentication
- X/Twitter API credentials
- AWS SES configuration (if using email notifications)
- Admin credentials

See `.env.example` for a complete list.

## Maintenance

### Log Management
The application uses both systemd journal and file-based logging:

1. Service Logs (via systemd):
```bash
# API logs
journalctl -u fore-poster -f

# Scheduler logs
journalctl -u fore-scheduler -f
```

2. Application Logs (in /var/log/fore-poster/):
- fore_poster.log: Main application logs
- error.log: Error-specific logs
- scheduler.log: Background job logs

Log rotation is configured to:
- Rotate logs daily
- Keep 14 days of logs
- Compress old logs
- Handle log ownership and permissions

### Updates
1. Pull latest code:
```bash
cd /var/www/fore-poster
git pull
```

2. Update dependencies:
```bash
# Backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run build
```

3. Restart services:
```bash
sudo systemctl restart fore-poster fore-scheduler
```

## Security Considerations

### Authentication & Authorization
- JWT tokens are used for API authentication
- Tokens expire after 24 hours
- All API endpoints require authentication
- Admin credentials should be changed immediately after setup

### API Security
- CORS must be properly configured for your domain
- Rate limiting should be implemented in production
- All API requests must use HTTPS
- API endpoints follow principle of least privilege

### Environment Security
- All environment variables must be properly secured
- Use different secrets for development and production
- JWT secrets should be strong (min 32 characters) and rotated regularly
- Database passwords should be strong and unique

### X/Twitter API
- Requires Elevated API access level
- API keys should have minimum required permissions
- Implement API rate limit monitoring

### AWS Integration
- Use IAM roles with minimum required permissions
- SES requires verified domain and email addresses
- Monitor AWS CloudWatch for unusual activity
- Enable AWS CloudTrail for API logging

### Database Security
- Use strong, unique passwords
- Regular database backups
- Limit database user permissions
- Consider encryption at rest

### Application Security
- Keep all dependencies updated
- Regular security audits
- Monitor application logs for unusual activity
- Implement request validation

### Infrastructure
- Server hardening (firewall, SSH configuration)
- Regular system updates
- SSL/TLS configuration and renewal
- Network access controls


## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## Support
For issues and feature requests, please open an issue in the repository.

## License
MIT License - see LICENSE file for details