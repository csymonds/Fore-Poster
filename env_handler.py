import os
import subprocess
import platform

def check_env():
    vars_to_check = [
        'JWT_SECRET',
        'DATABASE_URL',
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_TOKEN_SECRET',
        'AWS_REGION',
        'SES_SENDER',
        'SES_RECIPIENT'
    ]
    
    for var in vars_to_check:
        value = get_env_var(var)
        print(f"{var}: {'Set' if value else 'Not set'}")
        if value:
            print(f"Length: {len(value)}")

def get_env_var(var_name: str, default: str = None) -> str:
    if platform.system() == 'Windows':
        cmd = f'powershell -Command "[Environment]::GetEnvironmentVariable(\'{var_name}\', \'User\')"'
        result = subprocess.run(cmd, capture_output=True, text=True)
        value = result.stdout.strip()
    else:
        value = os.getenv(var_name)
    
    return value if value else default

def set_env_var(var_name: str, value: str) -> None:
    if platform.system() == 'Windows':
        cmd = f'powershell -Command "[Environment]::SetEnvironmentVariable(\'{var_name}\', \'{value}\', \'User\')"'
        subprocess.run(cmd, capture_output=True)
    else:
        os.environ[var_name] = value

if __name__ == "__main__":
    check_env()