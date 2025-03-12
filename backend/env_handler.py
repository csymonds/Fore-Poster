import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

def load_environment(custom_env_file=None):
    """Load environment variables from .env files.
    
    This function attempts to load environment variables from a custom file if provided,
    or falls back to standard locations. It also ensures essential environment variables
    are set with defaults.
    
    Args:
        custom_env_file: Optional path to a custom .env file
        
    Returns:
        dict: A dictionary containing the loaded environment variables
    """
    # First, try to load from custom file if provided
    if custom_env_file and os.path.isfile(custom_env_file):
        logger.info(f"Loading environment from custom file: {custom_env_file}")
        load_dotenv(custom_env_file)
    # Otherwise check ENVIRONMENT_FILE var
    elif os.getenv('ENVIRONMENT_FILE') and os.path.isfile(os.getenv('ENVIRONMENT_FILE')):
        env_file = os.getenv('ENVIRONMENT_FILE')
        logger.info(f"Loading environment from ENVIRONMENT_FILE: {env_file}")
        load_dotenv(env_file)
    # Otherwise check for APP_ENV to determine which .env file to load
    else:
        # Get app environment or default to development
        app_env = os.environ.get('APP_ENV', 'development')
        logger.info(f"APP_ENV is set to: {app_env}")
        
        # Determine environment file paths
        base_path = Path(os.path.dirname(os.path.abspath(__file__)))  # Get backend directory
        env_files = [
            base_path / f".env.{app_env}",  # First check for environment-specific file
            base_path / ".env",             # Then check for default .env file
            Path(f".env.{app_env}"),        # Check current directory for environment-specific file
            Path(".env")                    # Check current directory for default .env file
        ]
        
        # Try to load each env file in order until one is found
        for env_file in env_files:
            if env_file.is_file():
                logger.info(f"Loading environment from: {env_file}")
                load_dotenv(env_file)
                break
        else:
            logger.warning("No .env file found. Using system environment variables only.")
    
    # Set default values for essential variables if not already set
    set_default_env('APP_ENV', 'development')
    set_default_env('FLASK_ENV', os.getenv('APP_ENV', 'development'))
    set_default_env('INSTANCE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'))
    
    # Debug environment post-load
    app_env = os.getenv('APP_ENV')
    logger.info(f"Environment loaded. APP_ENV={app_env}")

    # Return the environment variables as a dictionary
    return dict(os.environ)

def set_default_env(key, default_value):
    """Set default environment variable if not already set.
    
    Args:
        key: The environment variable name
        default_value: The default value to set if not already set
    """
    if key not in os.environ:
        os.environ[key] = default_value
        logger.debug(f"Set default environment variable: {key}={default_value}")

def get_env_var(name, default=None):
    """Get an environment variable, with a default value.
    
    Args:
        name: The environment variable name
        default: The default value to return if the environment variable is not set
        
    Returns:
        The environment variable value, or the default if not set
    """
    return os.environ.get(name, default)

def safe_get_int(name, default=0, min_value=None, max_value=None):
    """Safely get an integer from environment variables, handling comments and validation.
    
    Args:
        name: The environment variable name
        default: Default value if the variable is not set or invalid
        min_value: Optional minimum allowed value
        max_value: Optional maximum allowed value
        
    Returns:
        int: The parsed and validated integer value
    """
    try:
        # Get the raw value, default to empty string if not found
        raw_value = os.environ.get(name, '')
        
        # If empty, return the default
        if not raw_value:
            return default
            
        # Clean the value by removing any comments (text after #)
        # and strip whitespace
        clean_value = raw_value.split('#')[0].strip()
        
        # Convert to integer
        result = int(clean_value)
        
        # Apply range constraints if provided
        if min_value is not None and result < min_value:
            logger.warning(f"Value for {name} ({result}) is below minimum ({min_value}). Using minimum value.")
            result = min_value
            
        if max_value is not None and result > max_value:
            logger.warning(f"Value for {name} ({result}) is above maximum ({max_value}). Using maximum value.")
            result = max_value
            
        return result
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing {name} as integer: {str(e)}. Using default value ({default}).")
        return default

def set_env_var(var_name: str, value: str) -> None:
    """Set environment variable value
    
    Args:
        var_name: Name of the environment variable to set
        value: Value to assign to the environment variable
    """
    os.environ[var_name] = value
    logger.debug(f"Set environment variable: {var_name}")

# Define sensitive variables that shouldn't have their values displayed
SENSITIVE_VARS = {
    'JWT_SECRET', 'DB_PASSWORD', 'X_API_KEY', 'X_API_SECRET', 
    'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'ADMIN_PASSWORD'
}

def check_env():
    """Check status of critical environment variables
    
    Verifies that all required environment variables are set.
    For security, the actual values of sensitive variables are not displayed.
    """
    vars_to_check = [
        'JWT_SECRET',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'DB_PORT',
        'DB_HOST',
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_TOKEN_SECRET',
        'AWS_REGION',
        'SES_SENDER',
        'SES_RECIPIENT',
        'ADMIN_USERNAME',
        'ADMIN_PASSWORD',
        'APP_ENV'
    ]
    
    # Set up console logging for this function
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        load_environment()
        logger.info("\nEnvironment variables status:")
        
        missing_critical_vars = []
        
        for var in vars_to_check:
            try:
                value = get_env_var(var)
                if var in SENSITIVE_VARS:
                    logger.info(f"{var}: Set [value hidden]")
                else:
                    logger.info(f"{var}: Set")
            except EnvironmentError:
                missing_critical_vars.append(var)
                logger.error(f"{var}: NOT SET - THIS IS REQUIRED")
        
        if missing_critical_vars:
            logger.error(f"Missing critical environment variables: {', '.join(missing_critical_vars)}")
            logger.error("Please set these variables in your .env file before proceeding.")
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking environment: {str(e)}")
        return False

if __name__ == "__main__":
    check_env()