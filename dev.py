#!/usr/bin/env python3
"""
🚀 Servidor de desarrollo Flask con recarga automática
Similar a 'npm run dev' en Vite

Uso:
  python dev.py

Características:
- ✅ Recarga automática al cambiar archivos Python
- ✅ Recarga automática al cambiar templates HTML
- ✅ Modo debug activado para mejores errores
- ✅ Observa cambios en static/ también
"""

import os
import sys
from pathlib import Path

# Cambiar al directorio del proyecto
os.chdir(Path(__file__).parent)

# Configurar variables de entorno para desarrollo
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

def main():
    print("🚀 Servidor de desarrollo Flask")
    print("📁 Proyecto: Gestión de Dinero")
    print("🌐 URL: http://127.0.0.1:5000")
    print("✨ Recarga automática activada")
    print("🔧 Modo debug habilitado")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 50)
    
    # Importar y ejecutar la app Flask
    try:
        from app import app
        
        # Configurar Flask para desarrollo
        app.config['DEBUG'] = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        
        # Ejecutar con recarga automática
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=True,
            use_debugger=True,
            threaded=True,
            extra_files=[
                'templates/',
                'static/css/',
                'static/js/',
                'models.py',
                'config.py'
            ]
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except ImportError as e:
        print(f"❌ Error importando la aplicación: {e}")
        print("💡 Asegúrate de estar en el directorio correcto")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == '__main__':
    main()
