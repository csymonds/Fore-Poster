"""
Main entry point for the Fore-Poster backend.
Run this file to start the Flask server.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fore_poster_run.log')
    ]
)
logger = logging.getLogger(__name__)

# Ensure the backend directory is in the path
# This makes imports work consistently regardless of where script is called from
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# Load environment before importing app
from env_handler import load_environment, get_env_var
load_environment()

# Now import the app
from fore_poster import app

if __name__ == "__main__":
    # Set a consistent instance path for database
    app.instance_path = os.path.join(BASE_DIR, "instance")
    os.makedirs(app.instance_path, exist_ok=True)
    
    port = int(os.environ.get("PORT", 8000))
    app_env = get_env_var('APP_ENV', 'development')
    
    logger.info(f"Starting Fore-Poster backend on port {port}")
    logger.info(f"Environment: {app_env}")
    logger.info(f"Database path: {os.path.join(app.instance_path, 'fore_poster.db')}")
    
    # Ensure debug mode is disabled in production
    debug_mode = app_env != 'production'
    if app_env == 'production' and debug_mode:
        logger.error("ERROR: Debug mode should not be enabled in production!")
        sys.exit(1)
    
    logger.info(f"Debug mode: {debug_mode}")
    app.run(debug=debug_mode, port=port) 