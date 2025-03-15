"""
Database Schema Manager

This script provides tools for database schema management:
1. Tracking schema versions
2. Creating tables that don't exist
3. Modifying existing tables when schema changes
4. Working in both development and production environments
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import traceback
from sqlalchemy import text, inspect, MetaData, Table, Column
import sqlalchemy.types as types
from sqlalchemy.exc import OperationalError, ProgrammingError

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("db_update")

# Script usage information
def print_usage():
    print(f"""
Database Schema Manager - Usage:
--------------------------------
python {os.path.basename(__file__)} --development   # Run in development mode
python {os.path.basename(__file__)} --production    # Run in production mode

You must specify either --development or --production to proceed.
This helps prevent accidentally running in the wrong environment.
""")
    sys.exit(1)

# Get environment from command line args
if len(sys.argv) != 2:
    print_usage()
    
if sys.argv[1] == '--production':
    env = 'production'
elif sys.argv[1] == '--development':
    env = 'development'
else:
    print_usage()

logger.info(f"Running in {env} mode")

if env == 'development':
    # Set development environment explicitly for local testing
    os.environ['APP_ENV'] = 'development'

    # Set dummy Twitter API credentials to prevent initialization errors
    os.environ['X_API_KEY'] = 'dummy_key'
    os.environ['X_API_SECRET'] = 'dummy_secret'
    os.environ['X_ACCESS_TOKEN'] = 'dummy_token'
    os.environ['X_ACCESS_TOKEN_SECRET'] = 'dummy_token_secret'

# Add current directory to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    # Load environment variables
    from env_handler import load_environment
    if env == 'development':
        # Look for .env.dev in parent directory (project root) for development
        env_dev_path = os.path.join(Path(__file__).parent.parent, ".env.dev")
        if os.path.exists(env_dev_path):
            logger.info(f"Loading development environment from: {env_dev_path}")
            load_environment(env_dev_path)
        else:
            logger.info("Development environment file (.env.dev) not found, using default .env")
            load_environment()
    else:
        # For production, just use the standard .env file
        logger.info("Loading production environment")
        load_environment()
    
    logger.info(f"Environment loaded. APP_ENV={os.environ.get('APP_ENV', 'Not set')}")
    
    # Now we can safely import the modules
    from fore_poster import app, db, Settings, User, Post
    
    # ---------------------------------------------------------------
    # Schema version - this is the current version of your database schema
    # Increment this when making changes to the database schema
    # ---------------------------------------------------------------
    SCHEMA_VERSION = '1.1'
    
    def get_current_schema_version():
        """Get the current schema version from the database"""
        with app.app_context():
            try:
                version = Settings.get('schema_version')
                return version
            except Exception:
                return None
    
    def set_schema_version(version):
        """Update the schema version in the database"""
        with app.app_context():
            Settings.set('schema_version', version)
            logger.info(f"Schema version updated to {version}")
    
    def get_model_definitions():
        """Get model definitions from SQLAlchemy models"""
        models = {
            'User': User,
            'Post': Post,
            'Settings': Settings
            # Add any new models here
        }
        return models
    
    def compare_model_with_table(model, inspector, table_name):
        """Compare model definition with actual table schema"""
        differences = []
        
        # Get columns from the model
        model_columns = {c.name: c for c in model.__table__.columns}
        
        # Get columns from the database
        db_columns = {c['name']: c for c in inspector.get_columns(table_name)}
        
        # Find columns in model but not in db
        for col_name, col in model_columns.items():
            if col_name not in db_columns:
                differences.append(f"Missing column: {col_name} in table {table_name}")
        
        # Additional checks could be added here (like column type changes)
        
        return differences
    
    def verify_and_update_database():
        """Verify database connection and schema, update tables if needed."""
        success = True
        with app.app_context():
            try:
                # Start a transaction
                db.session.begin_nested()
                
                # Check connection
                logger.info("Checking database connection...")
                result = db.session.execute(text("SELECT 1")).scalar()
                logger.info(f"Database connection successful: {result}")
                
                # Get database inspector
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                logger.info(f"Found tables: {tables}")
                
                # Create schema_migrations table if it doesn't exist
                if 'settings' not in tables:
                    logger.info("Settings table not found, creating all tables...")
                    db.create_all()
                    
                    # Check if tables were created successfully
                    inspector = inspect(db.engine)
                    updated_tables = inspector.get_table_names()
                    logger.info(f"Updated tables: {updated_tables}")
                    
                    if 'settings' in updated_tables:
                        logger.info("Tables created successfully")
                        
                        # Initialize schema version
                        set_schema_version(SCHEMA_VERSION)
                        
                        # Define default settings values
                        DEFAULT_SYSTEM_PROMPT = """You are an AI assistant for helping create social media posts.
Be creative, professional, and adapt to the user's tone and style.
Generate concise, engaging content optimized for social media."""
                        
                        # Initialize with default settings
                        if not Settings.query.filter_by(key='ai_system_prompt').first():
                            Settings.set('ai_system_prompt', DEFAULT_SYSTEM_PROMPT)
                            logger.info("Added default AI system prompt")
                            
                        if not Settings.query.filter_by(key='ai_temperature').first():
                            Settings.set('ai_temperature', 0.7)
                            logger.info("Added default AI temperature")
                            
                        if not Settings.query.filter_by(key='ai_web_search_enabled').first():
                            Settings.set('ai_web_search_enabled', True)
                            logger.info("Added default web search setting")
                    else:
                        logger.error("Failed to create tables")
                        db.session.rollback()
                        return False
                else:
                    # Check for schema updates if the tables already exist
                    current_version = get_current_schema_version()
                    logger.info(f"Current schema version: {current_version}")
                    
                    if current_version is None:
                        logger.info("Setting initial schema version")
                        set_schema_version(SCHEMA_VERSION)
                    elif current_version != SCHEMA_VERSION:
                        logger.info(f"Schema update needed: {current_version} -> {SCHEMA_VERSION}")
                        
                        # Perform specific migrations here
                        apply_migrations(current_version, SCHEMA_VERSION)
                    else:
                        logger.info("Schema is up to date")
                
                # Check all models against database schema
                models = get_model_definitions()
                schema_differences = []
                
                for model_name, model_class in models.items():
                    table_name = model_class.__tablename__
                    if table_name in tables:
                        differences = compare_model_with_table(model_class, inspector, table_name)
                        if differences:
                            schema_differences.extend(differences)
                
                if schema_differences:
                    logger.warning("Schema differences detected:")
                    for diff in schema_differences:
                        logger.warning(f"  - {diff}")
                    
                    logger.info("Attempting to update schema...")
                    apply_schema_differences(schema_differences)
                
                # Commit all changes
                db.session.commit()
                logger.info("Database verification and updates completed successfully")
                return True
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database verification failed: {str(e)}")
                traceback.print_exc()
                return False
    
    def apply_migrations(from_version, to_version):
        """Apply specific migrations based on version change"""
        logger.info(f"Applying migrations from {from_version} to {to_version}")
        
        # Example migration logic
        # if from_version == '1.0' and to_version == '1.1':
        #     add_column_to_posts_table()
        
        # Update schema version after migrations
        set_schema_version(to_version)
    
    def apply_schema_differences(differences):
        """Apply schema changes based on detected differences"""
        try:
            # Most changes require db.create_all() which works for new tables/columns
            # but may not work for altering existing columns
            db.create_all()
            
            # For more complex changes, we'd need custom SQL here
            # Example: Adding a column to an existing table in PostgreSQL
            # if any('Missing column: new_column in table posts' in diff for diff in differences):
            #     sql = "ALTER TABLE posts ADD COLUMN new_column TEXT"
            #     db.session.execute(text(sql))
            
            logger.info("Schema differences applied")
            return True
        except Exception as e:
            logger.error(f"Failed to apply schema differences: {str(e)}")
            traceback.print_exc()
            return False
    
    # Main execution
    if __name__ == "__main__":
        if verify_and_update_database():
            logger.info("✅ Database verification and updates completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Database verification and updates failed")
            sys.exit(1)

except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    traceback.print_exc()
    sys.exit(1) 