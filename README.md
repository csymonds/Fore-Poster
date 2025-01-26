# Fore-Poster

Social media automation tool designed for technical content creators. Schedule and manage posts across platforms with a focus on technical education content.

## Features
- Post scheduling and management
- Multi-platform support (currently X/Twitter)
- Development/Production environment handling
- AWS SES integration for notifications
- Secure authentication with JWT
- Background job processing

## Tech Stack
- Flask API backend
- PostgreSQL database (SQLite for development)
- APScheduler for job management
- AWS SES for email notifications
- Tweepy for X/Twitter integration

## Development Setup
1. Clone repository
2. Set up virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
4. Set environment variables
- JWT_SECRET
- X_API_KEY
- X_API_SECRET
- X_ACCESS_TOKEN
- X_ACCESS_TOKEN_SECRET

5. Run development server
```bash
python fore_poster.py
```

## Testing
```bash
pytest test_fore_poster.py
```

See [deployment guide](deployment/README.md) for production setup.

## License
MIT License