#!/usr/bin/env python3
"""
Script para eliminar billeteras predeterminadas de Nequi y Bancolombia
Solo debe quedar Efectivo como billetera predeterminada
"""

from app import app, db
from models import Billetera, Ingreso, Gasto

def cleanup_default_wallets():
    """Elimina las billeteras predeterminadas de Nequi y Bancolombia"""
    
    with app.app_context():
        print("🧹 Iniciando limpieza de billeteras predeterminadas...")
        
        # Buscar billeteras de Nequi y Bancolombia
        billeteras_a_eliminar = Billetera.query.filter(
            Billetera.nombre.in_(['Nequi', 'Bancolombia'])
        ).all()
        
        print(f"📋 Se encontraron {len(billeteras_a_eliminar)} billeteras para eliminar:")
        
        for billetera in billeteras_a_eliminar:
            print(f"   - {billetera.nombre} (ID: {billetera.id}, Perfil: {billetera.profile_id})")
        
        if not billeteras_a_eliminar:
            print("✅ No se encontraron billeteras de Nequi o Bancolombia para eliminar.")
            return
        
        # Confirmar eliminación
        respuesta = input("\n❓ ¿Deseas continuar con la eliminación? (s/N): ").lower().strip()
        
        if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada por el usuario.")
            return
        
        # Eliminar movimientos asociados primero
        total_movimientos_eliminados = 0
        for billetera in billeteras_a_eliminar:
            movimientos = Movimiento.query.filter_by(billetera_id=billetera.id).all()
            
            if movimientos:
                print(f"🗑️  Eliminando {len(movimientos)} movimientos de {billetera.nombre}...")
                for mov in movimientos:
                    db.session.delete(mov)
                total_movimientos_eliminados += len(movimientos)
        
        # Eliminar las billeteras
        total_billeteras_eliminadas = 0
        for billetera in billeteras_a_eliminar:
            print(f"🗑️  Eliminando billetera: {billetera.nombre}")
            db.session.delete(billetera)
            total_billeteras_eliminadas += 1
        
        # Confirmar cambios
        try:
            db.session.commit()
            print(f"\n✅ Limpieza completada exitosamente:")
            print(f"   📊 Billeteras eliminadas: {total_billeteras_eliminadas}")
            print(f"   📈 Movimientos eliminados: {total_movimientos_eliminados}")
            print(f"   💰 Solo queda 'Efectivo' como billetera predeterminada")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al realizar la limpieza: {str(e)}")
            return False
            
        return True

if __name__ == "__main__":
    print("🚀 Script de limpieza de billeteras predeterminadas")
    print("=" * 50)
    
    success = cleanup_default_wallets()
    
    if success:
        print("\n🎉 ¡Limpieza completada! Ahora solo 'Efectivo' es predeterminada.")
        print("💡 Las billeteras Nequi y Bancolombia se pueden crear manualmente.")
    else:
        print("\n❌ La limpieza no se pudo completar.")
