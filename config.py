import os
import secrets
from datetime import timedelta
from sqlalchemy.pool import NullPool

class Config:
    # Usar una SECRET_KEY de entorno o generar una aleatoria para desarrollo
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    SEND_FILE_MAX_AGE_DEFAULT = 0

    # Directorio base
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Elegir la base de datos según entorno
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Compatibilidad: convertir postgres:// a postgresql+psycopg2://
        if db_url.startswith('postgres://'):
            db_url = 'postgresql+psycopg2://' + db_url[len('postgres://'):]
        SQLALCHEMY_DATABASE_URI = db_url
        # Recomendado en serverless: sin pool de conexiones persistente
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'poolclass': NullPool
        }
    else:
        # En Vercel sin DB externa, usar SQLite en /tmp (no persistente)
        if os.environ.get('VERCEL'):
            SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/finanzas.db'
        else:
            # Desarrollo local: SQLite en carpeta instance
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'finanzas.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
