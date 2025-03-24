import os
from flask import Flask, render_template, request, redirect, url_for  # Importa funciones básicas de Flask
from flask_sqlalchemy import SQLAlchemy  # Importa SQLAlchemy para manejar la base de datos
from flask_migrate import Migrate  # Importa Flask-Migrate para gestionar migraciones (cambios en la base de datos)
from datetime import datetime  # Importa datetime para trabajar con fechas

# Crea la aplicación Flask
app = Flask(__name__)

# Configuración de la clave secreta de la app.
# Esto se usa para seguridad (por ejemplo, para firmar cookies). Se puede obtener de una variable de entorno o usar un valor por defecto.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')

# Desactiva el caché para archivos estáticos (útil en desarrollo para ver cambios inmediatamente)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configuración de la conexión a la base de datos.
# Si existe la variable DATABASE_URL (en producción, Render la define), se usará esa.
# Si no, se usará la URL externa que se pasó, conectándose a PostgreSQL.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://gestiondinero_user:sbZYaGViuEdnEOoVl3OuvJgqBaJPOHym@dpg-cvg6fgdumphs73dem04g-a.oregon-postgres.render.com/gestiondinero'
)
# Evita que SQLAlchemy rastree cambios de forma innecesaria (ahorra memoria)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa la base de datos (SQLAlchemy) y el sistema de migraciones (Flask-Migrate)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define un filtro personalizado para formatear números en formato de dinero.
# Este filtro recibe un número y lo formatea con dos decimales y separadores de miles.
def format_money(value):
    # Primero formatea el número, por ejemplo, 10000 se convierte en "10,000.00"
    s = "{:,.2f}".format(value)
    # Luego, intercambia las comas y puntos para obtener el formato español: "10.000,00"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

# Registra el filtro en el entorno de Jinja (el motor de plantillas de Flask)
app.jinja_env.filters['format_money'] = format_money

# --- Definición de modelos (las tablas de la base de datos) ---

# Modelo para los gastos. Cada gasto tiene un ID, un monto (entero), una descripción (opcional) y una fecha (por defecto la fecha actual).
class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)  # Se almacena como entero (sin decimales)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# Modelo para los ingresos. Funciona de manera similar al de gastos.
class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)  # Se almacena como entero
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# --- Rutas de la aplicación ---

# Ruta principal ("/"): muestra el balance y la lista de movimientos (gastos e ingresos)
@app.route('/')
def index():
    # Consulta todos los gastos e ingresos, ordenados de más recientes a más antiguos.
    gastos = Gasto.query.order_by(Gasto.fecha.desc()).all()
    ingresos = Ingreso.query.order_by(Ingreso.fecha.desc()).all()
    # Suma todos los montos de ingresos y gastos respectivamente.
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    total_gastos = sum(gasto.monto for gasto in gastos)
    # Calcula el balance restando los gastos de los ingresos.
    balance = total_ingresos - total_gastos
    # Renderiza la plantilla 'index.html', pasando las variables balance, gastos e ingresos.
    return render_template('index.html', balance=balance, gastos=gastos, ingresos=ingresos)

# Ruta para agregar un gasto. Se activa al enviar el formulario con método POST.
@app.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    # Obtiene los valores del formulario
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    if monto:
        try:
            # Limpia el valor del monto eliminando puntos y comas para que solo queden dígitos
            monto_clean = monto.replace(".", "").replace(",", "")
            # Crea una nueva instancia del modelo Gasto, convirtiendo el monto a entero.
            nuevo_gasto = Gasto(monto=int(monto_clean), descripcion=descripcion)
            # Agrega el nuevo gasto a la sesión de la base de datos y la guarda
            db.session.add(nuevo_gasto)
            db.session.commit()
        except Exception as e:
            # Si ocurre un error, revierte la sesión y muestra el error por consola
            db.session.rollback()
            print("Error al agregar gasto:", e)
    else:
        # Imprime mensaje en consola si el campo monto está vacío
        print("El campo monto es obligatorio.")
    # Redirige al usuario a la página principal
    return redirect(url_for('index'))

# Ruta para agregar un ingreso, similar a la de gasto.
@app.route('/agregar_ingreso', methods=['POST'])
def agregar_ingreso():
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    if monto:
        try:
            monto_clean = monto.replace(".", "").replace(",", "")
            nuevo_ingreso = Ingreso(monto=int(monto_clean), descripcion=descripcion)
            db.session.add(nuevo_ingreso)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Error al agregar ingreso:", e)
    else:
        print("El campo monto es obligatorio.")
    return redirect(url_for('index'))

# Ruta para deshacer (eliminar) un movimiento.
# Recibe dos parámetros: tipo (gasto o ingreso) y mov_id (ID del registro a eliminar).
@app.route('/deshacer/<tipo>/<int:mov_id>', methods=['POST'])
def deshacer_movimiento(tipo, mov_id):
    if tipo == 'gasto':
        mov = Gasto.query.get_or_404(mov_id)  # Busca el gasto por ID o devuelve 404 si no existe.
    elif tipo == 'ingreso':
        mov = Ingreso.query.get_or_404(mov_id)  # Lo mismo para ingreso.
    else:
        # Si el tipo no es válido, redirige a la página principal sin hacer nada.
        return redirect(url_for('index'))
    # Elimina el registro y guarda el cambio en la base de datos.
    db.session.delete(mov)
    db.session.commit()
    return redirect(url_for('index'))

# Arranque de la aplicación.
# Render inyecta la variable de entorno PORT en producción, y en caso de no existir, se usa el puerto 5000.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
