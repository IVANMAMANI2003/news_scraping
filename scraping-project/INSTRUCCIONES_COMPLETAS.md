# 📰 Sistema Completo de Scraping de Noticias con PostgreSQL

## 🎯 Resumen del Proyecto

Has creado un sistema completo de scraping de noticias que:
- ✅ Extrae noticias de múltiples fuentes
- ✅ Almacena datos en PostgreSQL automáticamente
- ✅ Detecta duplicados por URL
- ✅ Se ejecuta de forma programada
- ✅ Mantiene logs detallados

## 📁 Archivos Creados

### 🔧 Configuración y Base de Datos
- `setup_database.py` - Configura PostgreSQL y crea la tabla
- `config/database.py` - Configuración de la base de datos
- `env_example.txt` - Variables de entorno (copia a .env)

### 🕷️ Pipelines de Scrapy
- `pepelines/clean_pipeline.py` - Limpieza de datos (ya existía)
- `pepelines/postgres_pipeline.py` - **NUEVO** - Guarda en PostgreSQL

### 🕷️ Spiders de Scrapy
- `spiders/losandes_scrapy_spider.py` - **NUEVO** - Spider para Los Andes
- `spiders/pachamamaradio_spider.py` - Spider existente (de Colab)
- `spiders/punonoticias_spider.py` - Spider existente (de Colab)
- `spiders/sinfronteras_spider.py` - Spider existente (de Colab)

### 🚀 Scripts de Ejecución
- `run_scraping.py` - **NUEVO** - Ejecuta todos los spiders
- `scheduler.py` - **NUEVO** - Programador automático
- `test_scraping.py` - **NUEVO** - Pruebas del sistema
- `install_and_setup.py` - **NUEVO** - Instalación automática

### 🔄 Utilidades
- `convert_colab_to_scrapy.py` - **NUEVO** - Convierte spiders de Colab
- `README.md` - **NUEVO** - Documentación completa

## 🚀 Instrucciones de Instalación

### 1. Instalar Dependencias
```bash
pip install -r requeriments.txt
```

### 2. Configurar PostgreSQL
```bash
# Crear base de datos y tabla
python setup_database.py
```

### 3. Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp env_example.txt .env

# Editar con tus credenciales
# DB_PASSWORD=tu_contraseña_de_postgresql
```

### 4. Instalación Automática (Recomendado)
```bash
python install_and_setup.py
```

## 🎮 Cómo Usar el Sistema

### Ejecución Manual
```bash
# Ejecutar todos los spiders
python run_scraping.py

# Ejecutar un spider específico
scrapy crawl losandes
scrapy crawl pachamamaradio
scrapy crawl punonoticias
scrapy crawl sinfronteras
```

### Ejecución Automática
```bash
# Programador que ejecuta cada 6 horas
python scheduler.py
```

### Pruebas
```bash
# Verificar que todo funciona
python test_scraping.py
```

## 🗄️ Estructura de la Base de Datos

La tabla `noticias` tiene estos campos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | SERIAL | Clave primaria |
| titulo | TEXT | Título de la noticia |
| fecha | TIMESTAMP | Fecha de publicación |
| resumen | TEXT | Resumen de la noticia |
| contenido | TEXT | Contenido completo |
| categoria | VARCHAR(100) | Categoría |
| autor | VARCHAR(200) | Autor |
| tags | TEXT | Tags separados por comas |
| url | TEXT UNIQUE | URL única (evita duplicados) |
| fecha_extraccion | TIMESTAMP | Cuándo se extrajo |
| caracteres_contenido | INTEGER | Número de caracteres |
| palabras_contenido | INTEGER | Número de palabras |
| imagenes | TEXT | URLs de imágenes (JSON) |
| fuente | VARCHAR(100) | Fuente de la noticia |
| created_at | TIMESTAMP | Cuándo se guardó en BD |

## 🔧 Configuración Avanzada

### Modificar Horarios de Scraping
Edita `scheduler.py`:
```python
# Ejecutar cada 2 horas
schedule.every(2).hours.do(run_scraping_job)

# Ejecutar solo en días laborables
schedule.every().monday.at("09:00").do(run_scraping_job)
```

### Ajustar Delays entre Requests
Edita `settings.py`:
```python
DOWNLOAD_DELAY = 2  # 2 segundos entre requests
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # Randomizar ±50%
```

## 📊 Monitoreo y Consultas

### Ver Logs
```bash
# Logs del programador
tail -f scraping_scheduler.log

# Logs de Scrapy
scrapy crawl losandes -L INFO
```

### Consultar Base de Datos
```sql
-- Ver todas las noticias
SELECT * FROM noticias ORDER BY created_at DESC;

-- Contar por fuente
SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente;

-- Noticias de hoy
SELECT * FROM noticias WHERE DATE(created_at) = CURRENT_DATE;

-- Buscar por categoría
SELECT titulo, fecha FROM noticias WHERE categoria = 'Deportes';
```

## 🚨 Solución de Problemas

### Error de Conexión a PostgreSQL
1. Verifica que PostgreSQL esté ejecutándose
2. Revisa las credenciales en `.env`
3. Asegúrate de que la base de datos `noticias` existe

### Spiders No Encuentran Datos
1. Verifica que los selectores CSS sean correctos
2. Revisa si las páginas han cambiado su estructura
3. Aumenta el delay entre requests

### Error de Permisos
```bash
# En Windows, ejecutar como administrador
# En Linux/Mac
chmod +x *.py
```

## 🔄 Flujo de Trabajo

1. **Configuración Inicial**: `python install_and_setup.py`
2. **Primera Ejecución**: `python run_scraping.py`
3. **Verificar Datos**: Consultar la base de datos
4. **Configurar Automatización**: `python scheduler.py`
5. **Monitoreo**: Revisar logs y datos periódicamente

## 📈 Características del Sistema

- ✅ **Detección de Duplicados**: Por URL única
- ✅ **Limpieza Automática**: Fechas, contenido, estadísticas
- ✅ **Logging Detallado**: Para monitoreo y debugging
- ✅ **Configuración Flexible**: Delays, horarios, selectores
- ✅ **Múltiples Formatos**: PostgreSQL + JSON + CSV
- ✅ **Escalable**: Fácil agregar nuevas fuentes

## 🎯 Próximos Pasos Sugeridos

1. **Convertir Spiders de Colab**: Usar `convert_colab_to_scrapy.py`
2. **Ajustar Selectores**: Revisar cada spider según el sitio
3. **Configurar Horarios**: Ajustar según tus necesidades
4. **Monitorear Rendimiento**: Revisar logs regularmente
5. **Agregar Nuevas Fuentes**: Crear spiders adicionales

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en `scraping_scheduler.log`
2. Ejecuta `python test_scraping.py` para diagnóstico
3. Verifica la conexión a PostgreSQL
4. Revisa que los spiders tengan los selectores correctos

¡Tu sistema de scraping está listo para funcionar! 🎉
