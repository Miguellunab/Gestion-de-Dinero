import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    SEND_FILE_MAX_AGE_DEFAULT = 0
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
         'postgresql://gestiondinero_user:sbZYaGViuEdnEOoVl3OuvJgqBaJPOHym@dpg-cvg6fgdumphs73dem04g-a.oregon-postgres.render.com/gestiondinero'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
