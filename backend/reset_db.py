"""
Reset and initialize the database with an admin user.
Run this script after setting up your .env file.
"""
import os
import sys
from pathlib import Path

# Ensure the backend directory is in the path
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# Load environment before importing app
from env_handler import load_environment, get_env_var
load_environment()

# Set instance path for consistent database location
os.environ['FLASK_APP'] = 'fore_poster'
instance_path = os.path.join(BASE_DIR, "instance")
os.makedirs(instance_path, exist_ok=True)

# Import after environment is loaded
from fore_poster import app, db, User, robust_password_hash

# Get admin credentials from environment
admin_username = get_env_var('ADMIN_USERNAME')
admin_password = get_env_var('ADMIN_PASSWORD')

print(f"Using admin username: {admin_username}")
print(f"Admin password is set (not shown for security)")

# Use the same instance path as run.py
app.instance_path = instance_path
db_path = os.path.join(instance_path, 'fore_poster.db')
print(f"Database will be created at: {db_path}")

with app.app_context():
    # Reset database
    db.drop_all()
    db.create_all()
    
    # Create admin user with credentials from .env
    admin_user = User(
        username=admin_username,
        password=robust_password_hash(admin_password)
    )
    db.session.add(admin_user)
    db.session.commit()
    
    print("Database reset complete.")
    print(f"Created admin user: {admin_username}")
    
    # Verify user was created
    user = User.query.filter_by(username=admin_username).first()
    if user:
        print("Admin user verified in database.")
    else:
        print("WARNING: Failed to verify admin user in database!") 