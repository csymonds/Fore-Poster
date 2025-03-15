# Fore-Poster

A social media automation tool designed for technical content creators. Schedule and manage posts across platforms with a focus on technical education content.

<img src="https://www.visionstudioshub.com/img/fp1.png" alt="Description" width="600" />
<img src="https://www.visionstudioshub.com/img/fp2.png" alt="Description" width="600" />

## Architecture

Fore-Poster consists of the following main components:

- **Backend API (`fore_poster.py`)**: The main Flask application that handles API requests and immediate posting
- **Scheduler (`fore_scheduler.py`)**: Background service that processes scheduled posts
- **Shared Components (`backend/core/`)**: Common functionality used by both the API and scheduler:
  - `notification.py`: Handles sending email alerts via AWS SES in production mode
  - `posting.py`: Common posting functionality for social media platforms
  - `models.py`: Shared data models
  - `ai_service.py`: AI content generation using OpenAI's Responses API

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


## Features
- Post scheduling and management
- Smart scheduling that automatically selects optimal posting times
- Multi-platform support (currently X/Twitter)
- Image uploads for social media posts
- Development/Production environment handling
- AWS SES integration for email notifications
- Secure authentication with JWT
- Background job processing
- AI content generation using OpenAI's Responses API


## AI Content Generation

Fore-Poster includes AI-assisted content creation:

### Features
- Generate social media post content with a single click
- Real-time streaming of AI responses using Server-Sent Events
- Configurable system prompts and parameters
- Optional web search capability for more informed content
- Customizable temperature setting to control creativity

### Technology
- Integrated with OpenAI's Responses API
- Secure authentication using Bearer tokens
- Server-side streaming for responsive user experience

### Configuration
AI settings can be adjusted through the application's settings panel:
- System prompt: Customize the AI's behavior and tone
- Temperature: Adjust from factual (lower) to creative (higher)
- Web search: Enable/disable web search capabilities

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

## Development Status and Disclaimer

**Note:** This project is under active development and some features may be incomplete or experience occasional issues. It was developed with assistance from AI tools, which may have introduced inconsistencies or inaccuracies in certain parts of the codebase or documentation. Users are encouraged to report any issues they encounter.

## License
MIT License - see LICENSE file for details