from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, Profile, Gasto, Ingreso
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config.from_object(Config)

# Inicializa la base de datos y las migraciones
db.init_app(app)
migrate = Migrate(app, db)

# Tu filtro y rutas aquí...
def format_money(value):
    s = "{:,.2f}".format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# Rutas (login, dashboard, etc.) se mantienen prácticamente igual...
@app.route('/login')
def login():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    profiles = Profile.query.all()
    return render_template('login.html', profiles=profiles)

# ... el resto de tus rutas ...

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
