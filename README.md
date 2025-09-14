# 📰 BizNews - Sistema de Scraping y Visualización de Noticias

Un sistema completo de extracción, almacenamiento y visualización de noticias de múltiples fuentes peruanas, con dashboard interactivo y reportes estadísticos.

## 🏗️ Arquitectura del Proyecto

```
news_scraping/
├── backend/                    # Backend (FastAPI + PostgreSQL)
│   └── scraping-project/
│       ├── api/               # API REST con FastAPI
│       ├── scraper/           # Spiders de Scrapy
│       ├── pipelines/         # Procesamiento de datos
│       └── celery_tasks/      # Tareas programadas
├── frontend/                  # Frontend (HTML + JavaScript)
│   └── biznews/              # Interfaz web responsive
└── data/                     # Datos extraídos (CSV/JSON)
```

## 🚀 Inicio Rápido

### Prerrequisitos

- **Python 3.8+**
- **PostgreSQL 12+**
- **Redis** (opcional, para tareas programadas)
- **Git**

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd news_scraping
```

### 2. Configurar Backend

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

### 3. Configurar Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb news_db

# Configurar variables de entorno
cp env_example.txt .env
# Editar .env con tus credenciales de PostgreSQL
```

### 4. Inicializar Base de Datos

```bash
# Ejecutar migraciones
python setup_database.py

# Migrar datos existentes (opcional)
python migrate_to_postgres.py
```

### 5. Iniciar Backend

```bash
# Iniciar API FastAPI
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. Iniciar Frontend

```bash
# En otra terminal, navegar al frontend
cd biznews

# Iniciar servidor HTTP local
python serve.py
# O usar el script batch en Windows
start_server.bat
```

### 7. Acceder a la Aplicación

- **Frontend**: http://localhost:8080
- **API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 📊 Fuentes de Noticias

El sistema extrae noticias de las siguientes fuentes:

- **Pachamama Radio** - Noticias regionales de Puno
- **Puno Noticias** - Información local de Puno
- **Los Andes** - Periódico regional
- **Sin Fronteras** - Medios alternativos

## 🎯 Funcionalidades

### Frontend (BizNews)

#### 🏠 Página Principal
- **Portada**: Noticias destacadas y últimas noticias
- **Noticias de Puno**: Sección especializada con filtros
- **Noticias Trending**: Más populares y relevantes
- **Navegación**: Menú intuitivo entre secciones

#### 📰 Gestión de Contenido
- **Fuentes**: Visualización por fuente de noticias
- **Categorías**: Organización por temas
- **Filtros de Tiempo**: Hoy, semana, mes, año
- **Detalle de Noticias**: Páginas individuales con contenido completo

#### 📈 Reportes y Estadísticas
- **Gráfica de Fuentes**: Distribución por fuente (Dona)
- **Gráfica de Categorías**: Noticias por categoría (Barras)
- **Tendencia Mensual**: Evolución temporal (Línea)
- **Días de la Semana**: Patrones de publicación (Polar)
- **Top Noticias**: Ranking de popularidad (Barras horizontales)
- **Resumen Estadístico**: Métricas clave del sistema

### Backend (API)

#### 🔌 Endpoints Principales

```http
# Noticias
GET /news                    # Listar todas las noticias
GET /news/{id}              # Obtener noticia específica
GET /news/fuentes/{fuente}  # Noticias por fuente
GET /news/categorias/{cat}  # Noticias por categoría

# Metadatos
GET /news/fuentes/listar    # Listar fuentes disponibles
GET /news/categorias/listar # Listar categorías disponibles

# Filtros
GET /news?fecha_desde=YYYY-MM-DD  # Filtrar por fecha
GET /news?limit=50&skip=0        # Paginación
```

#### 🕷️ Sistema de Scraping

- **Scrapy Spiders**: Extracción automatizada de noticias
- **Pipelines**: Limpieza y procesamiento de datos
- **Celery Tasks**: Programación de extracciones
- **Deduplicación**: Evita noticias duplicadas

## 🛠️ Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` en `scraping-project/`:

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
```

### Configuración de Scraping

```bash
# Ejecutar scraping manual
cd scraping-project
scrapy crawl pachamamaradio
scrapy crawl punonoticias
scrapy crawl losandes
scrapy crawl sinfronteras

# Ejecutar todos los spiders
python run_all_spiders_complete.py
```

### Tareas Programadas (Celery)

```bash
# Iniciar worker de Celery
python celery_workers/start_worker.py

# Iniciar scheduler
python celery_workers/start_beat.py
```

## 📁 Estructura Detallada

### Backend (`scraping-project/`)

```
scraping-project/
├── api/                      # API FastAPI
│   ├── main.py              # Aplicación principal
│   ├── models.py            # Modelos de datos
│   ├── db.py                # Conexión a base de datos
│   └── routers/             # Endpoints de la API
│       └── news.py          # Endpoints de noticias
├── scraper/                 # Spiders de Scrapy
│   ├── settings.py          # Configuración de Scrapy
│   └── spiders/             # Spiders individuales
├── pipelines/               # Procesamiento de datos
│   ├── clean_pipeline.py    # Limpieza de contenido
│   └── postgres_pipeline.py # Almacenamiento en BD
├── celery_tasks/            # Tareas programadas
│   ├── scraping_tasks.py    # Tareas de scraping
│   └── cleanup_tasks.py     # Tareas de limpieza
└── data/                    # Datos extraídos
    ├── pachamamaradio/
    ├── punonoticias/
    ├── losandes/
    └── sinfronteras/
```

### Frontend (`biznews/`)

```
biznews/
├── index.html               # Página principal
├── fuentes.html             # Página de fuentes
├── categorias.html          # Página de categorías
├── reportes.html            # Dashboard de estadísticas
├── detalle_noticias.html    # Página de noticia individual
├── contact.html             # Página de contacto
├── js/                      # JavaScript
│   ├── news-api.js          # Cliente de API
│   ├── fuentes.js           # Lógica de fuentes
│   ├── categorias.js        # Lógica de categorías
│   └── reportes.js          # Gráficas y estadísticas
├── css/                     # Estilos
│   ├── style.css            # Estilos principales
│   ├── custom-fixes.css     # Correcciones personalizadas
│   └── reportes.css         # Estilos de reportes
├── img/                     # Imágenes
└── serve.py                 # Servidor HTTP local
```

## 🔧 Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido
- **PostgreSQL**: Base de datos relacional
- **Scrapy**: Framework de web scraping
- **Celery**: Tareas asíncronas programadas
- **Redis**: Broker de mensajes (opcional)
- **SQLAlchemy**: ORM para base de datos
- **Pydantic**: Validación de datos

### Frontend
- **HTML5**: Estructura semántica
- **CSS3**: Estilos responsive
- **JavaScript ES6+**: Lógica del cliente
- **Chart.js**: Gráficas interactivas
- **Bootstrap 4**: Framework CSS
- **Font Awesome**: Iconografía

### Herramientas
- **Uvicorn**: Servidor ASGI
- **Python HTTP Server**: Servidor de archivos estáticos
- **Git**: Control de versiones

## 📊 Base de Datos

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
```

### Índices Optimizados

```sql
CREATE INDEX idx_fuente ON noticias(fuente);
CREATE INDEX idx_categoria ON noticias(categoria);
CREATE INDEX idx_fecha ON noticias(fecha);
CREATE INDEX idx_url ON noticias(url);
```

## 🚀 Despliegue

### Desarrollo Local

```bash
# Terminal 1: Backend
cd scraping-project
venv\Scripts\activate
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd biznews
python serve.py
```

### Producción

```bash
# Usar Gunicorn para producción
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Servir frontend con Nginx
# Configurar proxy reverso para API
```

## 🐛 Solución de Problemas

### Error de CORS
```bash
# Verificar que FRONTEND_ORIGINS esté configurado
# En api/main.py se incluyen orígenes comunes
```

### Error de Base de Datos
```bash
# Verificar conexión a PostgreSQL
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

# Ejecutar spider individual
scrapy crawl pachamamaradio -L INFO
```

## 📈 Monitoreo

### Logs del Sistema
```bash
# Logs de API
tail -f logs/api.log

# Logs de Scraping
tail -f logs/scraping.log

# Logs de Celery
tail -f logs/celery.log
```

### Métricas de Rendimiento
- **Tiempo de respuesta API**: < 200ms
- **Tasa de éxito scraping**: > 95%
- **Uso de memoria**: < 512MB
- **Almacenamiento**: ~1GB por 10,000 noticias

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Autores

- **Desarrollador Principal**: [Tu Nombre]
- **Minería de Datos**: Ciclo 8
- **Universidad**: [Nombre de la Universidad]

## 📞 Soporte

Para soporte técnico o preguntas:
- **Email**: [tu-email@ejemplo.com]
- **Issues**: [GitHub Issues]
- **Documentación**: [Wiki del Proyecto]

---

## 🎯 Roadmap

### Versión 2.0
- [ ] Sistema de usuarios y autenticación
- [ ] Notificaciones push
- [ ] API de búsqueda avanzada
- [ ] Exportación de datos (PDF, Excel)
- [ ] Dashboard de administración

### Versión 3.0
- [ ] Machine Learning para categorización
- [ ] Análisis de sentimientos
- [ ] Detección de noticias duplicadas
- [ ] Integración con redes sociales
- [ ] Aplicación móvil

---

**¡Gracias por usar BizNews! 🚀**
