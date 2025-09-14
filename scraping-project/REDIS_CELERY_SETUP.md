# 🚀 Configuración de Redis y Celery para Scraping Automatizado

## 📋 Descripción

Este proyecto integra Redis como broker de tareas y Celery para automatizar el scraping de noticias. El sistema ejecuta tareas programadas cada 6 horas, evita duplicados y guarda datos directamente en PostgreSQL.

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Broker  │    │  Celery Workers │    │   PostgreSQL    │
│                 │    │                 │    │                 │
│  - Cola scraping│◄──►│  - Worker 1     │◄──►│  - Tabla noticias│
│  - Cola migration│    │  - Worker 2     │    │  - Detección    │
│  - Cola cleanup │    │  - Worker 3     │    │    duplicados   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
    ┌────▼────┐            ┌─────▼─────┐
    │ Celery  │            │  Spiders  │
    │  Beat   │            │           │
    │(Scheduler)│          │ - Los Andes│
    └─────────┘            │ - Puno    │
                           │ - Pachamama│
                           │ - Sin Fronteras│
                           └───────────┘
```

## 📁 Estructura de Archivos

```
proyecto/
├── celery_app.py                 # Configuración principal de Celery
├── config/
│   └── redis_config.py          # Configuración de Redis y Celery
├── celery_tasks/
│   ├── __init__.py
│   ├── scraping_tasks.py        # Tareas de scraping
│   ├── migration_tasks.py       # Tareas de migración
│   └── cleanup_tasks.py         # Tareas de limpieza
├── celery_workers/
│   ├── start_worker.py          # Script para iniciar workers
│   ├── start_beat.py            # Script para iniciar scheduler
│   └── control_tasks.py         # Script de control de tareas
├── start_redis_celery.py        # Iniciador automático
├── install_redis_celery.py      # Instalador
└── docker-compose-redis.yml     # Docker para Redis y PostgreSQL
```

## 🚀 Instalación

### 1. Instalación Automática

```bash
python install_redis_celery.py
```

### 2. Instalación Manual

#### Instalar dependencias:
```bash
pip install -r api/requirements.txt
```

#### Instalar Redis:
- **Windows**: Descargar desde [GitHub](https://github.com/microsoftarchive/redis/releases)
- **Linux**: `sudo apt-get install redis-server`
- **macOS**: `brew install redis`
- **Docker**: `docker run -d -p 6379:6379 redis:alpine`

#### Instalar PostgreSQL:
- Usar Docker: `docker-compose -f docker-compose-redis.yml up -d`

## 🎯 Uso

### 1. Iniciar Servicios

#### Opción A: Automático
```bash
python start_redis_celery.py
```

#### Opción B: Manual
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Worker de scraping
python celery_workers/start_worker.py --queue scraping

# Terminal 3: Worker de migración
python celery_workers/start_worker.py --queue migration

# Terminal 4: Worker de limpieza
python celery_workers/start_worker.py --queue cleanup

# Terminal 5: Scheduler
python celery_workers/start_beat.py
```

### 2. Control de Tareas

#### Ver estado de colas:
```bash
python celery_workers/control_tasks.py list-queues
```

#### Disparar scraping inmediato:
```bash
python celery_workers/control_tasks.py trigger-scraping
```

#### Disparar migración:
```bash
python celery_workers/control_tasks.py trigger-migration
```

#### Ver resultado de tarea:
```bash
python celery_workers/control_tasks.py get-result --task-id <ID>
```

#### Limpiar colas:
```bash
python celery_workers/control_tasks.py purge
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Redis
REDIS_URL=redis://localhost:6379/0

# Base de Datos
DATABASE_URL=postgresql://postgres:123456@localhost:5432/noticias

# Scraping
SCRAPING_INTERVAL_HOURS=6
DUPLICATE_CHECK_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

### Configuración de Tareas Programadas

En `celery_app.py`:

```python
celery_app.conf.beat_schedule = {
    'scrape-all-sources': {
        'task': 'celery_tasks.scraping_tasks.scrape_all_sources',
        'schedule': 21600.0,  # 6 horas
    },
    # Limpieza automática deshabilitada para mantener máximo historial de datos
    # 'cleanup-old-data': {
    #     'task': 'celery_tasks.cleanup_tasks.cleanup_old_data',
    #     'schedule': 86400.0,  # 24 horas
    # },
}
```

## 🔧 Tareas Disponibles

### Scraping Tasks
- `scrape_all_sources`: Scraping de todas las fuentes
- `scrape_single_source`: Scraping de una fuente específica
- `scrape_source_now`: Scraping inmediato
- `check_duplicates`: Verificar duplicados

### Migration Tasks
- `migrate_source_to_db`: Migrar una fuente a PostgreSQL
- `migrate_all_sources`: Migrar todas las fuentes

### Cleanup Tasks
- `cleanup_old_data`: Limpiar datos antiguos
- `cleanup_duplicates`: Eliminar duplicados
- `optimize_database`: Optimizar base de datos
- `database_health_check`: Verificar salud de la BD

## 📊 Monitoreo

### Ver tareas activas:
```bash
python celery_workers/control_tasks.py list-active
```

### Ver tareas programadas:
```bash
python celery_workers/control_tasks.py list-scheduled
```

### Verificar salud de la base de datos:
```python
from celery_tasks.cleanup_tasks import database_health_check
result = database_health_check.delay()
print(result.get())
```

## 🐛 Solución de Problemas

### Redis no conecta:
1. Verificar que Redis esté ejecutándose: `redis-cli ping`
2. Verificar puerto: `netstat -an | grep 6379`
3. Reiniciar Redis: `redis-server`

### Workers no procesan tareas:
1. Verificar conexión a Redis
2. Verificar configuración de colas
3. Revisar logs de workers

### Duplicados en la base de datos:
1. Ejecutar limpieza: `python celery_workers/control_tasks.py trigger-cleanup`
2. Verificar configuración de detección de duplicados

### Tareas fallan:
1. Revisar logs de workers
2. Verificar conectividad a sitios web
3. Verificar configuración de base de datos

## 📈 Escalabilidad

### Aumentar workers:
```bash
# Múltiples workers para scraping
python celery_workers/start_worker.py --queue scraping --concurrency 8

# Workers especializados
python celery_workers/start_worker.py --queue migration --concurrency 2
```

### Configurar Redis Cluster:
```python
# En redis_config.py
REDIS_URL = 'redis://node1:6379,redis://node2:6379,redis://node3:6379'
```

### Usar Flower para monitoreo:
```bash
pip install flower
celery -A celery_app flower
```

## 🔒 Seguridad

### Configurar autenticación Redis:
```python
REDIS_URL = 'redis://:password@localhost:6379/0'
```

### Configurar SSL:
```python
REDIS_URL = 'rediss://localhost:6380/0'
```

### Restringir acceso a base de datos:
```python
DATABASE_URL = 'postgresql://user:pass@localhost:5432/noticias?sslmode=require'
```

## 📝 Logs

Los logs se guardan en:
- Workers: Salida estándar
- Celery Beat: Salida estándar
- Aplicación: `logs/` (configurable)

Configurar logging en `celery_app.py`:
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/celery.log'),
        logging.StreamHandler()
    ]
)
```

## 🔧 **Configuraciones Especiales**

### 📊 **Conservación de Datos**
- **Sin limpieza automática**: Los datos se conservan indefinidamente para mantener el máximo historial
- **Base de datos creciente**: Acumula todas las noticias extraídas sin eliminación automática
- **Limpieza manual**: Disponible solo cuando sea necesario ejecutar `cleanup_old_data`

### 🖼️ **Limitación de Imágenes**
- **Máximo 2 imágenes** por noticia
- **Filtrado inteligente**: Excluye iconos, logos, avatares y botones
- **Filtrado por tamaño**: Excluye imágenes menores a 100x100 píxeles
- **Optimización de almacenamiento**: Reduce el tamaño de los datos guardados

## 🎉 ¡Listo!

Tu sistema de scraping automatizado está configurado. Las noticias se extraerán automáticamente cada 6 horas y se guardarán en PostgreSQL sin duplicados, conservando todo el historial de datos.
