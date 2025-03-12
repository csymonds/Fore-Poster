import os
import logging
from dotenv import load_dotenv

# Set up logger
logger = logging.getLogger(__name__)

def load_environment(custom_env_file=None):
    """Load environment variables from .env file
    
    Attempts to load environment variables from multiple possible locations,
    with priority given to a custom file if provided.
    
    Args:
        custom_env_file: Optional path to a specific .env file to use
        
    Raises:
        FileNotFoundError: If no .env file could be found in any location
    """
    # If custom environment file is provided, try to load it first
    logger.info(f"Custom file specified: {custom_env_file}")
    if custom_env_file and os.path.exists(custom_env_file):
        load_dotenv(custom_env_file)
        logger.info(f"Loaded environment from custom file: {custom_env_file}")
        return

    # Try multiple possible locations for the env file
    possible_locations = [
        '.env',  # Current directory
        os.path.join(os.path.dirname(__file__), '.env'),  # Same directory as this script
        os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),  # Project root
        '/etc/fore-poster/.env',  # System config directory
        '/var/www/fore-poster/.env'  # Production application directory
    ]

    env_file_found = False
    for env_path in possible_locations:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Loaded environment from: {env_path}")
            env_file_found = True
            break

    if not env_file_found:
        logger.warning("Warning: .env not found in any of these locations:")
        for loc in possible_locations:
            logger.warning(f"  - {os.path.abspath(loc)}")
        logger.error("No environment file found! Application may not function correctly.")

    # If environment file specified in systemd service, it takes precedence
    if 'ENVIRONMENT_FILE' in os.environ:
        custom_env_path = os.environ['ENVIRONMENT_FILE']
        if os.path.exists(custom_env_path):
            load_dotenv(custom_env_path)
            logger.info(f"Loaded environment from ENVIRONMENT_FILE: {custom_env_path}")
        else:
            logger.warning(f"Warning: Environment file specified in ENVIRONMENT_FILE not found: {custom_env_path}")

def get_env_var(var_name: str, default: str = None) -> str:
    """Get environment variable value, with optional default
    
    Args:
        var_name: Name of the environment variable to retrieve
        default: Optional default value if the variable is not set
        
    Returns:
        The environment variable value or the default
        
    Raises:
        EnvironmentError: If the variable is critical (no default provided) and not found
    """
    value = os.getenv(var_name, default)
    if value is None:
        logger.error(f"Critical environment variable {var_name} not set")
        # Raise error for critical variables (those without defaults)
        if default is None:
            raise EnvironmentError(f"Required environment variable '{var_name}' is not set")
    return value

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