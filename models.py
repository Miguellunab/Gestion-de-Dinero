from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    pin = db.Column(db.String(4), nullable=False)
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

class Billetera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    icono = db.Column(db.String(50), default="wallet") # Nombre del icono de FontAwesome
    color = db.Column(db.String(20), default="#6c757d") # Color en hexadecimal
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    cuenta = db.Column(db.String(50), default="Efectivo")  # Nuevo campo para la cuenta

class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'), nullable=False)
    cuenta = db.Column(db.String(50), default="Efectivo")  # Nuevo campo para la cuenta
