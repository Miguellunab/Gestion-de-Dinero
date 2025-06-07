from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from passlib.hash import pbkdf2_sha256

db = SQLAlchemy()

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    # Cambiar la longitud máxima del PIN para permitir el hash
    pin = db.Column(db.String(128), nullable=False)  # Cambiar de 4 a 128
    moneda = db.Column(db.String(3), default="COP", nullable=True)  # Temporalmente nullable=True
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)  # Temporalmente nullable=True
    ingresos = db.relationship('Ingreso', backref='profile', lazy=True)
    gastos = db.relationship('Gasto', backref='profile', lazy=True)
    billeteras = db.relationship('Billetera', backref='profile', lazy=True)
    login_attempts = db.Column(db.Integer, default=0, index=True)  # Añadir índice
    lockout_until = db.Column(db.DateTime, nullable=True, index=True)  # Añadir índice
    
    def is_locked(self):
        if self.lockout_until and self.lockout_until > datetime.now():
            return True
        return False
    
    def get_remaining_lockout_minutes(self):
        if not self.is_locked():
            return 0
        remaining = (self.lockout_until - datetime.now()).total_seconds() / 60
        return round(remaining)
    
    def set_pin(self, pin):
        self.pin = pbkdf2_sha256.hash(pin)
        
    def check_pin(self, pin):
        # Verificar si es un PIN en texto plano (probablemente solo 4 dígitos)
        if len(self.pin) == 4:
            # Si es texto plano, comparar directamente
            is_valid = (self.pin == pin)
            
            # Si coincide, actualizar a formato hasheado para futuras verificaciones
            if is_valid:
                self.pin = pbkdf2_sha256.hash(pin)
                db.session.commit()
            
            return is_valid
        else:
            # Si parece ser un hash, verificar con el método seguro
            try:
                return pbkdf2_sha256.verify(pin, self.pin)
            except ValueError:
                # Si hay error al verificar el hash, regresar False
                return False

class Billetera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    icono = db.Column(db.String(50), default="wallet") # Nombre del icono de FontAwesome
    color = db.Column(db.String(20), default="#6c757d") # Color en hexadecimal
    incluir_en_balance = db.Column(db.Boolean, default=True, nullable=False) # Nueva columna para incluir/excluir del balance
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)  # Cambiado a Float para soportar ambos tipos
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    cuenta = db.Column(db.String(50), default="Efectivo")  # Nuevo campo para la cuenta

class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)  # Cambiado a Float para soportar ambos tipos
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    cuenta = db.Column(db.String(50), default="Efectivo")  # Nuevo campo para la cuenta

class Transferencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    origen = db.Column(db.String(50), nullable=False)
    destino = db.Column(db.String(50), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)

class SalarioSemanal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Información de la semana (martes a lunes)
    fecha_inicio = db.Column(db.Date, nullable=False)  # Fecha del martes que inicia la semana
    fecha_fin = db.Column(db.Date, nullable=False)     # Fecha del lunes que termina la semana
    
    # Información de ingresos y deducciones
    salario_bruto = db.Column(db.Float, nullable=False, default=0.0)  # Salario antes de deducciones
    impuestos = db.Column(db.Float, nullable=False, default=0.0)      # Impuestos deducidos
    housing = db.Column(db.Float, nullable=False, default=0.0)        # Housing deducido
    salario_neto = db.Column(db.Float, nullable=False, default=0.0)   # Salario después de deducciones
    
    # Gastos de la semana
    gastos_comida = db.Column(db.Float, nullable=False, default=0.0)     # Gastos en comida
    gastos_variables = db.Column(db.Float, nullable=False, default=0.0)  # Otros gastos variables
    
    # Balance final de la semana
    balance_semanal = db.Column(db.Float, nullable=False, default=0.0)   # Balance final (salario_neto - gastos_totales)
    
    # Metadatos
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    
    # Relación
    profile = db.relationship('Profile', backref='salarios_semanales')
    
    def calcular_totales(self):
        """Calcula automáticamente el salario neto y balance semanal"""
        self.salario_neto = self.salario_bruto - self.impuestos - self.housing
        gastos_totales = self.gastos_comida + self.gastos_variables
        self.balance_semanal = self.salario_neto - gastos_totales
    
    def __repr__(self):
        return f'<SalarioSemanal {self.fecha_inicio} - {self.fecha_fin}>'
