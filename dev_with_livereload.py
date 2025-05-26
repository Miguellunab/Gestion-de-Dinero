#!/usr/bin/env python3
"""
Servidor de desarrollo integrado con Flask + Livereload
Similar a Vite para desarrollo web
"""

from livereload import Server
from livereload.watcher import Watcher
import subprocess
import threading
import time
import os
import sys
from pathlib import Path

class FlaskLiveReloadServer:
    def __init__(self):
        self.flask_process = None
        self.project_dir = Path(__file__).parent
        
    def start_flask(self):
        """Inicia el servidor Flask"""
        os.chdir(self.project_dir)
        
        # Comando para ejecutar Flask
        cmd = [sys.executable, 'app.py']
        
        try:
            self.flask_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Leer output en tiempo real
            for line in iter(self.flask_process.stdout.readline, ''):
                if line.strip():
                    print(f"🐍 Flask: {line.strip()}")
                    
        except Exception as e:
            print(f"❌ Error iniciando Flask: {e}")
    
    def restart_flask(self):
        """Reinicia el servidor Flask"""
        print("🔄 Reiniciando Flask...")
        if self.flask_process:
            self.flask_process.terminate()
            self.flask_process.wait()
        
        # Pequeña pausa antes de reiniciar
        time.sleep(1)
        
        # Reiniciar en un nuevo hilo
        flask_thread = threading.Thread(target=self.start_flask, daemon=True)
        flask_thread.start()
        
        print("✅ Flask reiniciado")
    
    def run(self):
        """Ejecuta el servidor de desarrollo"""
        print("🚀 Servidor de desarrollo Flask + LiveReload")
        print("=" * 50)
        
        # Iniciar Flask en un hilo separado
        print("🐍 Iniciando Flask...")
        flask_thread = threading.Thread(target=self.start_flask, daemon=True)
        flask_thread.start()
        
        # Esperar a que Flask se inicie
        time.sleep(3)
        
        # Configurar livereload
        server = Server()
        
        # Observar archivos Python y reiniciar Flask
        def on_python_change():
            self.restart_flask()
            
        server.watch('*.py', func=on_python_change, delay=0.5)
        server.watch('models.py', func=on_python_change, delay=0.5)
        server.watch('config.py', func=on_python_change, delay=0.5)
        
        # Observar templates, CSS, JS para recarga de navegador
        server.watch('templates/*.html', delay=0.3)
        server.watch('static/css/*.css', delay=0.3)
        server.watch('static/js/*.js', delay=0.3)
        server.watch('static/images/*', delay=0.5)
        
        print("📁 Observando cambios en:")
        print("   🐍 Python (reinicia Flask): *.py")
        print("   🎨 Templates (recarga navegador): templates/*.html")
        print("   🎭 CSS (recarga estilos): static/css/*.css")
        print("   ⚡ JavaScript: static/js/*.js")
        print("   🖼️ Imágenes: static/images/*")
        print("")
        print("🌐 Flask: http://127.0.0.1:5000")
        print("🔄 LiveReload: http://127.0.0.1:35729")
        print("✨ Recarga automática activada")
        print("🛑 Ctrl+C para detener")
        print("=" * 50)
        
        try:
            # Servir livereload
            server.serve(
                port=35729,
                host='127.0.0.1',
                restart_delay=0.5
            )
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo servidor...")
            if self.flask_process:
                self.flask_process.terminate()
            print("✅ Servidor detenido")

def main():
    server = FlaskLiveReloadServer()
    server.run()

if __name__ == '__main__':
    main()
