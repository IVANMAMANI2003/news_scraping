# 🕷️ BizNews Backend - Sistema de Scraping y API

Backend completo para extracción, procesamiento y API de noticias peruanas, construido con FastAPI, Scrapy y PostgreSQL.

## 🚀 Inicio Rápido

### 1. Configuración del Entorno

```bash
# Navegar al directorio del backend
cd scraping-project

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r api/requirements.txt
```

### 2. Configurar Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb news_db

# Configurar variables de entorno
cp env_example.txt .env
# Editar .env con tus credenciales
```

### 3. Inicializar Base de Datos

```bash
# Crear tablas y estructura
python setup_database.py

# Migrar datos existentes (opcional)
python migrate_to_postgres.py
```

### 4. Iniciar API

```bash
# Desarrollo
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

# Producción
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 5. Ejecutar Scraping

```bash
# Scraping manual
scrapy crawl pachamamaradio
scrapy crawl punonoticias
scrapy crawl losandes
scrapy crawl sinfronteras

# Scraping completo
python run_all_spiders_complete.py
```

## 📁 Estructura del Proyecto

```
scraping-project/
├── api/                      # API FastAPI
│   ├── main.py              # Aplicación principal
│   ├── models.py            # Modelos Pydantic
│   ├── db.py                # Conexión PostgreSQL
│   ├── requirements.txt     # Dependencias Python
│   └── routers/             # Endpoints de API
│       └── news.py          # Endpoints de noticias
├── scraper/                 # Sistema Scrapy
│   ├── settings.py          # Configuración Scrapy
│   └── spiders/             # Spiders individuales
│       ├── pachamamaradio.py
│       ├── punonoticias.py
│       ├── losandes.py
│       └── sinfronteras.py
├── pipelines/               # Procesamiento de datos
│   ├── clean_pipeline.py    # Limpieza de contenido
│   └── postgres_pipeline.py # Almacenamiento en BD
├── celery_tasks/            # Tareas programadas
│   ├── scraping_tasks.py    # Tareas de scraping
│   ├── cleanup_tasks.py     # Tareas de limpieza
│   └── migration_tasks.py   # Tareas de migración
├── celery_workers/          # Workers de Celery
│   ├── start_worker.py      # Iniciar worker
│   ├── start_beat.py        # Iniciar scheduler
│   └── control_tasks.py     # Control de tareas
├── config/                  # Configuraciones
│   ├── database.py          # Config de base de datos
│   └── redis_config.py      # Config de Redis
├── data/                    # Datos extraídos
│   ├── pachamamaradio/
│   ├── punonoticias/
│   ├── losandes/
│   └── sinfronteras/
├── logs/                    # Archivos de log
├── scripts/                 # Scripts de utilidad
│   ├── setup_database.py
│   ├── migrate_to_postgres.py
│   └── diagnose_postgres.py
└── tests/                   # Tests unitarios
```

## 🔌 API Endpoints

### Noticias

```http
# Listar noticias
GET /news
Query params:
  - limit: int (default: 20)
  - skip: int (default: 0)
  - order: str (asc/desc)
  - fecha_desde: str (YYYY-MM-DD)

# Obtener noticia específica
GET /news/{news_id}

# Noticias por fuente
GET /news/fuentes/{fuente_name}
Query params:
  - limit: int (default: 20)
  - skip: int (default: 0)
  - order: str (asc/desc)
  - fecha_desde: str (YYYY-MM-DD)

# Noticias por categoría
GET /news/categorias/{categoria_name}
Query params:
  - limit: int (default: 20)
  - skip: int (default: 0)
  - order: str (asc/desc)
  - fecha_desde: str (YYYY-MM-DD)
```

### Metadatos

```http
# Listar fuentes disponibles
GET /news/fuentes/listar

# Listar categorías disponibles
GET /news/categorias/listar
```

### Respuestas de Ejemplo

```json
{
  "total": 150,
  "items": [
    {
      "id": 1,
      "titulo": "Título de la noticia",
      "fecha": "2025-01-15",
      "hora": "10:30:00",
      "resumen": "Resumen de la noticia...",
      "contenido": "Contenido completo...",
      "categoria": "General",
      "autor": "Autor",
      "tags": "tag1,tag2",
      "url": "https://ejemplo.com/noticia",
      "fecha_extraccion": "2025-01-15T10:30:00",
      "imagenes": "url1,url2",
      "fuente": "Pachamama Radio",
      "created_at": "2025-01-15T10:30:00"
    }
  ]
}
```

## 🕷️ Sistema de Scraping

### Spiders Disponibles

#### Pachamama Radio
```bash
scrapy crawl pachamamaradio
```
- **URL**: https://pachamamaradio.org/
- **Categorías**: General, Política, Economía
- **Frecuencia**: Diaria
- **Items**: ~50 noticias/día

#### Puno Noticias
```bash
scrapy crawl punonoticias
```
- **URL**: https://punonoticias.com/
- **Categorías**: Local, Regional
- **Frecuencia**: Diaria
- **Items**: ~30 noticias/día

#### Los Andes
```bash
scrapy crawl losandes
```
- **URL**: https://losandes.com.pe/
- **Categorías**: Nacional, Internacional
- **Frecuencia**: Diaria
- **Items**: ~100 noticias/día

#### Sin Fronteras
```bash
scrapy crawl sinfronteras
```
- **URL**: https://sinfronteras.pe/
- **Categorías**: Alternativo, Social
- **Frecuencia**: Semanal
- **Items**: ~20 noticias/semana

### Configuración de Scraping

```python
# scraper/settings.py
BOT_NAME = 'news_scraper'
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Pipelines
ITEM_PIPELINES = {
    'pipelines.clean_pipeline.CleanPipeline': 300,
    'pipelines.postgres_pipeline.PostgresPipeline': 400,
}

# Base de datos
DATABASE_URL = 'postgresql://user:pass@localhost/news_db'
```

## 🗄️ Base de Datos

### Esquema Principal

```sql
-- Tabla de noticias
CREATE TABLE noticias (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(500) NOT NULL,
    fecha DATE,
    hora TIME,
    resumen TEXT,
    contenido TEXT,
    categoria VARCHAR(100),
    autor VARCHAR(200),
    tags TEXT,
    url VARCHAR(500) UNIQUE,
    fecha_extraccion TIMESTAMP,
    imagenes TEXT,
    fuente VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para optimización
CREATE INDEX idx_fuente ON noticias(fuente);
CREATE INDEX idx_categoria ON noticias(categoria);
CREATE INDEX idx_fecha ON noticias(fecha);
CREATE INDEX idx_url ON noticias(url);
CREATE INDEX idx_created_at ON noticias(created_at);
```

### Migraciones

```bash
# Crear estructura inicial
python setup_database.py

# Migrar datos de CSV/JSON
python migrate_to_postgres.py

# Migrar fuente específica
python migrate_pachamamaradio_to_db.py
python migrate_punonoticias_to_db.py
python migrate_losandes_to_db.py
python migrate_sinfronteras_to_db.py
```

## ⚙️ Configuración

### Variables de Entorno

Crear archivo `.env`:

```env
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=news_db
DB_USER=postgres
DB_PASSWORD=tu_password

# Redis (opcional)
REDIS_URL=redis://localhost:6379

# CORS
FRONTEND_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Scraping
DOWNLOAD_DELAY=1
RANDOMIZE_DOWNLOAD_DELAY=0.5
CONCURRENT_REQUESTS=16
```

### Configuración de FastAPI

```python
# api/main.py
app = FastAPI(
    title="BizNews API",
    description="API para sistema de noticias",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔄 Tareas Programadas (Celery)

### Configuración

```bash
# Instalar Redis (opcional)
# Windows: Descargar de https://redis.io/
# Linux: sudo apt-get install redis-server
# Mac: brew install redis

# Iniciar Redis
redis-server
```

### Workers

```bash
# Iniciar worker de Celery
python celery_workers/start_worker.py

# Iniciar scheduler
python celery_workers/start_beat.py

# Verificar workers
celery -A celery_app inspect active
```

### Tareas Disponibles

```python
# Tareas de scraping
from celery_tasks.scraping_tasks import scrape_pachamama, scrape_puno

# Ejecutar tarea
scrape_pachamama.delay()
scrape_puno.delay()

# Tareas de limpieza
from celery_tasks.cleanup_tasks import cleanup_old_news

# Limpiar noticias antiguas
cleanup_old_news.delay(days=30)
```

## 🧪 Testing

### Tests Unitarios

```bash
# Ejecutar todos los tests
python -m pytest tests/

# Test específico
python -m pytest tests/test_api.py

# Con cobertura
python -m pytest --cov=api tests/
```

### Tests de Integración

```bash
# Test de API
python test_api.py

# Test de base de datos
python test_db.py

# Test de scraping
python test_scraping.py
```

## 📊 Monitoreo

### Logs

```bash
# Logs de API
tail -f logs/api.log

# Logs de Scraping
tail -f logs/scraping.log

# Logs de Celery
tail -f logs/celery.log
```

### Métricas

```python
# Métricas de rendimiento
- Tiempo de respuesta API: < 200ms
- Tasa de éxito scraping: > 95%
- Uso de memoria: < 512MB
- Almacenamiento: ~1GB por 10,000 noticias
```

### Health Checks

```bash
# Verificar API
curl http://localhost:8000/health

# Verificar base de datos
python diagnose_postgres.py

# Verificar scraping
python test_scraping.py
```

## 🚀 Despliegue

### Desarrollo

```bash
# Terminal 1: API
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Celery Worker
python celery_workers/start_worker.py

# Terminal 3: Celery Beat
python celery_workers/start_beat.py
```

### Producción

```bash
# Usar Gunicorn
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Con supervisor
sudo supervisorctl start biznews-api
sudo supervisorctl start biznews-celery
```

### Docker (Opcional)

```bash
# Construir imagen
docker build -t biznews-backend .

# Ejecutar contenedor
docker run -p 8000:8000 biznews-backend

# Con docker-compose
docker-compose up -d
```

## 🐛 Solución de Problemas

### Error de Conexión a BD

```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Verificar conexión
python diagnose_postgres.py

# Recrear base de datos
dropdb news_db
createdb news_db
python setup_database.py
```

### Error de Scraping

```bash
# Verificar conectividad
python test_scraping.py

# Ejecutar spider con debug
scrapy crawl pachamamaradio -L DEBUG

# Verificar logs
tail -f logs/scraping.log
```

### Error de CORS

```bash
# Verificar configuración CORS
# En api/main.py verificar get_cors_origins()

# Verificar headers
curl -H "Origin: http://localhost:8080" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://localhost:8000/news
```

## 📈 Optimizaciones

### Base de Datos

```sql
-- Índices adicionales
CREATE INDEX idx_fecha_fuente ON noticias(fecha, fuente);
CREATE INDEX idx_categoria_fecha ON noticias(categoria, fecha);

-- Particionado por fecha (PostgreSQL 11+)
CREATE TABLE noticias_2025 PARTITION OF noticias
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### API

```python
# Cache con Redis
from functools import lru_cache
import redis

@lru_cache(maxsize=100)
def get_cached_news(fuente, limit, skip):
    # Implementar cache
    pass

# Paginación optimizada
def get_news_optimized(limit=20, skip=0):
    # Usar cursor-based pagination
    pass
```

### Scraping

```python
# Scraping distribuido
# Usar Scrapy Cluster o Scrapyd

# Rate limiting inteligente
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# User agents rotativos
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    # ... más user agents
]
```

## 🤝 Contribución

### Estándares de Código

- **Python**: PEP 8
- **Type hints**: Usar anotaciones de tipo
- **Docstrings**: Documentar funciones
- **Tests**: Cobertura > 80%

### Proceso de Desarrollo

1. Fork del repositorio
2. Crear rama feature
3. Implementar cambios
4. Agregar tests
5. Ejecutar linting
6. Pull request

## 📞 Soporte

Para soporte técnico:
- **Issues**: GitHub Issues
- **Email**: [tu-email@ejemplo.com]
- **Documentación**: README principal

---

**¡Disfruta desarrollando con BizNews Backend! 🚀**