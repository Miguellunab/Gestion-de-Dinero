import os
from dotenv import load_dotenv  # Añadir esta línea
from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, Profile, Gasto, Ingreso, Billetera, Transferencia  # Importar el nuevo modelo
from flask_migrate import Migrate
from datetime import datetime, timedelta, date  # Añadir importación de funciones para manipular fechas
import calendar
from flask_wtf.csrf import CSRFProtect  # Añadir esta importación al principio del archivo
import json
from markupsafe import Markup

# Cargar variables de entorno del archivo .env
load_dotenv()  # Añadir esta línea antes de crear la app

app = Flask(__name__)
app.config.from_object(Config)

csrf = CSRFProtect(app)  # Añadir esta línea justo después de crear la app

# Inicializa la base de datos y las migraciones
db.init_app(app)
migrate = Migrate(app, db)

# ---------------------- ENCABEZADOS DE SEGURIDAD HTTP ----------------------
# Cachear la política CSP para no reconstruirla en cada solicitud
_csp_policy = None

@app.after_request
def add_security_headers(response):
    # Solo aplicar encabezados a respuestas HTML
    if not response.mimetype.startswith('text/html'):
        return response
    
    # Encabezados básicos siempre rápidos de añadir
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'same-origin'
    
    # Política CSP más costosa - cachear
    global _csp_policy
    if _csp_policy is None:
        _csp_policy = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "media-src 'self'; "
            "object-src 'none'; "
            "form-action 'self';"
        )
    
    response.headers['Content-Security-Policy'] = _csp_policy
    
    # Solo añadir HSTS en producción
    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# ---------------------- FILTRO PERSONALIZADO ----------------------
def format_money(value):
    s = "{:,.2f}".format(value)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

app.jinja_env.filters['format_money'] = format_money

# Registrar filtros de template
@app.template_filter('tojson')
def _tojson(obj):
    return Markup(json.dumps(obj))

@app.template_filter('format_money')
def format_money(value):
    """Formatea valores monetarios correctamente según el tipo de moneda."""
    try:
        # Si hay una sesión activa, obtener el perfil y su moneda
        if 'profile_id' in session:
            profile = Profile.query.get(session['profile_id'])
            if profile and profile.moneda == 'COP':
                # Para pesos colombianos, mostrar sin decimales
                return f"{value:,.0f}".replace(",", ".")
            else:
                # Para otras monedas, mostrar con dos decimales
                return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            # Si no hay sesión, usar formato entero por defecto
            return f"{value:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"

# ---------------------- MIDDLEWARE PARA TIMEOUT DE SESIÓN ----------------------
@app.before_request
def check_session_timeout():
    if 'profile_id' in session and request.endpoint != 'static':  # No verificar para archivos estáticos
        if 'last_activity' in session:
            now = datetime.utcnow()
            try:
                last = datetime.fromisoformat(session['last_activity'])  # Usar fromisoformat en vez de parser
                if (now - last).total_seconds() > 15 * 60:
                    session.clear()
                    flash("Tu sesión ha expirado por inactividad.", "info")
                    return redirect(url_for('login'))
            except Exception:
                pass  # Silenciosamente ignorar errores de formato
        
        # Solo actualizar timestamp en solicitudes no frecuentes
        if not request.path.startswith('/static/'):
            session['last_activity'] = datetime.utcnow().isoformat()

# ---------------------- RUTAS DE AUTENTICACIÓN Y PERFILES ----------------------
@app.route('/login')
def login():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    # Ordenar perfiles por fecha de creación
    profiles = Profile.query.order_by(Profile.fecha_creacion).all()
    return render_template('login.html', profiles=profiles)

@app.route('/select_profile/<int:profile_id>', methods=['GET', 'POST'])
def select_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    
    # Verificación rápida de bloqueo sin llamadas adicionales a la base de datos
    if profile.lockout_until and profile.lockout_until > datetime.now():
        minutes_remaining = round((profile.lockout_until - datetime.now()).total_seconds() / 60)
        flash(f"Este perfil está bloqueado por {minutes_remaining} minutos debido a múltiples intentos incorrectos.", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        pin_input = request.form.get('pin')
        
        # Verificar PIN con el método secure
        if profile.check_pin(pin_input):
            # PIN correcto - resetear intentos solo si hubo intentos fallidos previos
            if profile.login_attempts > 0:
                profile.login_attempts = 0
                db.session.commit()
            
            # Configurar sesión
            session.permanent = True
            session['profile_id'] = profile.id
            session['last_activity'] = datetime.utcnow().isoformat()
            return redirect(url_for('dashboard'))
        else:
            # PIN incorrecto - actualizar contador y posiblemente bloquear
            profile.login_attempts += 1
            
            if profile.login_attempts >= 5:
                profile.lockout_until = datetime.now() + timedelta(minutes=30)
                db.session.commit()
                flash("Has excedido el número máximo de intentos. Tu cuenta ha sido bloqueada por 30 minutos.", "danger")
            else:
                db.session.commit()
                remaining_attempts = 5 - profile.login_attempts
                flash(f"PIN incorrecto. Te quedan {remaining_attempts} intentos.", "danger")
            
            return redirect(url_for('select_profile', profile_id=profile_id))
            
    return render_template('select_profile.html', profile=profile)

@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        pin = request.form.get('pin')
        moneda = request.form.get('moneda', 'COP')  # Obtener moneda seleccionada, COP por defecto
        
        if not name or not pin or len(pin) != 4 or not pin.isdigit():
            flash("Por favor, ingresa un nombre y un PIN de 4 dígitos.", "warning")
            return redirect(url_for('create_profile'))
        
        # Crear el nuevo perfil con la moneda seleccionada
        new_profile = Profile(name=name, pin=pin, moneda=moneda)
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
    
    # Consulta billeteras primero (son pocos registros)
    billeteras = Billetera.query.filter_by(profile_id=profile_id).all()
    
    # Si no hay billeteras, crear las predeterminadas
    if not billeteras:
        billeteras_predefinidas = [
            {"nombre": "Efectivo", "icono": "fas fa-money-bill-wave", "color": "#28a745"},
            {"nombre": "Bancolombia", "icono": "fas fa-university", "color": "#007bff"},
            {"nombre": "Nequi", "icono": "fas fa-mobile-alt", "color": "#e83e8c"}
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
    
    # Crear un diccionario de billeteras para mostrar iconos y colores correctos
    billeteras_dict = {b.nombre: {"icono": b.icono, "color": b.color} for b in billeteras}
    
    # OPTIMIZACIÓN: Calcular el balance mediante una consulta específica en lugar de cargar todos los registros
    # Obtener suma total de ingresos
    total_ingresos = db.session.query(db.func.sum(Ingreso.monto)).filter_by(profile_id=profile_id).scalar() or 0
    
    # Obtener suma total de gastos
    total_gastos = db.session.query(db.func.sum(Gasto.monto)).filter_by(profile_id=profile_id).scalar() or 0
    
    # Calcular balance global
    balance = total_ingresos - total_gastos
    
    # OPTIMIZACIÓN: Calcular balance por cuenta con consultas eficientes
    # Saldo inicial para todas las cuentas es 0
    balance_por_cuenta = {billetera.nombre: 0 for billetera in billeteras}
    
    # Sumar ingresos por cuenta con una única consulta
    ingresos_por_cuenta = db.session.query(
        Ingreso.cuenta, db.func.sum(Ingreso.monto)
    ).filter_by(profile_id=profile_id).group_by(Ingreso.cuenta).all()
    
    for cuenta, monto in ingresos_por_cuenta:
        cuenta = cuenta if cuenta and cuenta != 'none' else "Efectivo"
        balance_por_cuenta[cuenta] = balance_por_cuenta.get(cuenta, 0) + monto
    
    # Restar gastos por cuenta con una única consulta
    gastos_por_cuenta = db.session.query(
        Gasto.cuenta, db.func.sum(Gasto.monto)
    ).filter_by(profile_id=profile_id).group_by(Gasto.cuenta).all()
    
    for cuenta, monto in gastos_por_cuenta:
        cuenta = cuenta if cuenta and cuenta != 'none' else "Efectivo"
        balance_por_cuenta[cuenta] = balance_por_cuenta.get(cuenta, 0) - monto
    
    # Eliminar cuentas con balance cero
    balance_por_cuenta = {k: v for k, v in balance_por_cuenta.items() if v != 0}
    
    # OPTIMIZACIÓN: Cargar solo los 5 movimientos más recientes
    # Obtener los 5 gastos más recientes
    gastos_recientes = Gasto.query.filter_by(profile_id=profile_id).order_by(Gasto.fecha.desc()).limit(5).all()
    
    # Obtener los 5 ingresos más recientes
    ingresos_recientes = Ingreso.query.filter_by(profile_id=profile_id).order_by(Ingreso.fecha.desc()).limit(5).all()
    
    # Normalizar cuentas "none" a "Efectivo"
    for ingreso in ingresos_recientes:
        if not ingreso.cuenta or ingreso.cuenta == 'none':
            ingreso.cuenta = 'Efectivo'

    for gasto in gastos_recientes:
        if not gasto.cuenta or gasto.cuenta == 'none':
            gasto.cuenta = 'Efectivo'
    
    # En el template, se combinan y ordenan para mostrar solo los 5 movimientos más recientes en total
    # El slice ya está incluido en la plantilla
    
    return render_template('dashboard.html', 
                          profile=profile, 
                          balance=balance, 
                          gastos=gastos_recientes, 
                          ingresos=ingresos_recientes, 
                          balance_por_cuenta=balance_por_cuenta,
                          billeteras=billeteras,
                          billeteras_dict=billeteras_dict,
                          show_accounts=True if balance_por_cuenta else False,
                          hide_balance=False)

@app.route('/agregar_gasto', methods=['POST'])
def agregar_gasto():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    profile = Profile.query.get_or_404(profile_id)
    monto = request.form.get('monto', '')
    descripcion = request.form.get('descripcion', '')
    cuenta = request.form.get('cuenta', 'Efectivo')
    
    # Validaciones estrictas
    if not monto or not monto.strip():
        flash("El monto es obligatorio", "danger")
        return redirect(url_for('dashboard'))
    
    # Validar que la descripción no exceda cierto límite
    if descripcion and len(descripcion) > 200:
        flash("La descripción no puede exceder los 200 caracteres", "danger")
        return redirect(url_for('dashboard'))
          # Validar que la cuenta exista para este usuario
    billetera = Billetera.query.filter_by(profile_id=profile_id, nombre=cuenta).first()
    if not billetera:
        flash(f"La billetera {cuenta} no existe o no te pertenece", "danger")
        return redirect(url_for('dashboard'))
    
    try:
        # Procesar el monto según la moneda del perfil
        if profile.moneda == 'COP':
            # Para COP usar valores enteros (sin centavos)
            monto_clean = monto.replace(".", "").replace(",", "")
            monto_valor = int(monto_clean)
        else:
            # Para otras monedas (USD), permitir decimales
            # Normalizar entrada: reemplazar coma por punto
            monto_clean = monto.replace(",", ".")
            # Remover puntos que sean separadores de miles (solo si hay más de un punto)
            dot_count = monto_clean.count('.')
            if dot_count > 1:
                # Si hay múltiples puntos, el último es decimal, los demás son separadores de miles
                parts = monto_clean.split('.')
                monto_clean = ''.join(parts[:-1]) + '.' + parts[-1]
            monto_valor = float(monto_clean)
        
        # Verificar que el monto sea positivo
        if monto_valor <= 0:
            flash("El monto debe ser mayor que cero", "danger")
            return redirect(url_for('dashboard'))
            
        nuevo_gasto = Gasto(
            monto=monto_valor,
            descripcion=descripcion,
            profile_id=profile_id,
            cuenta=cuenta
        )
        db.session.add(nuevo_gasto)
        db.session.commit()
        flash("Gasto registrado correctamente", "success")
    except ValueError:
        flash("El monto debe ser un valor numérico válido", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al agregar gasto: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))

@app.route('/agregar_ingreso', methods=['POST'])
def agregar_ingreso():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    profile = Profile.query.get_or_404(profile_id)
    monto = request.form.get('monto', '')
    descripcion = request.form.get('descripcion', '')
    cuenta = request.form.get('cuenta', 'Efectivo')
    
    # Validaciones estrictas
    if not monto or not monto.strip():
        flash("El monto es obligatorio", "danger")
        return redirect(url_for('dashboard'))
    
    # Validar que la descripción no exceda cierto límite
    if descripcion and len(descripcion) > 200:
        flash("La descripción no puede exceder los 200 caracteres", "danger")
        return redirect(url_for('dashboard'))
        
    # Validar que la cuenta exista para este usuario
    billetera = Billetera.query.filter_by(profile_id=profile_id, nombre=cuenta).first()
    if not billetera:
        flash(f"La billetera {cuenta} no existe o no te pertenece", "danger")
        return redirect(url_for('dashboard'))
    
    try:
        # Procesar el monto según la moneda del perfil
        if profile.moneda == 'COP':
            # Para COP usar valores enteros (sin centavos)
            monto_clean = monto.replace(".", "").replace(",", "")
            monto_valor = int(monto_clean)
        else:
            # Para otras monedas (USD), permitir decimales
            # Normalizar entrada: reemplazar coma por punto
            monto_clean = monto.replace(",", ".")
            # Remover puntos que sean separadores de miles (solo si hay más de un punto)
            dot_count = monto_clean.count('.')
            if dot_count > 1:
                # Si hay múltiples puntos, el último es decimal, los demás son separadores de miles
                parts = monto_clean.split('.')
                monto_clean = ''.join(parts[:-1]) + '.' + parts[-1]
            monto_valor = float(monto_clean)
        
        # Verificar que el monto sea positivo
        if monto_valor <= 0:
            flash("El monto debe ser mayor que cero", "danger")
            return redirect(url_for('dashboard'))
            
        nuevo_ingreso = Ingreso(
            monto=monto_valor,
            descripcion=descripcion,
            profile_id=profile_id,
            cuenta=cuenta
        )
        db.session.add(nuevo_ingreso)
        db.session.commit()
        flash("Ingreso registrado correctamente", "success")
    except ValueError:
        flash("El monto debe ser un valor numérico válido", "danger")
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
    profile = Profile.query.get_or_404(profile_id)
      # Obtener los datos del formulario
    monto = request.form.get('monto', '0')
    descripcion = request.form.get('descripcion', '')
    cuenta = request.form.get('cuenta', 'Efectivo')
    next_page = request.form.get('next', 'dashboard')  # Obtener la página a la que redirigir
    
    try:
        # Procesar el monto según la moneda del perfil
        if profile.moneda == 'COP':
            # Para COP usar valores enteros (sin centavos)
            monto_clean = monto.replace(".", "").replace(",", "")
            monto_valor = int(monto_clean)
        else:
            # Para otras monedas (USD), permitir decimales
            # Normalizar entrada: reemplazar coma por punto
            monto_clean = monto.replace(",", ".")
            # Remover puntos que sean separadores de miles (solo si hay más de un punto)
            dot_count = monto_clean.count('.')
            if dot_count > 1:
                # Si hay múltiples puntos, el último es decimal, los demás son separadores de miles
                parts = monto_clean.split('.')
                monto_clean = ''.join(parts[:-1]) + '.' + parts[-1]
            monto_valor = float(monto_clean)
        
        # Actualizar según el tipo de movimiento
        if tipo == 'ingreso':
            movimiento = Ingreso.query.filter_by(id=id, profile_id=profile_id).first_or_404()
            movimiento.monto = monto_valor
            movimiento.descripcion = descripcion
            movimiento.cuenta = cuenta
            mensaje = "Ingreso actualizado correctamente"
            
        elif tipo == 'gasto':
            movimiento = Gasto.query.filter_by(id=id, profile_id=profile_id).first_or_404()
            movimiento.monto = monto_valor
            movimiento.descripcion = descripcion
            movimiento.cuenta = cuenta
            mensaje = "Gasto actualizado correctamente"
            
        db.session.commit()
        flash(mensaje, 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar el movimiento: {str(e)}", 'danger')
    
    # Redirigir según el parámetro 'next'
    if next_page == 'movimientos':
        return redirect(url_for('movimientos'))
    else:
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
    # Asegurar que id sea un entero (SQLAlchemy ya lo hace, esto es redundante pero explícito)
    try:
        id = int(id)
    except ValueError:
        flash("ID de billetera inválido", "danger")
        return redirect(url_for('listar_billeteras'))
    
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

@app.route('/informes')
def informes():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    profile_id = session['profile_id']
    profile = Profile.query.get_or_404(profile_id)

    # Obtener parámetros de filtro
    periodo = request.args.get('periodo', 'mes')
    billetera_sel = request.args.get('billetera', 'Todas')
    fecha_str = request.args.get('fecha')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    hoy = date.today()

    # Determinar rango de fechas según periodo o rango personalizado
    if periodo == 'rango' and fecha_desde and fecha_hasta and fecha_desde != 'None' and fecha_hasta != 'None':
        try:
            inicio = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            fin = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        except ValueError:
            # Si hay un error de formato, usar el mes actual como fallback
            inicio = date(hoy.year, hoy.month, 1)
            ultimo_dia = calendar.monthrange(inicio.year, inicio.month)[1]
            fin = date(inicio.year, inicio.month, ultimo_dia)
    elif periodo == 'dia':
        if fecha_str and len(str(fecha_str)) == 10 and fecha_str != 'None':
            try:
                inicio = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                inicio = hoy
        else:
            inicio = hoy
        fin = inicio
    elif periodo == 'año':
        if fecha_str and fecha_str != 'None':
            try:
                year = int(fecha_str)
                inicio = date(year, 1, 1)
                fin = date(year, 12, 31)
            except (ValueError, TypeError):
                inicio = date(hoy.year, 1, 1)
                fin = date(hoy.year, 12, 31)
        else:
            inicio = date(hoy.year, 1, 1)
            fin = date(hoy.year, 12, 31)
    else:  # mes por defecto
        if fecha_str and len(str(fecha_str)) == 7 and fecha_str != 'None':
            try:
                year, month = map(int, fecha_str.split('-'))
                inicio = date(year, month, 1)
            except (ValueError, TypeError):
                inicio = date(hoy.year, hoy.month, 1)
        else:
            inicio = date(hoy.year, hoy.month, 1)
        ultimo_dia = calendar.monthrange(inicio.year, inicio.month)[1]
        fin = date(inicio.year, inicio.month, ultimo_dia)

    fecha_inicio = datetime.combine(inicio, datetime.min.time())
    fecha_fin = datetime.combine(fin, datetime.max.time())
    
    # Resto de la función sigue igual...
    # Consultar billeteras
    billeteras = Billetera.query.filter_by(profile_id=profile_id).all()
    billeteras_dict = {b.nombre: {"icono": b.icono, "color": b.color} for b in billeteras}
    billeteras_nombres = [b.nombre for b in billeteras]

    # Filtro de billetera
    filtro_gasto = [Gasto.profile_id == profile_id, Gasto.fecha.between(fecha_inicio, fecha_fin)]
    filtro_ingreso = [Ingreso.profile_id == profile_id, Ingreso.fecha.between(fecha_inicio, fecha_fin)]
    if billetera_sel != 'Todas':
        filtro_gasto.append(Gasto.cuenta == billetera_sel)
        filtro_ingreso.append(Ingreso.cuenta == billetera_sel)

    gastos = Gasto.query.filter(*filtro_gasto).order_by(Gasto.fecha).all()
    ingresos = Ingreso.query.filter(*filtro_ingreso).order_by(Ingreso.fecha).all()

    # Agrupar datos para la gráfica
    fechas = []
    billeteras_series = {}
    
    if billetera_sel == 'Todas':
        # Agrupar por billetera y fecha
        # Inicializar estructura
        for b in billeteras_nombres:
            billeteras_series[b] = {}
            
        # Determinar agrupación (día, mes, año, rango)
        if periodo == 'año':
            for m in range(1, 13):
                key = f"{inicio.year}-{m:02d}"
                for b in billeteras_nombres:
                    billeteras_series[b][key] = 0
            
            # Procesar gastos e ingresos
            for gasto in gastos:
                key = gasto.fecha.strftime('%Y-%m')
                cuenta = gasto.cuenta or 'Efectivo'
                if cuenta in billeteras_series:
                    billeteras_series[cuenta][key] = billeteras_series[cuenta].get(key, 0) - gasto.monto
            
            for ingreso in ingresos:
                key = ingreso.fecha.strftime('%Y-%m')
                cuenta = ingreso.cuenta or 'Efectivo'
                if cuenta in billeteras_series:
                    billeteras_series[cuenta][key] = billeteras_series[cuenta].get(key, 0) + ingreso.monto
            
            fechas = [f"{inicio.year}-{m:02d}" for m in range(1, 13)]
        else:
            # Por día (o rango)
            dias = (fin - inicio).days + 1
            for d in range(dias):
                day = inicio + timedelta(days=d)
                key = day.strftime('%Y-%m-%d')
                for b in billeteras_nombres:
                    billeteras_series[b][key] = 0
            
            # Procesar gastos e ingresos
            for gasto in gastos:
                key = gasto.fecha.strftime('%Y-%m-%d')
                cuenta = gasto.cuenta or 'Efectivo'
                if cuenta in billeteras_series and key in billeteras_series[cuenta]:
                    billeteras_series[cuenta][key] -= gasto.monto
            
            for ingreso in ingresos:
                key = ingreso.fecha.strftime('%Y-%m-%d')
                cuenta = ingreso.cuenta or 'Efectivo'
                if cuenta in billeteras_series and key in billeteras_series[cuenta]:
                    billeteras_series[cuenta][key] += ingreso.monto
            
            fechas = [(inicio + timedelta(days=d)).strftime('%Y-%m-%d') for d in range(dias)]
    else:
        # Lógica para una sola billetera
        fecha_dict = {}
        if periodo == 'dia':
            for h in range(24):
                fecha_dict[f"{inicio.strftime('%Y-%m-%d')} {h:02d}"] = {'gastos': 0, 'ingresos': 0}
            
            for gasto in gastos:
                key = gasto.fecha.strftime('%Y-%m-%d %H')
                if key in fecha_dict:
                    fecha_dict[key]['gastos'] += gasto.monto
            
            for ingreso in ingresos:
                key = ingreso.fecha.strftime('%Y-%m-%d %H')
                if key in fecha_dict:
                    fecha_dict[key]['ingresos'] += ingreso.monto
                    
        if periodo == 'año':
            for m in range(1, 13):
                key = f"{inicio.year}-{m:02d}"
                fecha_dict[key] = {'gastos': 0, 'ingresos': 0}
                
            for gasto in gastos:
                key = gasto.fecha.strftime('%Y-%m')
                if key in fecha_dict:
                    fecha_dict[key]['gastos'] += gasto.monto
                    
            for ingreso in ingresos:
                key = ingreso.fecha.strftime('%Y-%m')
                if key in fecha_dict:
                    fecha_dict[key]['ingresos'] += ingreso.monto
        else:
            # Mes o rango personalizado
            dias = (fin - inicio).days + 1
            for d in range(dias):
                day = inicio + timedelta(days=d)
                key = day.strftime('%Y-%m-%d')
                fecha_dict[key] = {'gastos': 0, 'ingresos': 0}
                
            for gasto in gastos:
                key = gasto.fecha.strftime('%Y-%m-%d')
                if key in fecha_dict:
                    fecha_dict[key]['gastos'] += gasto.monto
                    
            for ingreso in ingresos:
                key = ingreso.fecha.strftime('%Y-%m-%d')
                if key in fecha_dict:
                    fecha_dict[key]['ingresos'] += ingreso.monto
                    
        # Convertir el diccionario a lista de pares para la plantilla
        fechas = [[k, v] for k, v in sorted(fecha_dict.items())]

    # Totales
    total_gastos = sum(gasto.monto for gasto in gastos)
    total_ingresos = sum(ingreso.monto for ingreso in ingresos)
    balance_periodo = total_ingresos - total_gastos

    # Para el selector de años y meses
    anios = list({g.fecha.year for g in Gasto.query.filter_by(profile_id=profile_id)} | {i.fecha.year for i in Ingreso.query.filter_by(profile_id=profile_id)})
    anios.sort(reverse=True)
    if not anios:  # Si no hay años, agregar el año actual
        anios = [hoy.year]
    meses = list(range(1, 13))

    return render_template(
        'informes.html',
        profile=profile,
        periodo=periodo,
        fechas=fechas,
        billeteras_dict=billeteras_dict,
        billeteras_nombres=billeteras_nombres,
        billetera_sel=billetera_sel,
        billeteras_series=billeteras_series,
        total_gastos=total_gastos,
        total_ingresos=total_ingresos,
        balance_periodo=balance_periodo,
        fecha_inicio=inicio,
        fecha_fin=fin,
        anios=anios,
        meses=meses,
        hoy=hoy,
        fecha_str=fecha_str,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

@app.route('/movimientos')
def movimientos():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    profile = Profile.query.get_or_404(profile_id)
    
    # Parámetros de paginación y filtrado
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Cantidad de movimientos por página
    
    # Filtros
    tipos_seleccionados = request.args.getlist('tipo')
    cuenta_seleccionada = request.args.get('cuenta', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    # Construir la consulta base
    query_ingresos = Ingreso.query.filter_by(profile_id=profile_id)
    query_gastos = Gasto.query.filter_by(profile_id=profile_id)
    
    # Aplicar filtros
    if tipos_seleccionados and len(tipos_seleccionados) == 1:
        if 'ingreso' not in tipos_seleccionados:
            query_ingresos = query_ingresos.filter(False)
        if 'gasto' not in tipos_seleccionados:
            query_gastos = query_gastos.filter(False)
    
    if cuenta_seleccionada:
        query_ingresos = query_ingresos.filter(Ingreso.cuenta == cuenta_seleccionada)
        query_gastos = query_gastos.filter(Gasto.cuenta == cuenta_seleccionada)
    
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
        query_ingresos = query_ingresos.filter(Ingreso.fecha >= fecha_desde_obj)
        query_gastos = query_gastos.filter(Gasto.fecha >= fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
        query_ingresos = query_ingresos.filter(Ingreso.fecha <= fecha_hasta_obj)
        query_gastos = query_gastos.filter(Gasto.fecha <= fecha_hasta_obj)
    
    # Ejecutar las consultas por separado
    ingresos = query_ingresos.all()
    gastos = query_gastos.all()
    
    # Combinar y ordenar los resultados
    all_transactions = []
    
    for ingreso in ingresos:
        all_transactions.append({
            'id': ingreso.id,
            'tipo': 'ingreso',
            'monto': ingreso.monto,
            'descripcion': ingreso.descripcion,
            'fecha': ingreso.fecha,
            'cuenta': ingreso.cuenta if ingreso.cuenta != 'none' else 'Efectivo'
        })
    
    for gasto in gastos:
        all_transactions.append({
            'id': gasto.id,
            'tipo': 'gasto',
            'monto': gasto.monto,
            'descripcion': gasto.descripcion,
            'fecha': gasto.fecha,
            'cuenta': gasto.cuenta if gasto.cuenta != 'none' else 'Efectivo'
        })
    
    # Ordenar por fecha (más reciente primero)
    all_transactions.sort(key=lambda x: x['fecha'], reverse=True)
    
    # Información de paginación
    total_movimientos = len(all_transactions)
    total_pages = (total_movimientos + per_page - 1) // per_page  # Ceil división
    
    # Limitar los resultados a la página actual
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    transactions_page = all_transactions[start_idx:end_idx] if start_idx < total_movimientos else []
    
    # Obtener información de billeteras para íconos y colores
    billeteras = Billetera.query.filter_by(profile_id=profile_id).all()
    billeteras_dict = {}
    for billetera in billeteras:
        billeteras_dict[billetera.nombre] = {
            'icono': billetera.icono or 'fas fa-wallet',
            'color': billetera.color or '#1e88e5'
        }
    
    hay_filtros_activos = bool(tipos_seleccionados or cuenta_seleccionada or fecha_desde or fecha_hasta)
    
    return render_template(
        'movimientos.html',
        profile=profile,
        transactions_page=transactions_page,
        billeteras=billeteras,
        billeteras_dict=billeteras_dict,
        page=page,
        total_pages=total_pages,
        total_movimientos=total_movimientos,
        tipos_seleccionados=tipos_seleccionados,
        cuenta_seleccionada=cuenta_seleccionada,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        hay_filtros_activos=hay_filtros_activos
    )

@app.route('/realizar_transferencia', methods=['POST'])
def realizar_transferencia():
    if 'profile_id' not in session:
        return redirect(url_for('login'))
    
    profile_id = session['profile_id']
    profile = Profile.query.get_or_404(profile_id)
    monto = request.form.get('monto', '')
    descripcion = request.form.get('descripcion', '')
    origen = request.form.get('origen', 'Efectivo')
    destino = request.form.get('destino', 'Efectivo')
    
    # Validaciones estrictas
    if not monto or not monto.strip():
        flash("El monto es obligatorio", "danger")
        return redirect(url_for('dashboard'))
    
    # Validar que la descripción no exceda cierto límite
    if descripcion and len(descripcion) > 200:
        flash("La descripción no puede exceder los 200 caracteres", "danger")
        return redirect(url_for('dashboard'))
    
    # Verificar que no sea la misma billetera
    if origen == destino:
        flash("No se puede transferir a la misma billetera", "danger")
        return redirect(url_for('dashboard'))
        
    # Validar que las billeteras existan para este usuario
    billetera_origen = Billetera.query.filter_by(profile_id=profile_id, nombre=origen).first()
    billetera_destino = Billetera.query.filter_by(profile_id=profile_id, nombre=destino).first()
    
    if not billetera_origen or not billetera_destino:
        flash("Una de las billeteras seleccionadas no existe o no te pertenece", "danger")
        return redirect(url_for('dashboard'))
    
    try:
        # Procesar el monto según la moneda del perfil
        if profile.moneda == 'COP':
            # Para COP usar valores enteros (sin centavos)
            monto_clean = monto.replace(".", "").replace(",", "")
            monto_valor = int(monto_clean)
        else:
            # Para otras monedas, preservar decimales
            monto_clean = monto.replace(".", "").replace(",", ".")
            monto_valor = float(monto_clean)
        
        # Verificar que el monto sea positivo
        if monto_valor <= 0:
            flash("El monto debe ser mayor que cero", "danger")
            return redirect(url_for('dashboard'))
        
        # Crear la transferencia en la base de datos
        nueva_transferencia = Transferencia(
            monto=monto_valor,
            descripcion=descripcion,
            origen=origen,
            destino=destino,
            profile_id=profile_id
        )
        
        # Crear el gasto de la cuenta origen
        gasto_origen = Gasto(
            monto=monto_valor,
            descripcion=f"Transferencia a {destino}" + (f": {descripcion}" if descripcion else ""),
            profile_id=profile_id,
            cuenta=origen
        )
        
        # Crear el ingreso en la cuenta destino
        ingreso_destino = Ingreso(
            monto=monto_valor,
            descripcion=f"Transferencia desde {origen}" + (f": {descripcion}" if descripcion else ""),
            profile_id=profile_id,
            cuenta=destino
        )
        
        # Guardar todo en la base de datos
        db.session.add(nueva_transferencia)
        db.session.add(gasto_origen)
        db.session.add(ingreso_destino)
        db.session.commit()
        
        flash(f"Transferencia de ${monto_valor:,.0f} de {origen} a {destino} realizada correctamente", "success")
    except ValueError:
        flash("El monto debe ser un valor numérico válido", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al realizar la transferencia: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))

# Ruta index: redirige a dashboard o login según la sesión
@app.route('/')
def index():
    if 'profile_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# ---------------------- ARRANQUE DE LA APLICACIÓN ----------------------
if __name__ == '__main__':
    # Configuración para desarrollo
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Servidor Flask con recarga automática")
    print(f"🌐 http://127.0.0.1:{port}")
    print("✨ Los cambios se recargarán automáticamente")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 50)
    
    app.run(
        host='127.0.0.1', 
        port=port, 
        debug=True,  # Habilita debug y recarga automática
        use_reloader=True,  # Recarga automática cuando cambian archivos Python
        use_debugger=True,  # Debugger web
        extra_files=['templates/', 'static/']  # Observar también templates y static
    )
