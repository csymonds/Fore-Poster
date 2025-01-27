#!/bin/sh

# Create directory and venv
mkdir -p /var/www/fore-poster
python3 -m venv /var/www/fore-poster/venv

# Install dependencies
source /var/www/fore-poster/venv/bin/activate
pip install flask flask_sqlalchemy tweepy PyJWT apscheduler boto3 gunicorn python-dotenv

# Copy service files
sudo cp fore-poster.service /etc/systemd/system/
sudo cp fore-scheduler.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start services
sudo systemctl start fore-poster
sudo systemctl start fore-scheduler

# Enable on boot
sudo systemctl enable fore-poster
sudo systemctl enable fore-scheduler

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

# Initial schema creation (after setting up venv and installing dependencies)
APP_ENV=production python3 << EOF
from fore_poster import app, db
with app.app_context():
    db.create_all()
EOF