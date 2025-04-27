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
