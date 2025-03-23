import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)

# Configuración de la SECRET_KEY (puedes configurarla desde una variable de entorno)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')

# Configuración de la base de datos: utiliza DATABASE_URL si está definida; de lo contrario, usa el External Database URL.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://gestiondinero_user:sbZYaGViuEdnEOoVl3OuvJgqBaJPOHym@dpg-cvg6fgdumphs73dem04g-a.oregon-postgres.render.com/gestiondinero'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos y migraciones
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Filtro personalizado para formatear el dinero (si deseas mostrarlo con formato en la tabla)
def format_money(value):
    # Formatea el número con dos decimales y separadores de miles (ej: "10.000,00")
    s = "{:,.2f}".format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# Modelos
class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)  # Se almacena como entero
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)  # Se almacena como entero
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# Ruta principal: muestra los movimientos y el balance
@app.route('/')
def index():
    gastos = Gasto.query.order_by(Gasto.fecha.desc()).all()
    ingresos = Ingreso.query.order_by(Ingreso.fecha.desc()).all()
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    total_gastos = sum(gasto.monto for gasto in gastos)
    balance = total_ingresos - total_gastos
    return render_template('index.html', balance=balance, gastos=gastos, ingresos=ingresos)

# Ruta para agregar un gasto
@app.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    if monto:
        try:
            # Eliminar cualquier carácter que no sea dígito y convertir a entero
            monto_clean = monto.replace(".", "").replace(",", "")
            nuevo_gasto = Gasto(monto=int(monto_clean), descripcion=descripcion)
            db.session.add(nuevo_gasto)
            db.session.commit()
            # flash("Gasto agregado exitosamente.", "success")
        except Exception as e:
            db.session.rollback()
            # flash("Error al agregar gasto: " + str(e), "danger")
            print("Error al agregar gasto:", e)
    else:
        # flash("El campo monto es obligatorio.", "warning")
        print("El campo monto es obligatorio.")
    return redirect(url_for('index'))

# Ruta para agregar un ingreso
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
            # flash("Ingreso agregado exitosamente.", "success")
        except Exception as e:
            db.session.rollback()
            # flash("Error al agregar ingreso: " + str(e), "danger")
            print("Error al agregar ingreso:", e)
    else:
        # flash("El campo monto es obligatorio.", "warning")
        print("El campo monto es obligatorio.")
    return redirect(url_for('index'))

# Ruta para deshacer (eliminar) un movimiento
@app.route('/deshacer/<tipo>/<int:mov_id>', methods=['POST'])
def deshacer_movimiento(tipo, mov_id):
    if tipo == 'gasto':
        mov = Gasto.query.get_or_404(mov_id)
    elif tipo == 'ingreso':
        mov = Ingreso.query.get_or_404(mov_id)
    else:
        return redirect(url_for('index'))
    db.session.delete(mov)
    db.session.commit()
    return redirect(url_for('index'))

# Arranque de la aplicación (Render inyecta PORT; usamos 5000 por defecto)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
