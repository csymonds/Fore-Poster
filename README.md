# Fore-Poster

A social media automation tool designed for technical content creators. Schedule and manage posts across platforms with a focus on technical education content.

<img src="https://www.visionstudioshub.com/img/fp.png" alt="Description" width="600" />

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

## Features
- Post scheduling and management
- Multi-platform support (currently X/Twitter)
- Image uploads for social media posts
- Development/Production environment handling
- AWS SES integration for notifications
- Secure authentication with JWT
- Background job processing

## Project Structure
```
fore-poster/
├── .env                  # Single source of truth for environment variables
├── .env.example          # Example environment file for reference
├── setup.sh              # Setup script for environment and dependencies
├── backend/              # Flask backend
│   ├── instance/         # Database location
│   │   └── uploads/      # Uploaded images storage directory
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

## License
MIT License - see LICENSE file for details

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