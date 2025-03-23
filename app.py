import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)

# Configuración de la SECRET_KEY (puedes configurarla desde una variable de entorno)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')

# Configuración de la base de datos: usa la variable DATABASE_URL de Render si existe,
# o el External Database URL que proporcionaste.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://gestiondinero_user:sbZYaGViuEdnEOoVl3OuvJgqBaJPOHym@dpg-cvg6fgdumphs73dem04g-a.oregon-postgres.render.com/gestiondinero'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa SQLAlchemy y Flask-Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Registrar filtro personalizado para formatear el dinero
def format_money(value):
    s = "{:,.2f}".format(value)  # Ejemplo: "10,000.00"
    # Convertir al formato español: "10.000,00"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# Modelos
class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# Ruta principal
@app.route('/')
def index():
    gastos = Gasto.query.all()
    ingresos = Ingreso.query.all()
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
            nuevo_gasto = Gasto(monto=float(monto), descripcion=descripcion)
            db.session.add(nuevo_gasto)
            db.session.commit()
            flash("Gasto agregado exitosamente.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error al agregar gasto: " + str(e), "danger")
    else:
        flash("El campo monto es obligatorio.", "warning")
    return redirect(url_for('index'))

# Ruta para agregar un ingreso
@app.route('/agregar_ingreso', methods=['POST'])
def agregar_ingreso():
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    if monto:
        try:
            nuevo_ingreso = Ingreso(monto=float(monto), descripcion=descripcion)
            db.session.add(nuevo_ingreso)
            db.session.commit()
            flash("Ingreso agregado exitosamente.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error al agregar ingreso: " + str(e), "danger")
    else:
        flash("El campo monto es obligatorio.", "warning")
    return redirect(url_for('index'))

# Ruta para cerrar sesión (dummy, ya que no implementamos autenticación)
@app.route('/logout')
def logout():
    flash("Sesión cerrada.", "info")
    return redirect(url_for('index'))

# Arranque de la aplicación, usando el puerto proporcionado por Render o 5000 por defecto
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)