from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta  # Se añadió timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finanzas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu_secreto_aqui'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Se añade la duración de la sesión
db = SQLAlchemy(app)

# Filtro Jinja para formatear números al estilo español (ej. 10.000,50)
def format_money(value):
    s = "{:,.2f}".format(value)  # ejemplo: "10,000.00"
    # Intercambia comas y puntos para formato español
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# Modelos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    gastos = db.relationship('Gasto', backref='user', lazy=True)
    ingresos = db.relationship('Ingreso', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Necesitas iniciar sesión.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rutas de autenticación
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if not username or not password or not confirm:
            flash("Debes llenar todos los campos", "danger")
            return redirect(url_for('register'))
        if password != confirm:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe", "danger")
            return redirect(url_for('register'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Usuario registrado. Ahora inicia sesión.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Evitar que un usuario logueado vea de nuevo el login
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')  # '1' si está marcado
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session.permanent = True if remember == '1' else False
            
            # Flash del mensaje de bienvenida
            flash("Bienvenido, " + user.username, "success")
            return redirect(url_for('index'))
        else:
            flash("Credenciales incorrectas", "danger")
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Has cerrado sesión", "info")
    return redirect(url_for('login'))

# Ruta principal: muestra balance y movimientos
@app.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])
    gastos = user.gastos
    ingresos = user.ingresos
    for g in gastos:
        g.tipo = 'Gasto'
    for i in ingresos:
        i.tipo = 'Ingreso'
    total_ingresos = sum(i.monto for i in ingresos)
    total_gastos = sum(g.monto for g in gastos)
    balance = total_ingresos - total_gastos
    movimientos = gastos + ingresos
    movimientos.sort(key=lambda x: x.fecha, reverse=True)
    return render_template('index.html', balance=balance, movimientos=movimientos)

@app.route('/agregar_gasto', methods=['POST'])
@login_required
def agregar_gasto():
    user = User.query.get(session['user_id'])
    monto_str = request.form.get('monto')
    # Quitar separadores de miles y convertir coma a punto para poder convertir a float
    monto_str = monto_str.replace(".", "").replace(",", ".")
    descripcion = request.form.get('descripcion')
    if monto_str:
        nuevo_gasto = Gasto(monto=float(monto_str), descripcion=descripcion, user_id=user.id)
        db.session.add(nuevo_gasto)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/agregar_ingreso', methods=['POST'])
@login_required
def agregar_ingreso():
    user = User.query.get(session['user_id'])
    monto_str = request.form.get('monto')
    monto_str = monto_str.replace(".", "").replace(",", ".")
    descripcion = request.form.get('descripcion')
    if monto_str:
        nuevo_ingreso = Ingreso(monto=float(monto_str), descripcion=descripcion, user_id=user.id)
        db.session.add(nuevo_ingreso)
        db.session.commit()
    return redirect(url_for('index'))

# Ruta para deshacer (eliminar) un movimiento
@app.route('/deshacer/<tipo>/<int:mov_id>', methods=['POST'])
@login_required
def deshacer_movimiento(tipo, mov_id):
    user = User.query.get(session['user_id'])
    if tipo == 'gasto':
        mov = Gasto.query.get_or_404(mov_id)
    elif tipo == 'ingreso':
        mov = Ingreso.query.get_or_404(mov_id)
    else:
        flash("Tipo inválido", "danger")
        return redirect(url_for('index'))
    if mov.user_id != user.id:
        flash("No tienes permiso para eliminar este movimiento", "danger")
        return redirect(url_for('index'))
    db.session.delete(mov)
    db.session.commit()
    flash("Movimiento eliminado", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
