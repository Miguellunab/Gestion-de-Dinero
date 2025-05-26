#!/usr/bin/env python3
"""Script simple para eliminar billeteras predeterminadas"""

from app import app, db
from models import Billetera

with app.app_context():
    print("🧹 Eliminando billeteras de Nequi y Bancolombia...")
    
    # Eliminar Nequi
    nequi = Billetera.query.filter_by(nombre='Nequi').all()
    for wallet in nequi:
        print(f"Eliminando Nequi ID: {wallet.id}")
        db.session.delete(wallet)
    
    # Eliminar Bancolombia
    bancolombia = Billetera.query.filter_by(nombre='Bancolombia').all()
    for wallet in bancolombia:
        print(f"Eliminando Bancolombia ID: {wallet.id}")
        db.session.delete(wallet)
    
    # Guardar cambios
    db.session.commit()
    print("✅ Listo! Solo queda Efectivo como predeterminada")
