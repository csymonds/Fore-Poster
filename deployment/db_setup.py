import os
from werkzeug.security import generate_password_hash
import hashlib
from env_handler import load_environment

# Load environment variables before importing the app
load_environment()

# Define the robust password hashing function
def robust_password_hash(password):
    """
    Create a password hash that works across environments.
    Falls back to different methods if preferred ones aren't available.
    """
    # Check if scrypt is available (default in newer Python versions)
    if hasattr(hashlib, 'scrypt'):
        try:
            return generate_password_hash(password)  # Default is scrypt
        except Exception:
            pass  # Fall through to alternatives
    
    # Use pbkdf2 which is widely available
    return generate_password_hash(password, method='pbkdf2:sha256')

# Now import the app and models
from fore_poster import app, db, User

with app.app_context():
    db.drop_all()  # Reset database
    db.create_all()
    
    # Create admin user
    default_user = User(
        username=os.getenv('ADMIN_USERNAME'),
        password=robust_password_hash(os.getenv('ADMIN_PASSWORD'))
    )
    db.session.add(default_user)
    db.session.commit()

    print("Database setup complete.")
    print(f"Created admin user: {os.getenv('ADMIN_USERNAME')}")