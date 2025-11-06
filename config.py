import os
import secrets
from datetime import timedelta
from sqlalchemy.pool import NullPool

def _resolve_database_url():
    """Obtiene la URL de base de datos desde variables comunes en Vercel/Neon.
    Prioriza variantes 'pooled'.
    """
    candidates = [
        'DATABASE_URL',               # nuestra principal
        'POSTGRES_URL',               # Vercel Postgres template
        'STORAGE_URL',                # integración con prefijo por defecto
        'POSTGRES_PRISMA_URL',        # a veces definida por integraciones
        'DATABASE_URL_UNPOOLED',      # alternativas sin pool
        'POSTGRES_URL_NON_POOLING',
    ]
    for key in candidates:
        val = os.environ.get(key)
        if val:
            # Normalizar a driver psycopg2 si es necesario
            if val.startswith('postgres://'):
                val = 'postgresql+psycopg2://' + val[len('postgres://'):]
            elif val.startswith('postgresql://') and 'postgresql+psycopg2://' not in val:
                val = 'postgresql+psycopg2://' + val[len('postgresql://'):]
            return val
    return None


class Config:
    # Usar una SECRET_KEY de entorno o generar una aleatoria para desarrollo
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    SEND_FILE_MAX_AGE_DEFAULT = 0

    # Directorio base
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Elegir la base de datos según entorno
    db_url = _resolve_database_url()
    if db_url:
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
