from datetime import datetime
import os


def _in_docker() -> bool:
    return os.path.exists('/.dockerenv')


def _db_host() -> str:
    host = os.getenv('DB_HOST') or '127.0.0.1'
    if host == 'mysql' and not _in_docker():
        return '127.0.0.1'
    return host


def _db_uri() -> str:
    return (
        f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
        f"@{_db_host()}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
    )

class Config:
    """Base configuration."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    DEBUG = False
    APPLICATION_ROOT = "/"

class ProdConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = 'ERROR'
    ENV = "prod"
    
    
class DevConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = 'DEBUG'
    ENV = "dev"
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
   