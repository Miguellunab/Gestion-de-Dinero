import os
import secrets
from datetime import timedelta

class Config:
    # Usar una SECRET_KEY de entorno o generar una aleatoria para desarrollo
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # Configuración para SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'finanzas.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
