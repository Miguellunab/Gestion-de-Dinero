# Gestión de Dinero (Flask)

Aplicación web en Flask para gestionar ingresos, gastos, billeteras y salarios semanales.

## Requisitos

- Windows 10/11
- Python 3.12 (recomendado 3.12.10)
- Git (opcional si clonas el repo manualmente)

## Puesta en marcha (Windows PowerShell)

Ya dejé el entorno listo en esta carpeta usando un entorno virtual `env` y dependencias instaladas. Si necesitas rehacerlo desde cero, sigue estos pasos:

```powershell
# 1) Instalar Python 3.12 (si no lo tienes)
winget install -e --id Python.Python.3.12

# 2) Crear el entorno virtual (dentro de la carpeta del proyecto)
py -3.12 -m venv env

# 3) Actualizar pip e instalar dependencias
./env/Scripts/python.exe -m pip install --upgrade pip
./env/Scripts/python.exe -m pip install -r requirements.txt

# 4) Ejecutar el servidor de desarrollo
./env/Scripts/python.exe app.py
```

El servidor quedará disponible en:

- http://127.0.0.1:5000

Para detenerlo, presiona Ctrl+C en la terminal.

## Estructura relevante

- `app.py`: aplicación Flask y rutas principales.
- `models.py`: modelos SQLAlchemy (SQLite por defecto).
- `config.py`: configuración (usa `.env` si existe). Base de datos en `instance/finanzas.db`.
- `migrations/`: scripts de migraciones con Alembic/Flask-Migrate.
- `templates/` y `static/`: frontend (Jinja, CSS, JS).
- `run_dev.py`: alternativa con livereload para autorecarga adicional.

## Variables de entorno (opcional)

Crea un archivo `.env` en la raíz para sobrescribir valores por defecto. Ejemplo:

```
# .env
SECRET_KEY=pon_aqui_una_clave_segura
# SQLALCHEMY_DATABASE_URI=sqlite:///ruta/personalizada.db
```

Si no defines `SECRET_KEY`, en desarrollo se genera una aleatoria.

## Migraciones de base de datos

Si cambias modelos, puedes aplicar migraciones:

```powershell
# Crear migración (después de cambios en models.py)
./env/Scripts/python.exe -m flask db migrate -m "mi cambio"

# Aplicar migraciones
./env/Scripts/python.exe -m flask db upgrade
```

Asegúrate de exportar FLASK_APP si usas comandos flask directamente:

```powershell
$env:FLASK_APP = "app.py"; ./env/Scripts/python.exe -m flask run
```

## Desarrollo con livereload (opcional)

```powershell
./env/Scripts/python.exe run_dev.py
```

## Notas

- Este entorno usa SQLite local por defecto, sin necesidad de instalar PostgreSQL.
- Para producción, usa un servidor WSGI (por ejemplo, `gunicorn`) y configura variables de entorno seguras.
