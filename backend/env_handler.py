import os
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
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
            print(f"Loaded environment from: {env_path}")
            env_file_found = True
            break

    if not env_file_found:
        print("Warning: .env not found in any of these locations:")
        for loc in possible_locations:
            print(f"  - {os.path.abspath(loc)}")

    # If environment file specified in systemd service, it takes precedence
    if 'ENVIRONMENT_FILE' in os.environ:
        custom_env_path = os.environ['ENVIRONMENT_FILE']
        if os.path.exists(custom_env_path):
            load_dotenv(custom_env_path)
            print(f"Loaded environment from ENVIRONMENT_FILE: {custom_env_path}")
        else:
            print(f"Warning: Environment file specified in ENVIRONMENT_FILE not found: {custom_env_path}")

def get_env_var(var_name: str, default: str = None) -> str:
    """Get environment variable value, with optional default"""
    value = os.getenv(var_name, default)
    if value is None:
        print(f"Warning: Environment variable {var_name} not set")
    return value

def set_env_var(var_name: str, value: str) -> None:
    """Set environment variable value"""
    os.environ[var_name] = value

def check_env():
    """Check status of critical environment variables"""
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
    
    load_environment()
    print("\nEnvironment variables status:")
    
    for var in vars_to_check:
        value = get_env_var(var)
        print(f"{var}: {'Set' if value else 'Not set'}")
        if value:
            print(f"Length: {len(value)}")

if __name__ == "__main__":
    check_env()