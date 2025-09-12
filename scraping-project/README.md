# 📰 Sistema de Scraping de Noticias

Este proyecto realiza scraping automático de noticias de diferentes fuentes y las almacena en una base de datos PostgreSQL.

## 🚀 Características

- **Scraping automático** de múltiples fuentes de noticias
- **Almacenamiento en PostgreSQL** con detección de duplicados
- **Programación de tareas** para ejecución automática
- **Pipeline de limpieza** de datos
- **Logging detallado** para monitoreo

## 📋 Fuentes de Noticias

- Los Andes
- Pachamama Radio
- Puno Noticias
- Sin Fronteras

## 🗄️ Estructura de la Base de Datos

La tabla `noticias` contiene los siguientes campos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | SERIAL | Clave primaria |
| titulo | TEXT | Título de la noticia |
| fecha | TIMESTAMP | Fecha de publicación |
| resumen | TEXT | Resumen de la noticia |
| contenido | TEXT | Contenido completo |
| categoria | VARCHAR(100) | Categoría de la noticia |
| autor | VARCHAR(200) | Autor de la noticia |
| tags | TEXT | Tags asociados |
| url | TEXT | URL única de la noticia |
| fecha_extraccion | TIMESTAMP | Fecha de extracción |
| caracteres_contenido | INTEGER | Número de caracteres |
| palabras_contenido | INTEGER | Número de palabras |
| imagenes | TEXT | URLs de imágenes |
| fuente | VARCHAR(100) | Fuente de la noticia |
| created_at | TIMESTAMP | Fecha de creación en BD |

## 🛠️ Instalación

### 1. Instalar dependencias

```bash
pip install -r requeriments.txt
```

### 2. Configurar PostgreSQL

1. Instalar PostgreSQL en tu sistema
2. Crear la base de datos:

```bash
python setup_database.py
```

### 3. Configurar variables de entorno

Copia el archivo `env_example.txt` a `.env` y modifica las credenciales:

```bash
cp env_example.txt .env
```

Edita el archivo `.env` con tus credenciales de PostgreSQL:

```
DB_HOST=localhost
DB_NAME=noticias
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_PORT=5432
```

## 🚀 Uso

### Ejecutar scraping manual

```bash
# Ejecutar todos los spiders
python run_scraping.py

# O ejecutar un spider específico
scrapy crawl losandes
scrapy crawl pachamamaradio
scrapy crawl punonoticias
scrapy crawl sinfronteras
```

### Ejecutar con programador automático

```bash
python scheduler.py
```

El programador ejecutará el scraping:
- Cada 6 horas
- Diario a las 06:00, 12:00 y 18:00

## 📁 Estructura del Proyecto

```
scraping-project/
├── spiders/                 # Spiders de Scrapy
│   ├── base_spider.py      # Spider base
│   ├── losandes_spider.py  # Spider Los Andes
│   ├── pachamamaradio_spider.py
│   ├── punonoticias_spider.py
│   └── sinfronteras_spider.py
├── pepelines/              # Pipelines de procesamiento
│   ├── clean_pipeline.py   # Limpieza de datos
│   └── postgres_pipeline.py # Guardado en PostgreSQL
├── config/                 # Configuraciones
│   └── database.py         # Config de BD
├── data/                   # Datos exportados
├── run_scraping.py         # Script principal
├── scheduler.py            # Programador de tareas
├── setup_database.py       # Configuración de BD
└── settings.py             # Configuración de Scrapy
```

## 🔧 Configuración Avanzada

### Modificar horarios de scraping

Edita el archivo `scheduler.py` para cambiar los horarios:

```python
# Ejecutar cada 2 horas
schedule.every(2).hours.do(run_scraping_job)

# Ejecutar solo en días laborables
schedule.every().monday.at("09:00").do(run_scraping_job)
```

### Configurar delays entre requests

Modifica `settings.py`:

```python
DOWNLOAD_DELAY = 2  # 2 segundos entre requests
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # Randomizar ±50%
```

## 📊 Monitoreo

### Ver logs

```bash
# Logs del programador
tail -f scraping_scheduler.log

# Logs de Scrapy
scrapy crawl losandes -L INFO
```

### Consultar base de datos

```sql
-- Ver todas las noticias
SELECT * FROM noticias ORDER BY created_at DESC;

-- Contar noticias por fuente
SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente;

-- Noticias de hoy
SELECT * FROM noticias WHERE DATE(created_at) = CURRENT_DATE;
```

## 🚨 Solución de Problemas

### Error de conexión a PostgreSQL

1. Verifica que PostgreSQL esté ejecutándose
2. Revisa las credenciales en `.env`
3. Asegúrate de que la base de datos `noticias` existe

### Error de permisos

```bash
# En Windows, ejecutar como administrador
# En Linux/Mac, verificar permisos de archivos
chmod +x *.py
```

### Spiders no encuentran datos

1. Verifica que los selectores CSS/XPath sean correctos
2. Revisa si las páginas han cambiado su estructura
3. Aumenta el delay entre requests

## 📝 Notas Importantes

- El sistema detecta automáticamente noticias duplicadas por URL
- Los datos se guardan tanto en PostgreSQL como en archivos JSON/CSV
- El scraping es respetuoso con delays configurados
- Se mantiene un log detallado de todas las operaciones

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de uso educativo y de investigación.
