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

# Set instance path explicitly for production
# This is critical for correct operation when running through WSGI
app.instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
os.makedirs(app.instance_path, exist_ok=True)
app.logger.info(f"Production instance path set to: {app.instance_path}")

# Set up upload folder from environment
upload_dir = os.getenv('UPLOAD_FOLDER', 'instance/uploads')
upload_folder = os.path.join(app.instance_path, upload_dir.replace('instance/', ''))
os.makedirs(upload_folder, exist_ok=True)
app.logger.info(f"Production upload folder set to: {upload_folder}")

if __name__ == "__main__":
    app.run()