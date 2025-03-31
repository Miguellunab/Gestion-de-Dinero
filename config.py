import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    SEND_FILE_MAX_AGE_DEFAULT = 0
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://usuario:contraseña@host:puerto/nombre_base'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
