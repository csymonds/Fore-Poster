# Fore-Poster

A social media automation tool designed for technical content creators. Schedule and manage posts across platforms with a focus on technical education content.

<img src="https://www.visionstudioshub.com/img/fp.png" alt="Description" width="600" />

## Architecture

Fore-Poster consists of the following main components:

- **Backend API (`fore_poster.py`)**: The main Flask application that handles API requests and immediate posting
- **Scheduler (`fore_scheduler.py`)**: Background service that processes scheduled posts
- **Shared Components (`backend/core/`)**: Common functionality used by both the API and scheduler:
  - `notification.py`: Handles sending email alerts via AWS SES in production mode
  - `posting.py`: Common posting functionality for social media platforms
  - `models.py`: Shared data models

This architecture allows for consistent behavior between immediate and scheduled posts while maintaining the flexibility to run the scheduler as a separate process in production.

### Notification System Architecture

Fore-Poster includes a robust notification system that:
- Sends email alerts via AWS SES in production environments
- Logs notifications locally in development environments
- Includes detailed API responses in notifications for better debugging
- Uses a factory pattern to ensure proper initialization order

The notification system is properly initialized after the application configuration, ensuring it correctly reflects the current environment settings.

## Quick Start

### 1. Run the Setup Script
```bash
# Clone the repository
git clone <repository-url>
cd fore-poster

# Run the setup script
./setup.sh
```

The setup script will:
- Create a virtual environment if needed
- Set up the .env file from .env.example if none exists
- Ensure the environment configuration is correctly linked
- Offer to install dependencies for both backend and frontend
- Make development testing scripts executable

### 2. Start the Application

#### Option 1: Using Dev Scripts (Recommended)
```bash
# Start the backend (in one terminal)
./dev_backend.sh

# Start the frontend (in another terminal)
./dev_frontend.sh
```

The dev scripts provide:
- Automatic database reset with the backend script
- Option to start the scheduler alongside the backend
- Proper environment linking verification
- Better logging and error handling

#### Option 2: Manual Startup
```bash
# Reset and initialize the database with admin user
python backend/reset_db.py

# Start the Flask API server
python backend/run.py

# Start development server (in a new terminal)
cd frontend
npm run dev
```

### 3. Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api

## Deployment

Fore-Poster includes a comprehensive deployment script for pushing updates to production:

```bash
# Deploy backend code and restart services
./deploy.sh --backend --restart

# Deploy frontend only
./deploy.sh --frontend

# Deploy both and restart services
./deploy.sh --all

# Initialize/reset the database
./deploy.sh --init-db
```

The deployment script handles:
- Building the frontend with production settings
- Copying backend files to the server
- Setting up proper directory permissions
- Creating necessary instance directories
- Restarting systemd services
- Verifying service status after deployment

In production, the application runs as two systemd services:
- `fore-poster.service`: The main API application
- `fore-scheduler.service`: The background scheduler for processing scheduled posts

## Features
- Post scheduling and management
- Smart scheduling that automatically selects optimal posting times
- Multi-platform support (currently X/Twitter)
- Image uploads for social media posts
- Development/Production environment handling
- AWS SES integration for email notifications
- Secure authentication with JWT
- Background job processing

## Project Structure
```
fore-poster/
├── .env                  # Single source of truth for environment variables
├── .env.example          # Example environment file for reference
├── setup.sh              # Setup script for environment and dependencies
├── deploy.sh             # Production deployment script
├── backend/              # Flask backend
│   ├── instance/         # Database location
│   │   └── uploads/      # Uploaded images storage directory
│   ├── core/             # Shared modules
│   │   ├── __init__.py   # Package marker
│   │   ├── notification.py # Email notification system 
│   │   ├── posting.py    # Shared posting functionality
│   │   └── models.py     # Shared data models
│   ├── config.py         # Configuration management
│   ├── env_handler.py    # Environment variable handling
│   ├── fore_poster.py    # Main API application
│   ├── fore_scheduler.py # Background job scheduler
│   ├── reset_db.py       # Database initialization script
│   ├── run.py            # Main entry point for backend
│   └── wsgi.py           # WSGI entry point
├── frontend/             # React/TypeScript frontend
│   ├── .env              # Symlink to root .env file
│   ├── src/              # Source code
│   └── ...               # Frontend configuration files
└── requirements.txt      # Python dependencies
```

## Environment Setup

The project uses a single `.env` file in the root directory for all environment variables. This keeps configuration in one place and avoids duplication.

### Key Environment Variables

```
# Application environment (development, testing, production)
APP_ENV=development

# AWS SES Configuration for Notifications
AWS_REGION=us-east-1
SES_SENDER=your-verified-email@example.com
SES_RECIPIENT=notifications-recipient@example.com

# X/Twitter API Credentials
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret

# Database Configuration
DB_USER=dbuser
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fore_poster
```

For frontend access, a symbolic link is created from `frontend/.env` to the root `.env` file. This ensures that:
1. Vite can find environment variables in the expected location
2. Only variables with the `VITE_` prefix are exposed to the frontend code
3. Changes to the root `.env` file are immediately reflected in the frontend

The `setup.sh` script ensures this link is correctly created and maintained.

### Database
- Development: SQLite database in `backend/instance/fore_poster.db`
- Production: PostgreSQL database (configured via environment variables)

### Authentication
- JWT-based authentication
- Default admin user created from ADMIN_USERNAME and ADMIN_PASSWORD in .env

## Smart Scheduling Feature

Fore-Poster includes an intelligent scheduling system that automatically selects the optimal time to post your content based on social media best practices:

### Optimal Posting Times
The system recognizes three peak engagement periods:
- **Morning (7:00 AM)**: Catch your audience during their morning routine
- **Noon (11:00 AM)**: Reach users during lunch breaks 
- **Evening (6:00 PM)**: Connect with your audience after work hours

### How It Works
1. When creating a new post, the system analyzes your existing scheduled posts
2. It finds the next available optimal time slot that doesn't conflict with other posts
3. The time is automatically set for your new post
4. You'll see a message indicating that an optimal time was selected

### Quick Time Selection
For easy scheduling, three convenient buttons are provided:
- **Morning**: Schedule for 7:00 AM (today or tomorrow if it's already past)
- **Noon**: Schedule for 11:00 AM (today or tomorrow if it's already past)
- **Evening**: Schedule for 6:00 PM (today or tomorrow if it's already past)

### Custom Scheduling
If you prefer a different time, you can still:
- Use the date/time picker for complete customization
- Edit any suggested time to your preference

## Image Upload Feature

Fore-Poster supports adding images to your social media posts:

### Supported Image Types
- JPEG/JPG
- PNG
- GIF

### Image Limitations
- Maximum file size: 16MB
- Images are stored in the backend/instance/uploads directory
- When posting to X/Twitter, the image will be included in the post
- Images can be added when creating a post or editing an existing one
- Click the X button to remove an attached image

### Configuration
The image upload feature can be configured through these environment variables:

```
# Maximum file size in megabytes (default: 16)
MAX_UPLOAD_SIZE_MB=16

# Allowed file extensions (default: 'png,jpg,jpeg,gif')
ALLOWED_FILE_EXTENSIONS=png,jpg,jpeg,gif

# Cache duration for served images in seconds (default: 86400 - 1 day)
CACHE_MAX_AGE=86400
```

## Email Notifications

Fore-Poster sends email notifications about post status in production environments:

### Notification Types:
- **Post Successfully Published** - Sent when a post is successfully published to X
- **Post Failed** - Sent when there's an error publishing a post
- **Posting Error** - Sent when an exception occurs during the posting process

### Email Content:
Each notification includes:
- Post ID and content
- Platform details
- Complete API response from X
- Time of posting
- Any error messages or warnings

### Configuration:
Email notifications require AWS SES configuration in your .env file:
```
AWS_REGION=us-east-1
SES_SENDER=your-verified-email@example.com
SES_RECIPIENT=notifications-recipient@example.com
```

In development mode, notifications are logged to console and log files instead of sending emails.

## Troubleshooting

### Database Issues
If you encounter database errors, try resetting the database:
```bash
python backend/reset_db.py
```

### Environment Variable Issues
If your environment variables aren't being picked up correctly:
1. Check that the `.env` file exists in the project root
2. Verify that `frontend/.env` is a symbolic link to `../.env`
3. Run `./setup.sh` to fix any environment issues

### Notification System Issues
If emails aren't being sent in production:
1. Ensure AWS_REGION, SES_SENDER, and SES_RECIPIENT are properly set in .env
2. Check that the APP_ENV environment variable is set to 'production'
3. Restart both services after making environment changes:
   ```bash
   sudo systemctl restart fore-poster.service fore-scheduler.service
   ```

## License
MIT License - see LICENSE file for details