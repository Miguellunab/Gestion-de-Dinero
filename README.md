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
- Para Vercel, la escritura en disco persistente no funciona (filesystem read-only). Usa Postgres externo (Neon recomendado).

## Despliegue en Vercel con Postgres (Neon)

1. Crea la base en Neon (región cercana a Vercel, US East/Washington es OK).
2. Obtén la cadena pooled (formato `postgres://...`).
3. En Vercel → Project Settings → Environment Variables:
	- `DATABASE_URL` = cadena (la app convierte `postgres://` a `postgresql+psycopg2://`).
	- `SECRET_KEY` = valor estable y seguro.
4. Redeploy. La app usará Postgres y deshabilitará el pool persistente (NullPool) para serverless.
5. Ejecuta migraciones desde tu máquina local apuntando a la URL remota:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://USER:PASSWORD@HOST/DBNAME?sslmode=require"
$env:FLASK_APP = "app.py"; ./env/Scripts/python.exe -m flask db upgrade
```

### Fallback temporal (solo demo)
Si no defines `DATABASE_URL` en Vercel, se usará SQLite en `/tmp/finanzas.db` (NO persistente).

### Variables de entorno máximas
Vercel permite hasta ~64 KB combinados de variables por despliegue; mantén las credenciales compactas.
