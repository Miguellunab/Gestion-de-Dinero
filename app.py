import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, Profile, Gasto, Ingreso, Billetera
from flask_migrate import Migrate
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)

# Inicializa la base de datos y las migraciones
db.init_app(app)
migrate = Migrate(app, db)

# ---------------------- FILTRO PERSONALIZADO ----------------------
def format_money(value):
    s = "{:,.2f}".format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# ---------------------- MIDDLEWARE PARA TIMEOUT DE SESIÓN ----------------------
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

# ---------------------- RUTAS DE AUTENTICACIÓN Y PERFILES ----------------------
@app.route('/login')
def login():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    profiles = Profile.query.all()
    return render_template('login.html', profiles=profiles)

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

@app.route('/logout')
def logout():
    session.pop('profile_id', None)
    return redirect(url_for('login'))

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

@app.route('/delete_profile/<int:profile_id>', methods=['POST'])
def delete_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    # Borra los gastos e ingresos asociados
    Gasto.query.filter_by(profile_id=profile_id).delete()
    Ingreso.query.filter_by(profile_id=profile_id).delete()
    # Borra el perfil
    db.session.delete(profile)
    db.session.commit()
    flash("Perfil eliminado correctamente", "success")
    return redirect(url_for('login'))

# ---------------------- RUTAS DE LA APLICACIÓN (GESTIÓN DE DINERO) ----------------------
@app.route('/dashboard')
def dashboard():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    profile = Profile.query.get_or_404(profile_id)
    
    # Consulta gastos e ingresos
    gastos = Gasto.query.filter_by(profile_id=profile_id).order_by(Gasto.fecha.desc()).all()
    ingresos = Ingreso.query.filter_by(profile_id=profile_id).order_by(Ingreso.fecha.desc()).all()
    
    # Normalizar cuentas "none" a "Efectivo"
    for ingreso in ingresos:
        if not ingreso.cuenta or ingreso.cuenta == 'none':
            ingreso.cuenta = 'Efectivo'

    for gasto in gastos:
        if not gasto.cuenta or gasto.cuenta == 'none':
            gasto.cuenta = 'Efectivo'
    
    # Consulta billeteras
    billeteras = Billetera.query.filter_by(profile_id=profile_id).all()
    
    # Si no hay billeteras, crear las predeterminadas
    if not billeteras:
        billeteras_predefinidas = [
            {"nombre": "Efectivo", "icono": "money-bill-wave", "color": "#28a745"},
            {"nombre": "Bancolombia", "icono": "university", "color": "#007bff"},
            {"nombre": "Nequi", "icono": "mobile-alt", "color": "#e83e8c"}
        ]
        
        for billetera in billeteras_predefinidas:
            nueva = Billetera(
                nombre=billetera['nombre'],
                icono=billetera['icono'],
                color=billetera['color'],
                profile_id=profile_id
            )
            db.session.add(nueva)
        
        db.session.commit()
        billeteras = Billetera.query.filter_by(profile_id=profile_id).all()
    
    # Calcular balance global
    total_gastos = sum(gasto.monto for gasto in gastos)
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    balance = total_ingresos - total_gastos
    
    # Calcular balance por cuenta
    balance_por_cuenta = {}
    
    # Sumar ingresos por cuenta
    for ingreso in ingresos:
        cuenta = ingreso.cuenta or "Efectivo"
        if cuenta not in balance_por_cuenta:
            balance_por_cuenta[cuenta] = 0
        balance_por_cuenta[cuenta] += ingreso.monto
    
    # Restar gastos por cuenta
    for gasto in gastos:
        cuenta = gasto.cuenta or "Efectivo"
        if cuenta not in balance_por_cuenta:
            balance_por_cuenta[cuenta] = 0
        balance_por_cuenta[cuenta] -= gasto.monto
    
    # Eliminar cuentas con balance cero
    balance_por_cuenta = {k: v for k, v in balance_por_cuenta.items() if v != 0}
    
    # Crear un diccionario de billeteras para mostrar iconos y colores correctos
    billeteras_dict = {b.nombre: {"icono": b.icono, "color": b.color} for b in billeteras}
    
    return render_template('dashboard.html', 
                          profile=profile, 
                          balance=balance, 
                          gastos=gastos, 
                          ingresos=ingresos, 
                          balance_por_cuenta=balance_por_cuenta,
                          billeteras=billeteras,
                          billeteras_dict=billeteras_dict)

@app.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    cuenta = request.form.get('cuenta', 'Efectivo')
    profile_id = session['profile_id']
    
    if monto:
        try:
            monto_clean = monto.replace(".", "").replace(",", "")
            nuevo_gasto = Gasto(
                monto=int(monto_clean),
                descripcion=descripcion,
                profile_id=profile_id,
                cuenta=cuenta  # Guardar la cuenta seleccionada
            )
            db.session.add(nuevo_gasto)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar gasto: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))

@app.route('/agregar_ingreso', methods=['POST'])
def agregar_ingreso():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    monto = request.form.get('monto')
    descripcion = request.form.get('descripcion')
    cuenta = request.form.get('cuenta', 'Efectivo')
    profile_id = session['profile_id']
    
    if monto:
        try:
            monto_clean = monto.replace(".", "").replace(",", "")
            nuevo_ingreso = Ingreso(
                monto=int(monto_clean),
                descripcion=descripcion,
                profile_id=profile_id,
                cuenta=cuenta  # Guardar la cuenta seleccionada
            )
            db.session.add(nuevo_ingreso)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar ingreso: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))

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

@app.route('/editar_movimiento/<tipo>/<int:id>', methods=['POST'])
def editar_movimiento(tipo, id):
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    
    # Obtener los datos del formulario
    monto = request.form.get('monto', '0')
    descripcion = request.form.get('descripcion', '')
    cuenta = request.form.get('cuenta', 'Efectivo')
    
    # Limpiar el monto
    monto_clean = monto.replace(".", "").replace(",", "")
    
    try:
        monto_int = int(monto_clean)
        
        # Actualizar según el tipo de movimiento
        if tipo == 'ingreso':
            movimiento = Ingreso.query.filter_by(id=id, profile_id=profile_id).first_or_404()
            movimiento.monto = monto_int
            movimiento.descripcion = descripcion
            movimiento.cuenta = cuenta
            mensaje = "Ingreso actualizado correctamente"
            
        elif tipo == 'gasto':
            movimiento = Gasto.query.filter_by(id=id, profile_id=profile_id).first_or_404()
            movimiento.monto = monto_int
            movimiento.descripcion = descripcion
            movimiento.cuenta = cuenta
            mensaje = "Gasto actualizado correctamente"
            
        db.session.commit()
        flash(mensaje, 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar el movimiento: {str(e)}", 'danger')
    
    return redirect(url_for('dashboard'))

# Nuevas rutas para gestión de billeteras
@app.route('/billeteras')
def listar_billeteras():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    billeteras = Billetera.query.filter_by(profile_id=profile_id).all()
    
    # Billeteras predeterminadas que siempre deben existir
    billeteras_predefinidas = [
        {"nombre": "Efectivo", "icono": "money-bill-wave", "color": "#28a745"},
        {"nombre": "Bancolombia", "icono": "university", "color": "#007bff"},
        {"nombre": "Nequi", "icono": "mobile-alt", "color": "#e83e8c"}
    ]
    
    # Verificar si ya existen las billeteras predefinidas
    nombres_existentes = [b.nombre for b in billeteras]
    
    # Crear las billeteras predefinidas si no existen
    for billetera in billeteras_predefinidas:
        if billetera['nombre'] not in nombres_existentes:
            nueva = Billetera(
                nombre=billetera['nombre'],
                icono=billetera['icono'],
                color=billetera['color'],
                profile_id=profile_id
            )
            db.session.add(nueva)
    
    # Guardar cambios si hubo nuevas billeteras
    if len(billeteras) < len(billeteras_predefinidas):
        db.session.commit()
        # Refrescar la lista de billeteras
        billeteras = Billetera.query.filter_by(profile_id=profile_id).all()
    
    return render_template('billeteras.html', billeteras=billeteras)

@app.route('/billetera/nueva', methods=['POST'])
def crear_billetera():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    nombre = request.form.get('nombre')
    icono = request.form.get('icono')
    color = request.form.get('color', '#6c757d')
    
    # Validar que no exista ya una billetera con ese nombre
    existe = Billetera.query.filter_by(profile_id=profile_id, nombre=nombre).first()
    if existe:
        flash('Ya tienes una billetera con ese nombre', 'warning')
        return redirect(url_for('listar_billeteras'))
    
    # Crear la nueva billetera
    nueva_billetera = Billetera(
        nombre=nombre,
        icono=icono,
        color=color,
        profile_id=profile_id
    )
    
    db.session.add(nueva_billetera)
    db.session.commit()
    
    flash(f'Billetera "{nombre}" creada exitosamente', 'success')
    return redirect(url_for('listar_billeteras'))

@app.route('/billetera/<int:id>/editar', methods=['POST'])
def editar_billetera(id):
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    billetera = Billetera.query.get_or_404(id)
    
    # Verificar que la billetera pertenezca al usuario actual
    if billetera.profile_id != session['profile_id']:
        flash('No tienes permiso para editar esta billetera', 'danger')
        return redirect(url_for('listar_billeteras'))
    
    # Verificar si es la billetera Efectivo (la única que no se puede editar)
    if billetera.nombre == "Efectivo":
        flash('No puedes modificar la billetera principal', 'warning')
        return redirect(url_for('listar_billeteras'))
    
    nombre_anterior = billetera.nombre
    nombre = request.form.get('nombre')
    icono = request.form.get('icono')
    color = request.form.get('color', '#6c757d')
    
    # Actualizar datos
    billetera.nombre = nombre
    billetera.icono = icono
    billetera.color = color
    
    # Actualizar también las transacciones si cambió el nombre
    if nombre_anterior != nombre:
        Gasto.query.filter_by(profile_id=session['profile_id'], cuenta=nombre_anterior).update({Gasto.cuenta: nombre})
        Ingreso.query.filter_by(profile_id=session['profile_id'], cuenta=nombre_anterior).update({Ingreso.cuenta: nombre})
    
    db.session.commit()
    
    flash(f'Billetera "{nombre}" actualizada correctamente', 'success')
    return redirect(url_for('listar_billeteras'))

@app.route('/billetera/<int:id>/eliminar', methods=['POST'])
def eliminar_billetera(id):
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    billetera = Billetera.query.get_or_404(id)
    
    # Verificar que la billetera pertenezca al usuario actual
    if billetera.profile_id != session['profile_id']:
        flash('No tienes permiso para eliminar esta billetera', 'danger')
        return redirect(url_for('listar_billeteras'))
    
    # Verificar si es la billetera Efectivo (la única que no se puede eliminar)
    if billetera.nombre == "Efectivo":
        flash('No puedes eliminar la billetera principal', 'warning')
        return redirect(url_for('listar_billeteras'))
    
    nombre_billetera = billetera.nombre
    
    # Antes de eliminar, actualizar las transacciones que usen esta billetera
    Gasto.query.filter_by(profile_id=session['profile_id'], cuenta=nombre_billetera).update({Gasto.cuenta: "Efectivo"})
    Ingreso.query.filter_by(profile_id=session['profile_id'], cuenta=nombre_billetera).update({Ingreso.cuenta: "Efectivo"})
    
    db.session.delete(billetera)
    db.session.commit()
    
    flash(f'Billetera "{nombre_billetera}" eliminada correctamente', 'success')
    return redirect(url_for('listar_billeteras'))

# Ruta index: redirige a dashboard o login según la sesión
@app.route('/')
def index():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# ---------------------- ARRANQUE DE LA APLICACIÓN ----------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
