import os
from env_handler import get_env_var

class Config:
    TESTING = False
    DEVELOPMENT = True
    PRODUCTION = False
    
    @classmethod
    def init_app(cls, env='development'):
        cls.TESTING = env == 'testing'
        cls.DEVELOPMENT = env == 'development'
        cls.PRODUCTION = env == 'production'
            
        # Common configs
        cls.JWT_SECRET = get_env_var('JWT_SECRET')
        
        # Database configurations
        db_user = get_env_var('DB_USER')
        db_password = get_env_var('DB_PASSWORD')
        db_host = get_env_var('DB_HOST', 'localhost')
        db_port = get_env_var('DB_PORT', '5432')
        db_name = get_env_var('DB_NAME')
        
        if cls.PRODUCTION:
            cls.SQLALCHEMY_DATABASE_URI = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        else:
            # Default to SQLite for non-production
            cls.SQLALCHEMY_DATABASE_URI = 'sqlite:///fore_poster.db'
        
        # X API configs
        cls.X_API_KEY = get_env_var('X_API_KEY')
        cls.X_API_SECRET = get_env_var('X_API_SECRET')
        cls.X_ACCESS_TOKEN = get_env_var('X_ACCESS_TOKEN')
        cls.X_ACCESS_TOKEN_SECRET = get_env_var('X_ACCESS_TOKEN_SECRET')
        
        # AWS configs for production
        if cls.PRODUCTION:
            cls.AWS_REGION = get_env_var('AWS_REGION', 'us-east-1')
            cls.SES_SENDER = get_env_var('SES_SENDER')
            cls.SES_RECIPIENT = get_env_var('SES_RECIPIENT')
        
        print("Env:", env)
        if cls.PRODUCTION:
            print("PRODUCTION:", cls.PRODUCTION)
            print("DATABASE_URL:", cls.SQLALCHEMY_DATABASE_URI)