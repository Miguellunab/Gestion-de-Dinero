import os
import secrets
from datetime import timedelta

class Config:
    # Usar una SECRET_KEY de entorno o generar una aleatoria para desarrollo
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # Usar variable de entorno para la URL de base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Si no hay variable de entorno DATABASE_URL
    if not SQLALCHEMY_DATABASE_URI:
        # Generar URI de PostgreSQL desde componentes individuales (más seguro)
        DB_USER = os.environ.get('DB_USER', 'postgres')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = os.environ.get('DB_PORT', '5432')
        DB_NAME = os.environ.get('DB_NAME', 'dinero_dev')
        
        # Construir la URL de conexión
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        
        print("⚠️ ADVERTENCIA: Usando configuración PostgreSQL local para desarrollo.")
    
    # Corregir prefijo para compatibilidad con versiones recientes de SQLAlchemy
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
