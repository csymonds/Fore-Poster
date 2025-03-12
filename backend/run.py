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

# Set environment explicitly before anything else, but only once
# Check if we're being reloaded by Flask's debugger
if 'WERKZEUG_RUN_MAIN' not in os.environ:
    os.environ['APP_ENV'] = 'development'
    logger.info(f"Setting APP_ENV to development for local run")

    # Load environment before importing app, but only on first run
    from env_handler import load_environment

    # Look for .env.dev in parent directory (project root)
    env_dev_path = os.path.join(BASE_DIR.parent, ".env.dev")
    if os.path.exists(env_dev_path):
        logger.info(f"Loading development environment from: {env_dev_path}")
        load_environment(env_dev_path)
    else:
        # Fallback to finding .env.dev in current directory
        env_dev_path = os.path.join(BASE_DIR, ".env.dev")
        if os.path.exists(env_dev_path):
            logger.info(f"Loading development environment from: {env_dev_path}")
            load_environment(env_dev_path)
        else:
            logger.warning(f"Development environment file not found at: {env_dev_path}")
            logger.warning("Falling back to .env file. Application may not run correctly.")
            load_environment()
else:
    logger.info("Flask reloader detected - skipping environment reload")

# Now import the app
from fore_poster import app

if __name__ == "__main__":
    # Set a consistent instance path for database
    app.instance_path = os.path.join(BASE_DIR, "instance")
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Only log instance path on the first run
    if 'WERKZEUG_RUN_MAIN' not in os.environ:
        logger.info(f"Set instance path to: {app.instance_path}")
    
    port = int(os.environ.get("PORT", 8000))
    
    # Only log startup info on the first run
    if 'WERKZEUG_RUN_MAIN' not in os.environ:
        logger.info(f"Starting Fore-Poster backend on port {port}")
        logger.info(f"Environment: {os.environ.get('APP_ENV')}")
        logger.info(f"Database path: {os.path.join(app.instance_path, 'fore_poster.db')}")
    
    # Debug mode only in development environments
    debug_mode = os.environ.get('APP_ENV') != 'production'
    if 'WERKZEUG_RUN_MAIN' not in os.environ:
        logger.info(f"Debug mode: {debug_mode}")
    
    app.run(debug=debug_mode, port=port) 