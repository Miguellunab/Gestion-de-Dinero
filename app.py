import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)

# Clave secreta para seguridad (para sesiones, etc.)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')

# Desactivar caché para archivos estáticos (útil en desarrollo)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configuración de la base de datos: si existe DATABASE_URL (Render) se usa esa,
# de lo contrario, se usa el External Database URL.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://gestiondinero_user:sbZYaGViuEdnEOoVl3OuvJgqBaJPOHym@dpg-cvg6fgdumphs73dem04g-a.oregon-postgres.render.com/gestiondinero'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos y el sistema de migraciones
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ---------------------- MODELOS ----------------------

# Modelo para los perfiles (cada usuario tendrá un perfil con nombre y un pin de 4 dígitos)
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Nombre del perfil
    pin = db.Column(db.String(4), nullable=False)  # Pin de 4 dígitos (en texto)
    # Relaciones: cada perfil tiene sus ingresos y gastos
    ingresos = db.relationship('Ingreso', backref='profile', lazy=True)
    gastos = db.relationship('Gasto', backref='profile', lazy=True)

# Modelo para un gasto
class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)  # Se almacena como entero
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)  # Relación con Profile

# Modelo para un ingreso
class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)  # Se almacena como entero
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)  # Relación con Profile

# ---------------------- FILTRO PERSONALIZADO ----------------------

def format_money(value):
    # Formatea el número (ej: 10000 -> "10.000,00")
    s = "{:,.2f}".format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# ---------------------- RUTAS DE PERFILES Y AUTENTICACIÓN ----------------------

# Pantalla de login: muestra los perfiles existentes y opción de crear nuevo perfil.
@app.route('/login')
def login():
    # Si ya hay un perfil en sesión, redirige al dashboard
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    # Consulta todos los perfiles para mostrarlos
    profiles = Profile.query.all()
    return render_template('login.html', profiles=profiles)

# Ruta para seleccionar un perfil y pedir el PIN.
@app.route('/select_profile/<int:profile_id>', methods=['GET', 'POST'])
def select_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if request.method == 'POST':
        # Obtiene el PIN ingresado en el formulario
        pin_input = request.form.get('pin')
        if pin_input == profile.pin:
            # Si el PIN es correcto, guarda el id del perfil en la sesión
            session['profile_id'] = profile.id
            return redirect(url_for('dashboard'))
        else:
            flash("PIN incorrecto. Inténtalo de nuevo.", "danger")
            return redirect(url_for('select_profile', profile_id=profile_id))
    # Renderiza un formulario para ingresar el PIN para el perfil seleccionado
    return render_template('select_profile.html', profile=profile)

# Ruta para crear un nuevo perfil
@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        pin = request.form.get('pin')
        # Validar que el pin tenga 4 dígitos y que el nombre no esté vacío
        if not name or not pin or len(pin) != 4 or not pin.isdigit():
            flash("Por favor, ingresa un nombre y un PIN de 4 dígitos.", "warning")
            return redirect(url_for('create_profile'))
        # Crear el perfil y guardarlo en la base de datos
        new_profile = Profile(name=name, pin=pin)
        db.session.add(new_profile)
        db.session.commit()
        flash("Perfil creado exitosamente.", "success")
        return redirect(url_for('login'))
    return render_template('create_profile.html')

# Ruta para cerrar sesión (salir del perfil actual)
@app.route('/logout')
def logout():
    session.pop('profile_id', None)
    return redirect(url_for('login'))

# ---------------------- RUTAS DE LA APLICACIÓN (GESTIÓN DE DINERO) ----------------------

# Ruta principal: muestra la página de inicio
@app.route('/')
def index():
    # Si no hay perfil en sesión, redirige a la pantalla de login
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    # Consulta los ingresos y gastos del perfil actual
    gastos = Gasto.query.filter_by(profile_id=profile_id).order_by(Gasto.fecha.desc()).all()
    ingresos = Ingreso.query.filter_by(profile_id=profile_id).order_by(Ingreso.fecha.desc()).all()
    
    # Calcula el balance
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    total_gastos = sum(gasto.monto for gasto in gastos)
    balance = total_ingresos - total_gastos
    
    return render_template('index.html', balance=balance, gastos=gastos, ingresos=ingresos)

# Dashboard: muestra la gestion de dinero para el perfil logueado
@app.route('/dashboard')
def dashboard():
    # Si no hay perfil en sesión, redirige a la pantalla de login
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    profile_id = session['profile_id']
    # Consulta los ingresos y gastos del perfil actual, ordenados por fecha descendente
    gastos = Gasto.query.filter_by(profile_id=profile_id).order_by(Gasto.fecha.desc()).all()
    ingresos = Ingreso.query.filter_by(profile_id=profile_id).order_by(Ingreso.fecha.desc()).all()
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    total_gastos = sum(gasto.monto for gasto in gastos)
    balance = total_ingresos - total_gastos
    return render_template('dashboard.html', balance=balance, gastos=gastos, ingresos=ingresos)

# Ruta para agregar un gasto, asociándolo al perfil logueado
@app.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    profile_id = session['profile_id']
    if monto:
        try:
            # Limpia el valor: quita puntos y comas para obtener solo dígitos
            monto_clean = monto.replace(".", "").replace(",", "")
            nuevo_gasto = Gasto(monto=int(monto_clean), descripcion=descripcion, profile_id=profile_id)
            db.session.add(nuevo_gasto)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Error al agregar gasto:", e)
    else:
        print("El campo monto es obligatorio.")
    return redirect(url_for('dashboard'))

# Ruta para agregar un ingreso, asociándolo al perfil logueado
@app.route('/agregar_ingreso', methods=['POST'])
def agregar_ingreso():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    profile_id = session['profile_id']
    if monto:
        try:
            monto_clean = monto.replace(".", "").replace(",", "")
            nuevo_ingreso = Ingreso(monto=int(monto_clean), descripcion=descripcion, profile_id=profile_id)
            db.session.add(nuevo_ingreso)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Error al agregar ingreso:", e)
    else:
        print("El campo monto es obligatorio.")
    return redirect(url_for('dashboard'))

# Ruta para deshacer (eliminar) un movimiento (gasto o ingreso) del perfil actual
@app.route('/deshacer/<tipo>/<int:mov_id>', methods=['POST'])
def deshacer_movimiento(tipo, mov_id):
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    if tipo == 'gasto':
        mov = Gasto.query.filter_by(id=mov_id, profile_id=session['profile_id']).first_or_404()
    elif tipo == 'ingreso':
        mov = Ingreso.query.filter_by(id=mov_id, profile_id=session['profile_id']).first_or_404()
    else:
        return redirect(url_for('dashboard'))
    db.session.delete(mov)
    db.session.commit()
    return redirect(url_for('dashboard'))

# ---------------------- ARRANQUE DE LA APLICACIÓN ----------------------
if __name__ == '__main__':
    # Render inyecta la variable PORT, si no se define se usa 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
