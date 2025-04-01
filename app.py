from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, Profile, Gasto, Ingreso
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config.from_object(Config)

# Actualizar configuración para SQLite local
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'sqlite:///instance/finanzas.db'
)

# Inicializa la base de datos y las migraciones
db.init_app(app)
migrate = Migrate(app, db)

# Filtro para formatear dinero
def format_money(value):
    s = "{:,.0f}".format(value)  # Cambiado a 0 decimales para enteros
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# Ruta raíz - redirige según la sesión
@app.route('/')
def index():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Ruta de login
@app.route('/login')
def login():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    profiles = Profile.query.all()
    return render_template('login.html', profiles=profiles)

# Ruta para seleccionar un perfil
@app.route('/profile/<int:profile_id>', methods=['GET', 'POST'])
def select_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    
    if request.method == 'POST':
        pin = request.form.get('pin')
        if pin == profile.pin:
            session['profile_id'] = profile.id
            session['profile_name'] = profile.name
            session.permanent = True
            return redirect(url_for('dashboard'))
        else:
            flash('PIN incorrecto', 'danger')
    
    return render_template('select_profile.html', profile=profile)

# Ruta para crear un perfil
@app.route('/profile/create', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        pin = request.form.get('pin')
        
        if len(pin) != 4 or not pin.isdigit():
            flash('El PIN debe tener exactamente 4 dígitos', 'danger')
        else:
            new_profile = Profile(name=name, pin=pin)
            db.session.add(new_profile)
            db.session.commit()
            flash(f'Perfil "{name}" creado con éxito', 'success')
            return redirect(url_for('login'))
    
    return render_template('create_profile.html')

# Dashboard principal
@app.route('/dashboard')
def dashboard():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    profile = Profile.query.get_or_404(profile_id)
    
    gastos = Gasto.query.filter_by(profile_id=profile_id).order_by(Gasto.fecha.desc()).all()
    ingresos = Ingreso.query.filter_by(profile_id=profile_id).order_by(Ingreso.fecha.desc()).all()
    
    total_gastos = sum(gasto.monto for gasto in gastos)
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    balance = total_ingresos - total_gastos
    
    return render_template('index.html', 
                           profile=profile,
                           gastos=gastos, 
                           ingresos=ingresos, 
                           balance=balance)

# Ruta para agregar un gasto
@app.route('/gasto/add', methods=['POST'])
def agregar_gasto():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    monto = request.form.get('monto', '0')
    monto = monto.replace('.', '')  # Quitar puntos de separadores de miles
    descripcion = request.form.get('descripcion', '')
    
    try:
        monto = int(monto)
    except ValueError:
        flash('El monto debe ser un número válido', 'danger')
        return redirect(url_for('dashboard'))
    
    gasto = Gasto(
        monto=monto,
        descripcion=descripcion,
        profile_id=session['profile_id']
    )
    
    db.session.add(gasto)
    db.session.commit()
    flash('Gasto registrado correctamente', 'success')
    return redirect(url_for('dashboard'))

# Ruta para agregar un ingreso
@app.route('/ingreso/add', methods=['POST'])
def agregar_ingreso():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    monto = request.form.get('monto', '0')
    monto = monto.replace('.', '')  # Quitar puntos de separadores de miles
    descripcion = request.form.get('descripcion', '')
    
    try:
        monto = int(monto)
    except ValueError:
        flash('El monto debe ser un número válido', 'danger')
        return redirect(url_for('dashboard'))
    
    ingreso = Ingreso(
        monto=monto,
        descripcion=descripcion,
        profile_id=session['profile_id']
    )
    
    db.session.add(ingreso)
    db.session.commit()
    flash('Ingreso registrado correctamente', 'success')
    return redirect(url_for('dashboard'))

# Ruta para eliminar un movimiento
@app.route('/deshacer/<tipo>/<int:mov_id>', methods=['POST'])
def deshacer_movimiento(tipo, mov_id):
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    if tipo == 'gasto':
        movimiento = Gasto.query.get_or_404(mov_id)
    else:
        movimiento = Ingreso.query.get_or_404(mov_id)
    
    # Verificar que el movimiento pertenezca al perfil actual
    if movimiento.profile_id != session['profile_id']:
        flash('No tienes permiso para eliminar este movimiento', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(movimiento)
    db.session.commit()
    flash('Movimiento eliminado correctamente', 'success')
    return redirect(url_for('dashboard'))

# Ruta para editar un perfil
@app.route('/profile/<int:profile_id>/edit', methods=['POST'])
def edit_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    
    name = request.form.get('name')
    profile.name = name
    
    db.session.commit()
    flash('Perfil actualizado correctamente', 'success')
    return redirect(url_for('login'))

# Ruta para eliminar un perfil
@app.route('/profile/<int:profile_id>/delete', methods=['POST'])
def delete_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    
    # Eliminar primero los gastos e ingresos asociados
    Gasto.query.filter_by(profile_id=profile_id).delete()
    Ingreso.query.filter_by(profile_id=profile_id).delete()
    
    db.session.delete(profile)
    db.session.commit()
    flash('Perfil eliminado correctamente', 'success')
    return redirect(url_for('login'))

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Inicialización de la base de datos para desarrollo
@app.before_first_request
def create_tables_and_default_data():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
