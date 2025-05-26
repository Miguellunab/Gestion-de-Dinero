#!/usr/bin/env python3
"""
Servidor de desarrollo con livereload completo
Recarga automáticamente Python, HTML, CSS y JS como Vite
"""

from livereload import Server
import os
from pathlib import Path

def main():
    # Cambiar al directorio del proyecto
    os.chdir(Path(__file__).parent)
    
    # Crear servidor livereload
    server = Server()
    
    # Configurar qué archivos observar y qué hacer cuando cambien
    print("🚀 Configurando livereload...")
    
    # Para archivos Python: reiniciar la aplicación Flask
    server.watch('*.py')
    server.watch('models.py')
    server.watch('config.py')
    
    # Para templates: solo recargar el navegador
    server.watch('templates/*.html')
    
    # Para CSS: recargar estilos
    server.watch('static/css/*.css')
    
    # Para JavaScript: recargar scripts
    server.watch('static/js/*.js')
    
    # Para imágenes: recargar página
    server.watch('static/images/*')
    
    print("✅ Livereload configurado")
    print("📁 Observando:")
    print("   🐍 Python: *.py")
    print("   🎨 Templates: templates/*.html")
    print("   🎭 CSS: static/css/*.css") 
    print("   ⚡ JavaScript: static/js/*.js")
    print("   🖼️ Imágenes: static/images/*")
    print("")
    print("🌐 Abriendo en: http://127.0.0.1:5500")
    print("✨ Recarga automática activada")
    print("🛑 Ctrl+C para detener")
    print("=" * 50)
    
    # Servir la aplicación Flask a través de livereload
    server.serve(
        port=5500,
        host='127.0.0.1',
        restart_delay=0.5,  # Medio segundo de delay
        open_url='http://127.0.0.1:5500'  # Abrir automáticamente
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido")
    except Exception as e:
        print(f"❌ Error: {e}")
