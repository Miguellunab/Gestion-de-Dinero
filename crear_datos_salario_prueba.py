"""
Script para crear datos de prueba de salarios semanales
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Profile, SalarioSemanal
from datetime import datetime, timedelta

def crear_datos_prueba():
    with app.app_context():
        # Buscar el primer perfil disponible
        profile = Profile.query.first()
        if not profile:
            print("No hay perfiles disponibles. Crea un perfil primero.")
            return
        
        print(f"Creando datos de prueba para el perfil: {profile.name}")
        
        # Crear algunas semanas de salario de ejemplo
        datos_salario = [            {
                'fecha_referencia': datetime(2025, 6, 3).date(),  # Martes pasado
                'salario_bruto': 1200000,
                'impuestos': 150000,
                'housing': 200000,
                'gastos_comida': 120000,
                'gastos_variables': 80000
            },
            {
                'fecha_referencia': datetime(2025, 5, 27).date(),  # Semana anterior
                'salario_bruto': 1200000,
                'impuestos': 150000,
                'housing': 200000,
                'gastos_comida': 110000,
                'gastos_variables': 70000
            },
            {
                'fecha_referencia': datetime(2025, 5, 20).date(),  # Hace 2 semanas
                'salario_bruto': 1150000,
                'impuestos': 140000,
                'housing': 200000,
                'gastos_comida': 100000,
                'gastos_variables': 60000
            }
        ]
        
        for datos in datos_salario:
            # Calcular el rango de la semana salarial (martes a lunes)
            fecha_ref = datos['fecha_referencia']
            dias_hasta_martes = (fecha_ref.weekday() - 1) % 7
            fecha_inicio = fecha_ref - timedelta(days=dias_hasta_martes)
            fecha_fin = fecha_inicio + timedelta(days=6)
            
            # Verificar si ya existe
            salario_existente = SalarioSemanal.query.filter_by(
                profile_id=profile.id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            ).first()
            
            if not salario_existente:                nuevo_salario = SalarioSemanal(
                    profile_id=profile.id,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    salario_bruto=datos['salario_bruto'],
                    impuestos=datos['impuestos'],
                    housing=datos['housing'],
                    gastos_comida=datos['gastos_comida'],
                    gastos_variables=datos['gastos_variables']
                )
                
                # Calcular automáticamente el salario neto y balance
                nuevo_salario.calcular_totales()
                
                db.session.add(nuevo_salario)
                print(f"✓ Creado salario para semana {fecha_inicio} - {fecha_fin}")
            else:
                print(f"× Ya existe salario para semana {fecha_inicio} - {fecha_fin}")
        
        try:
            db.session.commit()
            print("✓ Datos de prueba creados exitosamente")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error al crear datos de prueba: {e}")

if __name__ == "__main__":
    crear_datos_prueba()
