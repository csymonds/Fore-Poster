import os
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    env_file = 'pf.env'
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        print(f"Warning: {env_file} not found")

def get_env_var(var_name: str, default: str = None) -> str:
    """Get environment variable value, with optional default"""
    return os.getenv(var_name, default)

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
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_TOKEN_SECRET',
        'AWS_REGION',
        'SES_SENDER',
        'SES_RECIPIENT',
        'APP_ENV',
        'ADMIN_USERNAME',
        'ADMIN_PASSWORD'
    ]
    
    load_environment()
    
    for var in vars_to_check:
        value = get_env_var(var)
        print(f"{var}: {'Set' if value else 'Not set'}")
        if value:
            print(f"Length: {len(value)}")

if __name__ == "__main__":
    check_env()