#!/usr/bin/env python3
"""
Run this script after setting up your .env file.
This will create the database and add a test admin user.
"""
import os
import sys
from pathlib import Path
import logging
import shutil

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("db_reset")

# Add current directory to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Load environment variables from .env file
try:
    from env_handler import load_environment, get_env_var
    
    BASE_DIR = Path(__file__).parent.absolute()
    load_environment()
    logger.info("Environment loaded")
except ImportError as e:
    logger.error(f"Failed to import env_handler: {str(e)}")
    sys.exit(1)

# Determine environment
app_env = get_env_var('APP_ENV', 'development')
is_production = app_env == 'production'
logger.info(f"Application environment: {app_env}")

# Import SQLAlchemy-related modules after environment is loaded
try:
    # Import the flask app with its initialized SQLAlchemy instance
    from fore_poster import app, db, User, robust_password_hash
    from werkzeug.security import generate_password_hash
    from config import Config
    
    logger.info("Successfully imported app modules")
except ImportError as e:
    logger.error(f"Failed to import application modules: {str(e)}")
    logger.error("Make sure you're running this script from the correct directory.")
    sys.exit(1)

# Initialize app configuration to ensure proper database URI
with app.app_context():
    logger.info(f"SQLAlchemy Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

# Get admin credentials
admin_username = get_env_var('ADMIN_USERNAME', 'admin')
admin_password = get_env_var('ADMIN_PASSWORD', 'password')

if not admin_username or not admin_password:
    logger.error("ADMIN_USERNAME and/or ADMIN_PASSWORD not defined in .env file")
    sys.exit(1)

# Determine database type and path
if is_production:
    # For production, we use PostgreSQL
    db_user = get_env_var('DB_USER')
    db_password = get_env_var('DB_PASSWORD')
    db_host = get_env_var('DB_HOST', 'localhost')
    db_port = get_env_var('DB_PORT', '5432')
    db_name = get_env_var('DB_NAME')
    
    if not all([db_user, db_password, db_name]):
        logger.error("Production mode requires DB_USER, DB_PASSWORD, and DB_NAME to be set")
        sys.exit(1)
        
    db_uri = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    logger.info(f"Using PostgreSQL database: {db_name} on {db_host}:{db_port}")
    
    # We won't handle backup for PostgreSQL here - that should be done with pg_dump
    db_path = None
else:
    # For development/testing, use SQLite
    db_path = get_env_var('DB_PATH', None)
    if not db_path:
        db_path = os.path.join(app.instance_path, 'fore_poster.db')
    
    # Ensure the instance directory exists
    instance_dir = os.path.dirname(db_path)
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        logger.info(f"Created instance directory: {instance_dir}")
    
    logger.info(f"Using SQLite database at: {db_path}")
    
    # Backup existing database if it exists
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup.{int(os.path.getmtime(db_path))}"
        logger.info(f"Backing up existing database to: {backup_path}")
        try:
            shutil.copy2(db_path, backup_path)
            # Set secure permissions on the backup
            os.chmod(backup_path, 0o600)
            logger.info("Set permissions 600 on backup file")
        except Exception as e:
            logger.warning(f"Could not backup existing database: {str(e)}")

try:
    with app.app_context():
        # Reset database
        logger.info("Dropping all tables...")
        db.drop_all()
        logger.info("Creating all tables...")
        db.create_all()
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(app.instance_path, 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir, exist_ok=True)
            logger.info(f"Created uploads directory: {uploads_dir}")
        
        # Create admin user with credentials from .env
        logger.info(f"Creating admin user: {admin_username}")
        
        # Use the robust_password_hash function
        password_hash = robust_password_hash(admin_password)
        
        admin_user = User(
            username=admin_username,
            password=password_hash
        )
        db.session.add(admin_user)
        db.session.commit()
        
        logger.info("Database reset complete")
        
        # Verify user was created
        user = User.query.filter_by(username=admin_username).first()
        if user:
            logger.info("Admin user verified in database")
        else:
            logger.error("Failed to verify admin user in database!")
            sys.exit(1)
        
        # Set secure permissions on the database file (for SQLite only)
        if not is_production and db_path and os.path.exists(db_path):
            try:
                os.chmod(db_path, 0o600)
                logger.info("Set secure permissions (600) on database file")
            except Exception as e:
                logger.warning(f"Could not set permissions on database file: {str(e)}")
        
        # On Linux systems, try to set ownership if relevant (for SQLite only)
        if not is_production and db_path and sys.platform == 'linux' and os.path.exists(db_path):
            try:
                # Try to determine the right owner
                current_user = os.environ.get('USER', os.environ.get('LOGNAME', 'cjs'))
                os.system(f"sudo chown {current_user}:{current_user} {db_path}")
                logger.info(f"Set ownership of database file to {current_user}")
            except Exception as e:
                logger.warning(f"Could not set ownership on database file: {str(e)}")
                logger.warning("You may need to manually set proper ownership")
        
        # Show database connection information
        if is_production:
            db_info = f"PostgreSQL database: {db_name} on {db_host}:{db_port}"
        else:
            db_info = f"SQLite database at: {db_path}"
        
        print("\n✅ Database setup successfully completed!")
        print(f"Database: {db_info}")
        print(f"Login with username '{admin_username}' and your configured password")
        
except Exception as e:
    logger.error(f"Error: {str(e)}", exc_info=True)
    sys.exit(1) 