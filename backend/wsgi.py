import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Explicitly set APP_ENV to production before importing the app
os.environ['APP_ENV'] = 'production'
os.environ['FLASK_ENV'] = 'production'

from fore_poster import app

if __name__ == "__main__":
    app.run()