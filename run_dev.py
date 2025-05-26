#!/usr/bin/env python3
"""
Script simple de desarrollo con livereload
Ejecuta Flask con recarga automática como Vite
"""

import subprocess
import sys
import time
from pathlib import Path
import os

def main():
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🚀 Iniciando servidor de desarrollo con livereload...")
    print("📁 Directorio: " + str(project_dir))
    print("🌐 URL: http://127.0.0.1:5000")
    print("✨ Los cambios se recargarán automáticamente")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 50)
    
    # Comando para ejecutar con livereload
    cmd = [
        sys.executable, "-m", "livereload", 
        "--port", "35729",  # Puerto para livereload
        "--host", "127.0.0.1",
        "."  # Directorio a observar
    ]
    
    try:
        # Ejecutar livereload en segundo plano
        livereload_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Esperar un momento para que livereload se inicie
        time.sleep(2)
        
        # Ahora ejecutar Flask
        print("🔧 Iniciando Flask...")
        flask_cmd = [sys.executable, "app.py"]
        flask_process = subprocess.Popen(flask_cmd)
        
        # Esperar a que terminen los procesos
        flask_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
        try:
            livereload_process.terminate()
            flask_process.terminate()
        except:
            pass
        print("✅ Servidor detenido")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
