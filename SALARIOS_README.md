# Sistema de Gestión de Salarios Semanales

## Descripción
El sistema de gestión de salarios semanales permite a los usuarios administrar sus ingresos y gastos en ciclos semanales que van de **martes a lunes**. Esta funcionalidad es ideal para personas que reciben pagos semanales y quieren un control detallado de sus finanzas.

## Características Implementadas

### 1. **Modelo de Datos (SalarioSemanal)**
- **Rango semanal**: Automáticamente calcula la semana de martes a lunes
- **Salario bruto**: Ingreso total antes de deducciones
- **Deducciones automáticas**: Impuestos y housing
- **Gastos semanales**: Comida y gastos variables
- **Cálculos automáticos**: Salario neto y balance semanal

### 2. **Interfaz de Usuario**
- **Dashboard integrado**: Botón de acceso directo desde el dashboard principal
- **Página dedicada**: Interfaz completa para gestión de salarios
- **Estadísticas generales**: Promedios y totales automáticos
- **Diseño responsivo**: Compatible con móviles y escritorio

### 3. **Funcionalidades CRUD**
- **Agregar**: Registro de nuevos salarios semanales
- **Editar**: Modificación de registros existentes
- **Eliminar**: Eliminación con confirmación
- **Visualizar**: Vista detallada de todos los registros

## Cómo Usar

### Acceso
1. Desde el dashboard principal, hacer clic en el botón con ícono de salario (💰)
2. Esto llevará a la página de gestión de salarios semanales

### Agregar un Nuevo Salario
1. Hacer clic en "Registrar Salario" en la tarjeta azul
2. Completar el formulario:
   - **Fecha de referencia**: Cualquier día de la semana (se calculará automáticamente el rango martes-lunes)
   - **Salario bruto**: Ingreso total antes de deducciones
   - **Deducciones/Impuestos**: Montos deducidos por impuestos
   - **Deducción Vivienda**: Housing u otros gastos de vivienda
   - **Gastos Comida**: Gastos en alimentación de la semana
   - **Gastos Variables**: Otros gastos diversos

3. Los cálculos se realizan automáticamente:
   - **Salario Neto** = Salario Bruto - Impuestos - Housing
   - **Balance Semanal** = Salario Neto - Gastos Comida - Gastos Variables

### Editar un Salario Existente
1. Hacer clic en el botón de editar (✏️) en cualquier tarjeta de salario
2. Modificar los campos necesarios
3. Guardar los cambios

### Eliminar un Salario
1. Hacer clic en el botón de eliminar (🗑️) en cualquier tarjeta de salario
2. Confirmar la eliminación

## Estadísticas Automáticas
La página muestra automáticamente:
- **Número total** de semanas registradas
- **Salario bruto promedio** de todas las semanas
- **Salario neto promedio** de todas las semanas

## Tecnologías Utilizadas
- **Backend**: Flask + SQLAlchemy
- **Frontend**: Bootstrap 5 + JavaScript vanilla
- **Base de datos**: SQLite con migraciones automáticas
- **Seguridad**: CSRF protection integrado

## Estructura de Archivos Modificados/Creados

### Nuevos Archivos
- `templates/gestion_salarios.html` - Interfaz principal
- `crear_datos_salario_prueba_v2.py` - Script para datos de prueba

### Archivos Modificados
- `models.py` - Agregado modelo SalarioSemanal
- `app.py` - Nuevas rutas y funciones auxiliares
- `templates/dashboard.html` - Botón de acceso
- `static/css/dashboard.css` - Estilos para el botón

## Características Técnicas
- **Validación de duplicados**: No permite registrar dos salarios para la misma semana
- **Cálculos automáticos**: Totales actualizados en tiempo real
- **Formato de fecha inteligente**: Rangos de semana legibles
- **Manejo de errores**: Mensajes informativos para el usuario
- **Diseño consistente**: Integrado con el estilo existente de la aplicación

## Próximas Mejoras Posibles
- Gráficos de tendencias salariales
- Exportación a Excel/PDF
- Comparativas mensuales
- Alertas de gastos excesivos
- Integración con categorías de gastos existentes
