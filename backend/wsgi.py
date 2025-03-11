"""
WSGI entry point for the Fore-Poster application in production.

This module configures the production environment and initializes the Flask application
for use with WSGI servers like Gunicorn, uWSGI, or mod_wsgi.
"""
# Standard library imports
import os
import sys

# Add the application directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables explicitly to ensure the application runs in production mode
# This is necessary because some WSGI servers may not pass environment variables from the system
# These must be set before importing the Flask application
os.environ['APP_ENV'] = 'production'
os.environ['FLASK_ENV'] = 'production'

# Local application imports
from fore_poster import app

if __name__ == "__main__":
    app.run()