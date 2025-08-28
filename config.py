import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for production deployment"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # KiteConnect API Configuration
    KITE_API_KEY = os.environ.get('KITE_API_KEY') or 'tmp23p1tsmywqb5s'
    KITE_API_SECRET = os.environ.get('KITE_API_SECRET') or 'd1lkd7orpowxrdm4ff6l4fnctp0cjmh9'
    KITE_ACCESS_TOKEN = os.environ.get('KITE_ACCESS_TOKEN') or 'kX69S2Ny9K7QBBNAWO3AinX3rwB0YMYR'
    
    # MongoDB Configuration
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb+srv://hello:Hello123@option-chain.15yln1l.mongodb.net/?retryWrites=true&w=majority&appName=Option-chain'
    
    # SMTP Configuration
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = os.environ.get('SMTP_USER') or 'hellopythonhere@gmail.com'
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') or 'uhex ufof seya lxuz'
    
    # Environment
    ENVIRONMENT = os.environ.get('ENVIRONMENT') or 'development'
    
    # Debug mode (False for production)
    DEBUG = ENVIRONMENT != 'production'
    
    # Port configuration for Render
    PORT = int(os.environ.get('PORT', 5000))
    
    # KiteConnect Redirect URL (environment-based)
    KITE_REDIRECT_URL = os.environ.get('KITE_REDIRECT_URL') or 'http://localhost:5000/kite/callback'
