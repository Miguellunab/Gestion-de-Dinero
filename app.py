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

# Filtro para formatear montos
def format_money(value):
    s = "{:,.2f}".format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# Ruta raíz: redirige según la sesión
@app.route('/')
def index():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# Ruta de login: muestra todos los perfiles
@app.route('/login')
def login():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    profiles = Profile.query.all()
    return render_template('login.html', profiles=profiles)

# Ruta para el dashboard
@app.route('/dashboard')
def dashboard():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    profile_id = session['profile_id']
    profile = Profile.query.get(profile_id)
    if not profile:
        flash("Perfil no encontrado. Por favor, inicie sesión de nuevo.", "warning")
        return redirect(url_for('login'))
    
    # Consultar gastos e ingresos y calcular balance
    gastos = Gasto.query.filter_by(profile_id=profile_id).order_by(Gasto.fecha.desc()).all()
    ingresos = Ingreso.query.filter_by(profile_id=profile_id).order_by(Ingreso.fecha.desc()).all()
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    total_gastos = sum(gasto.monto for gasto in gastos)
    balance = total_ingresos - total_gastos
    
    return render_template('dashboard.html', balance=balance, gastos=gastos, ingresos=ingresos, profile=profile)

# Ruta para seleccionar perfil y validar PIN
@app.route('/select_profile/<int:profile_id>', methods=['GET', 'POST'])
def select_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if request.method == 'POST':
        pin_input = request.form.get('pin')
        if pin_input == profile.pin:
            session.permanent = True
            session['profile_id'] = profile.id
            session['last_activity'] = datetime.utcnow().isoformat()
            return redirect(url_for('dashboard'))
        else:
            flash("PIN incorrecto. Inténtalo de nuevo.", "danger")
            return redirect(url_for('select_profile', profile_id=profile_id))
    return render_template('select_profile.html', profile=profile)

# Ruta para crear un nuevo perfil
@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        pin = request.form.get('pin')
        if not name or not pin or len(pin) != 4 or not pin.isdigit():
            flash("Por favor, ingresa un nombre y un PIN de 4 dígitos.", "warning")
            return redirect(url_for('create_profile'))
        new_profile = Profile(name=name, pin=pin)
        db.session.add(new_profile)
        db.session.commit()
        flash("Perfil creado exitosamente.", "success")
        return redirect(url_for('login'))
    return render_template('create_profile.html')

# Ruta para editar perfil
@app.route('/edit_profile/<int:profile_id>', methods=['POST'])
def edit_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    new_name = request.form.get('name')
    if new_name and len(new_name) <= 50:
        profile.name = new_name
        db.session.commit()
        flash("Perfil actualizado correctamente", "success")
    else:
        flash("Nombre inválido. Debe tener entre 1 y 50 caracteres.", "danger")
    return redirect(url_for('login'))

# Nueva ruta para eliminar perfil
@app.route('/delete_profile/<int:profile_id>', methods=['POST'])
def delete_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    # Si existen datos relacionados (ingresos, gastos) y no tienes configuración de cascada, elimínalos manualmente:
    # Gasto.query.filter_by(profile_id=profile_id).delete()
    # Ingreso.query.filter_by(profile_id=profile_id).delete()
    db.session.delete(profile)
    db.session.commit()
    flash("Perfil eliminado correctamente.", "success")
    return redirect(url_for('login'))

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('profile_id', None)
    return redirect(url_for('login'))

# Middleware para controlar el tiempo de inactividad en la sesión
@app.before_request
def check_session_timeout():
    if 'profile_id' in session:
        session.permanent = True
        if 'last_activity' in session:
            now = datetime.utcnow()
            try:
                from dateutil import parser
                last = parser.parse(session['last_activity'])
                if (now - last).total_seconds() > 15 * 60:
                    session.clear()
                    flash("Tu sesión ha expirado por inactividad.", "info")
                    return redirect(url_for('login'))
            except Exception as e:
                print(f"Error al procesar timestamp: {e}")
        session['last_activity'] = datetime.utcnow().isoformat()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)