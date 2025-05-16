from datetime import datetime
import os

class Config:
    """Base configuration."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DEBUG = False
    APPLICATION_ROOT = "/"

class ProdConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///prod.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = 'ERROR'
    ENV = "prod"
    
    
class DevConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = 'DEBUG'
    ENV = "dev"
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
   