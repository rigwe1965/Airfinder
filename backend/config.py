import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    IS_DEV = os.getenv('FLASK_ENV') == 'development'
    SECRET_KEY = os.getenv('SECRET_KEY') or ('dev-secret-key' if IS_DEV else None)
    JWT_SECRET = os.getenv('JWT_SECRET') or ('dev-jwt-secret' if IS_DEV else None)
    PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', 'http://localhost:5000').rstrip('/')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///airfinder.db').replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'Airfinder <noreply@airfinder.com>')

    MARKUP_PERCENT = float(os.getenv('DEFAULT_MARKUP_PERCENT', 8))
    SERVICE_FEE_USD = float(os.getenv('DEFAULT_SERVICE_FEE_USD', 15))
    COMMISSION_PERCENT = float(os.getenv('DEFAULT_COMMISSION_PERCENT', 3))

    SUPER_ADMIN_EMAIL = os.getenv('SUPER_ADMIN_EMAIL')
    SUPER_ADMIN_PASSWORD = os.getenv('SUPER_ADMIN_PASSWORD')
    MAX_CONTENT_LENGTH = 64 * 1024
    # Require a server-signed fare quote on booking (set QUOTE_ENFORCE=false only as an emergency switch)
    QUOTE_ENFORCE = os.getenv('QUOTE_ENFORCE', 'true').lower() != 'false'

    PORT = int(os.getenv('PORT', 5000))
