"""
Configuration file for the Flask application
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # API Keys
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    # Model configurations
    SUMMARIZATION_MODEL = "llama-3.1-8b-instant"
    IMAGE_MODEL = "gemini-2.5-flash"
    QA_MODEL = "gemini-2.5-flash"
    EMBEDDING_MODEL = "models/gemini-embedding-001"


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
