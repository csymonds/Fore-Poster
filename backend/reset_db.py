#!/usr/bin/env python3
"""
Run this script after setting up your .env file.
This will create the database and add a test admin user.
"""
import os
import sys
from pathlib import Path
from fore_poster import app, db, User, robust_password_hash
from env_handler import load_environment, get_env_var

# Load environment variables from .env file
BASE_DIR = Path(__file__).parent.absolute()
load_environment()

admin_username = get_env_var('ADMIN_USERNAME', 'admin')
admin_password = get_env_var('ADMIN_PASSWORD', 'password')

db_path = os.path.join(app.instance_path, 'fore_poster.db')
print(f"Database will be created at: {db_path}")

try:
    with app.app_context():
        # Reset database
        db.drop_all()
        db.create_all()
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(app.instance_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Create admin user with credentials from .env
        admin_user = User(
            username=admin_username,
            password=robust_password_hash(admin_password)
        )
        db.session.add(admin_user)
        db.session.commit()
        
        print("✅ Database reset complete.")
        print(f"✅ Created admin user: {admin_username}")
        
        # Verify user was created
        user = User.query.filter_by(username=admin_username).first()
        if user:
            print("✅ Admin user verified in database.")
        else:
            print("❌ WARNING: Failed to verify admin user in database!") 
except Exception as e:
    print(f"❌ Error: {str(e)}") 