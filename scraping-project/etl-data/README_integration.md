# Scripts de Integración de Noticias

## 📁 Archivos Disponibles

### 1. `create_clean_table.py`
**Propósito**: Crear la tabla `noticias_limpia` y cargar datos procesados iniciales.

**Uso**:
```bash
python create_clean_table.py
```

**Funciones**:
- Crea la tabla `noticias_limpia` con estructura optimizada
- Carga datos del archivo `data_etl_final_20251014_063022.csv`
- Aplica validaciones de tipos de datos
- Maneja duplicados por URL

### 2. `integrate_new_news.py`
**Propósito**: Integrar nuevas noticias desde archivos CSV con filtro de duplicados.

**Uso**:
```bash
python integrate_new_news.py
```

**Funciones**:
- Busca automáticamente archivos CSV nuevos en el directorio
- Filtra noticias duplicadas por URL
- Aplica transformaciones ETL básicas si es necesario
- Inserta solo noticias nuevas en `noticias_limpia`

## 🔄 Flujo de Trabajo Recomendado

### Paso 1: Configuración Inicial
```bash
# Crear tabla y cargar datos iniciales
python create_clean_table.py
```

### Paso 2: Integración Continua
```bash
# Integrar nuevas noticias (ejecutar cada vez que tengas nuevos datos)
python integrate_new_news.py
```

## 📊 Características de los Scripts

### Filtro de Duplicados
- **Método**: Comparación por URL
- **Ventaja**: Evita noticias duplicadas automáticamente
- **Eficiencia**: Consulta rápida de URLs existentes

### Transformaciones ETL
- **Básicas**: Aplicadas automáticamente si faltan columnas
- **Avanzadas**: Requieren procesamiento previo con `data-normalizer.py`

### Validación de Datos
- **Fechas**: Conversión segura a tipos de fecha PostgreSQL
- **Números**: Validación de campos numéricos
- **Textos**: Limpieza de caracteres especiales

## 📈 Monitoreo

### Verificación Automática
- Conteo de registros totales
- Distribución por fuente
- Noticias más recientes
- Estadísticas de categorías

### Logs de Progreso
- Procesamiento por lotes
- Conteo de registros insertados
- Errores detallados

## 🚀 Casos de Uso

### 1. Carga Inicial
```bash
# Primera vez - crear tabla y cargar datos base
python create_clean_table.py
```

### 2. Actualización Diaria
```bash
# Después de scraping - agregar nuevas noticias
python integrate_new_news.py
```

### 3. Migración de Datos
```bash
# Migrar datos de diferentes fuentes
# Colocar archivos CSV en el directorio etl-data
python integrate_new_news.py
```

## ⚠️ Consideraciones

### Archivos Soportados
- **Formato**: CSV con encoding UTF-8
- **Columnas mínimas**: titulo, url, fuente
- **Ubicación**: Directorio `etl-data/`

### Rendimiento
- **Lotes**: Procesamiento en lotes de 50-100 registros
- **Memoria**: Optimizado para archivos grandes
- **Base de datos**: Usa transacciones para consistencia

### Seguridad
- **Duplicados**: Prevención automática
- **Transacciones**: Rollback en caso de error
- **Validación**: Verificación de tipos de datos
