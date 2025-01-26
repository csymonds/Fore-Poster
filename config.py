import os
from env_handler import get_env_var

class Config:
    TESTING = False
    DEVELOPMENT = True
    PRODUCTION = False
    
    @classmethod
    def init_app(cls, env='development'):
        if env == 'testing':
            cls.TESTING = True
        elif env == 'development':
            cls.DEVELOPMENT = True
        elif env == 'production':
            cls.PRODUCTION = True
            
        # Common configs
        cls.JWT_SECRET = get_env_var('JWT_SECRET')
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
            cls.SQLALCHEMY_DATABASE_URI = get_env_var('DATABASE_URL')