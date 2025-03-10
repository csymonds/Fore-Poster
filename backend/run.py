"""
Main entry point for the Fore-Poster backend.
Run this file to start the Flask server.
"""
import os
import sys
from pathlib import Path

# Ensure the backend directory is in the path
# This makes imports work consistently regardless of where script is called from
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# Load environment before importing app
from env_handler import load_environment
load_environment()

# Now import the app
from fore_poster import app

if __name__ == "__main__":
    # Set a consistent instance path for database
    app.instance_path = os.path.join(BASE_DIR, "instance")
    os.makedirs(app.instance_path, exist_ok=True)
    
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Fore-Poster backend on port {port}")
    print(f"Database path: {os.path.join(app.instance_path, 'fore_poster.db')}")
    
    app.run(debug=True, port=port) 