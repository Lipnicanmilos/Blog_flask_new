import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # SECRET_KEY sa načíta z .env súboru, nikdy nesmie byť natvrdo v kóde
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-me')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///sqlite.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # E-mailové nastavenia - USERNAME aj PASSWORD idú z .env, nikdy nie do repozitára
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    MAX_CONTENT_LENGTH = int(0.5 * 1024 * 1024)  # 0.5 MB limit na upload
    UPLOAD_FOLDER = os.path.join('static', 'profile_pics')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    CKEDITOR_HEIGHT = 500
