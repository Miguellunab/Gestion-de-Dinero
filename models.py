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
