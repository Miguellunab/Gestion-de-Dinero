import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

# ---------------------- CONFIGURACIÓN INICIAL ----------------------

# Crea la aplicación Flask
app = Flask(__name__)

# Configura la clave secreta para la seguridad de las sesiones.
# Se puede establecer mediante una variable de entorno o, si no, se usa 'super-secret-key'.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')
# Desactiva el caché para archivos estáticos (útil durante el desarrollo)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configuración de la base de datos:
# Si existe la variable DATABASE_URL (por ejemplo, en Render), se usa esa URL.
# En caso contrario, se utiliza una URL externa de PostgreSQL (para desarrollo local).
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://gestiondinero_user:sbZYaGViuEdnEOoVl3OuvJgqBaJPOHym@dpg-cvg6fgdumphs73dem04g-a.oregon-postgres.render.com/gestiondinero'
)
# Desactiva el seguimiento de modificaciones (ahorra memoria)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa SQLAlchemy para manejar la base de datos y Flask-Migrate para migraciones.
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ---------------------- FILTRO PERSONALIZADO ----------------------
# Esta función formatea un número a un estilo monetario (por ejemplo, 10000 se muestra como "10.000,00")
def format_money(value):
    s = "{:,.2f}".format(value)  # Formatea con dos decimales (ej: "10,000.00")
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")  # Cambia el formato a estilo español
    return s

# Registra el filtro para que se pueda usar en las plantillas con el nombre "format_money"
app.jinja_env.filters['format_money'] = format_money

# ---------------------- MODELOS (TABLAS DE LA BASE DE DATOS) ----------------------

# Modelo para el Perfil del usuario.
# Cada perfil tiene un nombre y un PIN de 4 dígitos. Además, se relaciona con ingresos y gastos.
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)   # Nombre del perfil
    pin = db.Column(db.String(4), nullable=False)       # PIN de 4 dígitos (se guarda como texto)
    # Relaciones: cada perfil tiene muchos ingresos y gastos
    ingresos = db.relationship('Ingreso', backref='profile', lazy=True)
    gastos = db.relationship('Gasto', backref='profile', lazy=True)

# Modelo para un Gasto.
# Cada gasto tiene un monto (entero), una descripción (opcional), una fecha de creación y se asocia a un perfil.
class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)  # Se almacena como entero (no se usan decimales en pesos colombianos)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)

# Modelo para un Ingreso, similar al de gasto.
class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)

# ---------------------- RUTAS DE AUTENTICACIÓ(N) Y PERFILES ----------------------

# Ruta para la pantalla de login.
# Muestra todos los perfiles (al estilo Netflix) y una opción para crear uno nuevo.
@app.route('/login')
def login():
    # Si ya hay un perfil en sesión, redirige al dashboard (gestión de dinero)
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    profiles = Profile.query.all()  # Obtiene todos los perfiles de la base de datos
    return render_template('login.html', profiles=profiles)

# Ruta para seleccionar un perfil.
# Muestra un formulario para ingresar el PIN de 4 dígitos para el perfil seleccionado.
@app.route('/select_profile/<int:profile_id>', methods=['GET', 'POST'])
def select_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)  # Busca el perfil o retorna 404 si no existe
    if request.method == 'POST':
        pin_input = request.form.get('pin')
        if pin_input == profile.pin:
            session['profile_id'] = profile.id  # Guarda el ID del perfil en la sesión
            return redirect(url_for('dashboard'))
        else:
            flash("PIN incorrecto. Inténtalo de nuevo.", "danger")
            return redirect(url_for('select_profile', profile_id=profile_id))
    return render_template('select_profile.html', profile=profile)

# Ruta para crear un nuevo perfil.
# En esta pantalla se ingresa un nombre y un PIN de 4 dígitos.
@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        pin = request.form.get('pin')
        # Validación: se requiere nombre y PIN, el PIN debe tener exactamente 4 dígitos y ser numérico.
        if not name or not pin or len(pin) != 4 or not pin.isdigit():
            flash("Por favor, ingresa un nombre y un PIN de 4 dígitos.", "warning")
            return redirect(url_for('create_profile'))
        new_profile = Profile(name=name, pin=pin)
        db.session.add(new_profile)
        db.session.commit()
        flash("Perfil creado exitosamente.", "success")
        return redirect(url_for('login'))
    return render_template('create_profile.html')

# Ruta para cerrar sesión (salir del perfil actual).
@app.route('/logout')
def logout():
    session.pop('profile_id', None)  # Elimina el ID del perfil de la sesión
    return redirect(url_for('login'))

# ---------------------- RUTAS DE LA APLICACIÓN (GESTIÓN DE DINERO) ----------------------

# Ruta para el dashboard: muestra la gestión de dinero (balance, ingresos, gastos) para el perfil logueado.
@app.route('/dashboard')
def dashboard():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    profile_id = session['profile_id']
    # Consulta los gastos e ingresos asociados al perfil actual, ordenados de más recientes a más antiguos.
    gastos = Gasto.query.filter_by(profile_id=profile_id).order_by(Gasto.fecha.desc()).all()
    ingresos = Ingreso.query.filter_by(profile_id=profile_id).order_by(Ingreso.fecha.desc()).all()
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    total_gastos = sum(gasto.monto for gasto in gastos)
    balance = total_ingresos - total_gastos
    return render_template('dashboard.html', balance=balance, gastos=gastos, ingresos=ingresos)

# Ruta para agregar un gasto, asociándolo al perfil logueado.
@app.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    profile_id = session['profile_id']
    if monto:
        try:
            # Limpia el valor: quita puntos y comas para obtener solo dígitos.
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

# Ruta para agregar un ingreso, asociándolo al perfil logueado.
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

# Ruta para deshacer (eliminar) un movimiento (gasto o ingreso) del perfil actual.
@app.route('/deshacer/<tipo>/<int:mov_id>', methods=['POST'])
def deshacer_movimiento(tipo, mov_id):
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    if tipo == 'gasto':
        # Busca el gasto que pertenece al perfil actual, o devuelve 404 si no existe.
        mov = Gasto.query.filter_by(id=mov_id, profile_id=session['profile_id']).first_or_404()
    elif tipo == 'ingreso':
        mov = Ingreso.query.filter_by(id=mov_id, profile_id=session['profile_id']).first_or_404()
    else:
        return redirect(url_for('dashboard'))
    db.session.delete(mov)
    db.session.commit()
    return redirect(url_for('dashboard'))

# ---------------------- RUTA "INDEX" ORIGINAL ----------------------
# Modificada para redirigir a la pantalla de login si no hay un perfil en sesión,
# o al dashboard si ya se ha seleccionado uno.
@app.route('/')
def index():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# ---------------------- ARRANQUE DE LA APLICACIÓN ----------------------
if __name__ == '__main__':
    # Render inyecta la variable PORT en producción; si no está definida, se usa 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    