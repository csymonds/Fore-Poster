#!/usr/bin/env python3
"""
Database reset and initialization utility for Fore-Poster.

Run this script after setting up your .env file.
This will create the database and add an admin user.

Usage:
    python reset_db.py [--force] [--env-file ENV_FILE_PATH]
    
Arguments:
    --force                   Skip confirmation prompt (use with caution)
    --env-file PATH           Path to a custom .env file
"""
import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
import logging
import shutil

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("db_reset")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Reset and initialize the Fore-Poster database")
    parser.add_argument('--force', action='store_true', 
                        help='Force reset without confirmation (use with caution)')
    parser.add_argument('--env-file', dest='env_file', type=str,
                        help='Path to a custom .env file to use')
    # For backward compatibility, keep the positional argument
    parser.add_argument('env_file_pos', nargs='?', default=None, 
                        help='(Deprecated) Path to a custom .env file to use')
    return parser.parse_args()

# Add current directory to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Set development environment explicitly
os.environ['APP_ENV'] = 'development'
logger.info("Setting APP_ENV to development for database reset")

# Load environment variables from .env file
try:
    from env_handler import load_environment, get_env_var
    
    BASE_DIR = Path(__file__).parent.absolute()
    args = parse_arguments()
    
    # Prioritize named argument, fall back to positional if needed
    env_file_path = args.env_file or args.env_file_pos
    
    # Load environment from custom file if provided
    if env_file_path:
        if os.path.exists(env_file_path):
            logger.info(f"Loading environment from custom file: {env_file_path}")
            load_environment(env_file_path)
        else:
            logger.warning(f"Custom environment file not found: {env_file_path}")
            # Look for .env.dev in parent directory (project root)
            env_dev_path = os.path.join(BASE_DIR.parent, ".env.dev")
            if os.path.exists(env_dev_path):
                logger.info(f"Loading development environment from: {env_dev_path}")
                load_environment(env_dev_path)
            else:
                # Try local .env
                logger.warning("Falling back to default .env file")
                load_environment()
    else:
        # Look for .env.dev in parent directory (project root)
        env_dev_path = os.path.join(BASE_DIR.parent, ".env.dev")
        if os.path.exists(env_dev_path):
            logger.info(f"Loading development environment from: {env_dev_path}")
            load_environment(env_dev_path)
        else:
            logger.info("No custom environment file specified, using default .env")
            load_environment()
        
    logger.info(f"Environment loaded. APP_ENV={os.environ.get('APP_ENV', 'Not set')}")
except ImportError as e:
    logger.error(f"Failed to import env_handler: {str(e)}")
    sys.exit(1)

def backup_database(db_path):
    """
    Create a backup of the existing database file.
    
    Args:
        db_path: Path to the database file
    
    Returns:
        str: Path to the backup file or None if backup failed
    """
    if not os.path.exists(db_path):
        logger.info("No existing database to backup.")
        return None
        
    backup_path = f"{db_path}.backup.{int(os.path.getmtime(db_path))}"
    logger.info(f"Backing up existing database to: {backup_path}")
    
    try:
        shutil.copy2(db_path, backup_path)
        # Set secure permissions on the backup
        os.chmod(backup_path, 0o600)
        logger.info("Set permissions 600 on backup file")
        return backup_path
    except Exception as e:
        logger.warning(f"Could not backup existing database: {str(e)}")
        return None

def set_file_ownership(file_path, user=None):
    """
    Set file ownership using subprocess instead of os.system for better security.
    
    Args:
        file_path: Path to the file
        user: User to set as owner (default: current user)
    """
    if not sys.platform == 'linux' or not os.path.exists(file_path):
        return
        
    try:
        # Determine the right owner
        if user is None:
            user = os.environ.get('USER', os.environ.get('LOGNAME', 'www-data'))
        
        # Use subprocess.run with explicit argument list instead of shell=True
        logger.info(f"Setting ownership of {file_path} to {user}")
        result = subprocess.run(
            ["sudo", "chown", f"{user}:{user}", file_path],
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        
        if result.returncode != 0:
            logger.warning(f"Could not set ownership: {result.stderr}")
        else:
            logger.info(f"Set ownership of {file_path} to {user}")
    except Exception as e:
        logger.warning(f"Could not set ownership on file: {str(e)}")
        logger.warning("You may need to manually set proper ownership")

def ensure_directory_exists(directory_path):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory to ensure exists
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    # If directory_path is empty or just whitespace, return False
    if not directory_path or not directory_path.strip():
        logger.error("Cannot create directory: empty path provided")
        return False
        
    logger.info(f"Ensuring directory exists: {directory_path}")
    
    if os.path.exists(directory_path):
        if os.path.isdir(directory_path):
            logger.info(f"Directory already exists: {directory_path}")
            return True
        else:
            logger.error(f"Path exists but is not a directory: {directory_path}")
            return False
    
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.info(f"Successfully created directory: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {str(e)}")
        return False

def is_valid_path(path):
    """
    Check if a path is valid and not a comment or instruction.
    
    Args:
        path: The path to validate
        
    Returns:
        bool: True if the path seems valid
    """
    if not path:
        return False
        
    # Check for common comment indicators
    if path.strip().startswith(('#', '//', '/*', '*', ';')):
        return False
        
    # Check if it has basic path structure (not starting with invalid characters)
    if re.match(r'^[a-zA-Z0-9_\-./~]+$', path.strip()):
        return True
        
    # If it contains spaces or other characters, it might be a comment
    if ' ' in path and not os.path.exists(path):
        return False
        
    return True

def main():
    # Use global args parsed at startup
    global args
    
    # Get environment settings
    app_env = os.environ.get('APP_ENV', 'development')
    is_production = app_env == 'production'
    logger.info(f"Application environment: {app_env}")
    logger.info(f"Is production mode: {is_production}")
    
    # Confirm reset if not using --force flag
    if not args.force:
        confirm = input(f"\nWARNING: This will reset the {app_env} database and delete all existing data!\nType 'RESET' to confirm: ")
        if confirm != "RESET":
            logger.info("Database reset cancelled.")
            return
    
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
    
    # Log admin username but NEVER log the password
    logger.info(f"Using admin username: {admin_username}")
    
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
        db_path_from_env = get_env_var('DB_PATH', None)
        
        # Log app instance path to help debugging
        logger.info(f"Flask app.instance_path: {app.instance_path}")
        
        # Check if DB_PATH is valid and not a comment
        if db_path_from_env and is_valid_path(db_path_from_env):
            db_path = db_path_from_env
            logger.info(f"Using environment-specified SQLite database path: {db_path}")
        else:
            # Make sure instance_path is absolute
            if db_path_from_env:
                logger.warning(f"Ignoring invalid DB_PATH value: '{db_path_from_env}' - using default")
            
            if not os.path.isabs(app.instance_path):
                abs_instance_path = os.path.abspath(app.instance_path)
                logger.info(f"Converting relative instance path to absolute: {abs_instance_path}")
            else:
                abs_instance_path = app.instance_path
                
            db_path = os.path.join(abs_instance_path, 'fore_poster.db')
            logger.info(f"Using default SQLite database path: {db_path}")
        
        # Get the instance directory and make sure it exists
        instance_dir = os.path.dirname(db_path)
        logger.info(f"Database directory path: {instance_dir}")
        
        # Create the instance directory if it doesn't exist
        if not ensure_directory_exists(instance_dir):
            logger.error("Failed to create instance directory, cannot proceed")
            sys.exit(1)
            
        # Double check the directory exists
        if not os.path.exists(instance_dir):
            logger.error(f"Instance directory does not exist after creation attempt: {instance_dir}")
            sys.exit(1)
            
        logger.info(f"Instance directory exists and is ready: {instance_dir}")
        logger.info(f"Using SQLite database at: {db_path}")
        
        # Backup existing database if it exists
        backup_path = backup_database(db_path)
    
    try:
        with app.app_context():
            # Reset database
            logger.info("Dropping all tables...")
            db.drop_all()
            logger.info("Creating all tables...")
            db.create_all()
            
            # Verify the database file was created
            if not is_production:
                if os.path.exists(db_path):
                    logger.info(f"Verified database file was created: {db_path}")
                    file_size = os.path.getsize(db_path)
                    logger.info(f"Database file size: {file_size} bytes")
                else:
                    logger.warning(f"Database file was not created at expected path: {db_path}")
                    # Try to determine why
                    logger.info(f"Current working directory: {os.getcwd()}")
                    logger.info(f"Is instance directory writable? {os.access(instance_dir, os.W_OK)}")
            
            # Create uploads directory if it doesn't exist
            upload_folder = get_env_var('UPLOAD_FOLDER', 'instance/uploads')
            uploads_dir = os.path.join(app.instance_path, upload_folder.replace('instance/', ''))
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
            
            # On Linux systems, set ownership if needed (for SQLite only)
            if not is_production and db_path and os.path.exists(db_path):
                set_file_ownership(db_path)
            
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
        
        # Attempt to restore from backup if we have one
        if not is_production and db_path and backup_path and os.path.exists(backup_path):
            logger.info("Attempting to restore from backup...")
            try:
                shutil.copy2(backup_path, db_path)
                logger.info("Database restored from backup")
            except Exception as restore_error:
                logger.error(f"Failed to restore from backup: {str(restore_error)}")
        
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
        print("\nOperation completed successfully!")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1) 