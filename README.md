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

## Development Setup

### Environment Configuration

1. Set up separate environment files:
   - Backend: Use the `.env.example` file in the `backend` directory to create a '.env' file there
   - Frontend: Create a `.env` file in the `frontend` directory with just:
     ```
     VITE_API_BASE_URL=http://localhost:8000/api
     ```

2. Install backend dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

### Running the Application

#### Backend

Reset the database and create an admin user:
```bash
cd backend
python reset_db.py
```

Start the Flask API server:
```bash
cd backend
python run.py
```

To run the scheduler separately for development:
```bash
cd backend
python fore_scheduler.py
```

#### Frontend

Start the Vite development server:
```bash
cd frontend
npm run dev
```

### Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api

## Production Deployment

Fore-Poster includes a deployment script for pushing updates to production:

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
├── deploy.sh             # Production deployment script
├── backend/              # Flask backend
│   ├── .env              # Backend environment configuration
│   ├── .env.example      # Example backend environment file
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
│   ├── .env              # Frontend environment configuration
│   ├── src/              # Source code
│   └── ...               # Frontend configuration files
└── requirements.txt      # Python dependencies
```

## Environment Configuration

The project uses separate `.env` files for backend and frontend, each in their own directory:

### Backend Environment Variables (`backend/.env`)

The backend environment file includes configuration for:
- Application environment (development/production)
- AWS SES for email notifications
- X/Twitter API credentials
- Database connection settings
- JWT authentication secrets
- Admin user credentials

### Frontend Environment Variables (`frontend/.env`)

The frontend environment file contains only:
```
VITE_API_BASE_URL=http://localhost:8000/api
```

This separation ensures that:
1. Frontend code only has access to the API URL it needs
2. Backend sensitive information stays isolated from the frontend
3. Each part of the application can be configured independently

### Database
- Development: SQLite database in `backend/instance/fore_poster.db`
- Production: PostgreSQL database (configured via environment variables)

### Authentication
- JWT-based authentication
- Default admin user created from credentials in the backend .env file

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
The image upload feature can be configured through environment variables in your backend .env file.

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
Email notifications require AWS SES configuration in your backend `.env` file.

In development mode, notifications are logged to console and log files instead of sending emails.

## Troubleshooting

### Database Issues
If you encounter database errors, try resetting the database:
```bash
cd backend
python reset_db.py
```

### Environment Variable Issues
If your environment variables aren't being picked up correctly:

1. For backend issues:
   - Verify that `.env` exists in the backend directory
   - Check that environment variables are correctly formatted (no spaces around = signs)
   - Ensure no trailing spaces or comments on the same line as variables

2. For frontend issues:
   - Verify that `frontend/.env` exists and contains VITE_API_BASE_URL
   - After changing frontend environment variables, restart the Vite dev server

### Notification System Issues
If emails aren't being sent in production:
1. Ensure AWS_REGION, SES_SENDER, and SES_RECIPIENT are properly set in backend .env
2. Check that the APP_ENV environment variable is set to 'production'
3. Restart both services after making environment changes:
   ```bash
   sudo systemctl restart fore-poster.service fore-scheduler.service
   ```

## Development Status and Disclaimer

**Note:** This project is under active development and some features may be incomplete or experience occasional issues. It was developed with assistance from AI tools, which may have introduced inconsistencies or inaccuracies in certain parts of the codebase or documentation. Users are encouraged to report any issues they encounter.

## License
MIT License - see LICENSE file for details