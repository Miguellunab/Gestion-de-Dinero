#!/usr/bin/env python3
"""
Script de desarrollo con livereload para Flask
Similar a Vite, recarga automáticamente cuando cambian los archivos
"""

import os
import sys
from livereload import Server, shell
from pathlib import Path

# Asegurar que estamos en el directorio correcto
os.chdir(Path(__file__).parent)

def main():
    # Crear el servidor de livereload
    server = Server()
    
    # Observar archivos Python
    server.watch('*.py', shell('python app.py', shell=True))
    server.watch('models.py', shell('python app.py', shell=True))
    server.watch('config.py', shell('python app.py', shell=True))
    
    # Observar templates HTML
    server.watch('templates/*.html')
    
    # Observar archivos CSS
    server.watch('static/css/*.css')
    
    # Observar archivos JavaScript
    server.watch('static/js/*.js')
    
    # Observar archivos de imagen
    server.watch('static/images/*')
    
    print("🚀 Servidor de desarrollo con livereload iniciado!")
    print("📁 Observando cambios en:")
    print("   - Archivos Python (*.py)")
    print("   - Templates (templates/*.html)")
    print("   - CSS (static/css/*.css)")
    print("   - JavaScript (static/js/*.js)")
    print("   - Imágenes (static/images/*)")
    print("")
    print("🌐 Abre tu navegador en: http://127.0.0.1:5500")
    print("✨ Los cambios se recargarán automáticamente")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 50)
    
    # Iniciar el servidor en el puerto 5500 (diferente al Flask normal)
    try:
        server.serve(
            port=5500,
            host='127.0.0.1',
            restart_delay=1,  # Esperar 1 segundo antes de reiniciar
            open_url_delay=2   # Esperar 2 segundos antes de abrir el navegador
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
