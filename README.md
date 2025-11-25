# 📰 BizNews - Sistema Completo de Gestión de Noticias

Un sistema completo y profesional de extracción, almacenamiento, procesamiento con IA, visualización y gestión de noticias de múltiples fuentes peruanas, con dashboard interactivo, panel de administración, sistema de autenticación, API REST, y procesamiento de contenido con inteligencia artificial.

---

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Características Principales](#características-principales)
4. [Instalación y Configuración](#instalación-y-configuración)
5. [Base de Datos](#base-de-datos)
6. [Backend API - Documentación Completa](#backend-api---documentación-completa)
7. [Frontend - Páginas Públicas](#frontend---páginas-públicas)
8. [Panel de Administración](#panel-de-administración)
9. [Sistema de Autenticación](#sistema-de-autenticación)
10. [Sistema de Scraping](#sistema-de-scraping)
11. [Sistema de Limpieza con IA](#sistema-de-limpieza-con-ia)
12. [Sistema de Migración de Datos](#sistema-de-migración-de-datos)
13. [Sistema de Suscripciones y Planes](#sistema-de-suscripciones-y-planes)
14. [Configuración Avanzada](#configuración-avanzada)
15. [Despliegue](#despliegue)
16. [Solución de Problemas](#solución-de-problemas)
17. [Contribución](#contribución)

---

## 🎯 Descripción General

**BizNews** es una plataforma completa de gestión de noticias que incluye:

- **Extracción Automatizada**: Sistema de scraping de múltiples fuentes de noticias
- **Procesamiento con IA**: Limpieza y análisis de contenido usando modelos de lenguaje (Ollama)
- **API REST Completa**: Endpoints para acceso programático a los datos
- **Panel de Administración**: Interfaz completa para gestión de usuarios, noticias, fuentes y más
- **Sitio Web Público**: Visualización de noticias con búsqueda avanzada
- **Sistema de Autenticación**: JWT-based con roles y permisos
- **Sistema de Planes**: Diferentes niveles de acceso (Free, Pro, Business, Enterprise)
- **Migración de Datos**: Herramientas ETL para transformación de datos

---

## 🏗️ Arquitectura del Sistema

```
news_scraping/
├── scraping-project/          # Backend (FastAPI + PostgreSQL)
│   ├── api/                   # API REST con FastAPI
│   │   ├── main.py           # Aplicación principal
│   │   ├── auth.py           # Autenticación JWT
│   │   ├── db.py             # Pool de conexiones PostgreSQL
│   │   ├── models.py         # Modelos Pydantic
│   │   └── routers/          # Endpoints de la API
│   │       ├── news.py       # Noticias públicas
│   │       ├── advanced.py   # Búsqueda avanzada
│   │       ├── auth.py       # Autenticación
│   │       ├── users.py      # Gestión de usuarios
│   │       ├── api_keys.py   # Gestión de API keys
│   │       ├── admin.py      # Panel de administración
│   │       ├── nlp_cleaning.py  # Limpieza con IA
│   │       ├── scrapers.py   # Gestión de scrapers
│   │       ├── export.py     # Exportación de datos
│   │       ├── metadata.py   # Metadatos
│   │       └── social.py     # Noticias sociales
│   ├── spiders/              # Spiders de Scrapy
│   │   ├── pachamamaradio_local.py
│   │   ├── punonoticias_local.py
│   │   ├── losandes_local.py
│   │   ├── sinfronteras_local.py
│   │   └── test_scraper_local.py
│   ├── nlp_cleaning/         # Procesamiento con IA
│   │   └── nlp_cleaner.py    # Limpiador de contenido
│   ├── etl-data/             # Scripts de migración
│   │   └── migrate_completo.py
│   ├── init.sql              # Esquema de base de datos
│   └── requirements.txt      # Dependencias Python
│
├── biznews/                  # Frontend (HTML + JavaScript)
│   ├── index.html            # Página principal
│   ├── page/                 # Páginas públicas
│   │   ├── fuentes.html
│   │   ├── categorias.html
│   │   ├── servicios.html
│   │   ├── busqueda.html
│   │   ├── noticias-ia.html
│   │   ├── detalle-noticia-ia.html
│   │   ├── detalle_noticias.html
│   │   ├── contact.html
│   │   └── login.html
│   ├── admin/                # Panel de administración
│   │   ├── dashboard.html
│   │   ├── noticias.html
│   │   ├── usuarios.html
│   │   ├── api-keys.html
│   │   ├── scrapers.html
│   │   ├── limpieza.html
│   │   ├── fuentes.html
│   │   ├── categorias.html
│   │   └── reportes.html
│   ├── js/                   # JavaScript
│   │   ├── navigation.js     # Navegación dinámica
│   │   ├── public-auth.js    # Autenticación pública
│   │   ├── news-api.js       # Cliente API
│   │   ├── busqueda.js       # Búsqueda avanzada
│   │   ├── noticias-ia.js    # Noticias con IA
│   │   ├── subscription-cta.js  # CTA de suscripción
│   │   └── admin/            # JS del panel admin
│   │       ├── auth.js
│   │       ├── dashboard.js
│   │       ├── noticias.js
│   │       ├── usuarios.js
│   │       ├── api-keys.js
│   │       ├── scrapers.js
│   │       ├── limpieza.js
│   │       └── sidebar.js
│   ├── css/                  # Estilos
│   │   ├── global.css
│   │   ├── subscription-cta.css
│   │   └── ...
│   └── serve.py              # Servidor HTTP local
│
└── README.md                 # Este archivo
```

---

## ✨ Características Principales

### 🔐 Autenticación y Autorización
- Sistema JWT completo con refresh tokens
- Roles: admin, user, moderator
- Planes: free, pro, business, enterprise
- Gestión de sesiones
- API keys para acceso programático

### 📰 Gestión de Noticias
- Extracción automatizada de múltiples fuentes
- Procesamiento con IA (Ollama) para limpieza de contenido
- Búsqueda avanzada con múltiples filtros
- Categorización automática
- Detección de duplicados por URL

### 🎨 Interfaz de Usuario
- Sitio web público responsive
- Panel de administración completo
- Dashboard con métricas en tiempo real
- Búsqueda avanzada con filtros múltiples
- Visualización de noticias procesadas con IA

### 🕷️ Sistema de Scraping
- Múltiples scrapers configurados
- Ejecución bajo demanda desde el panel
- Filtros por fecha, fuente, categoría
- Control de cantidad de noticias
- Migración automática de datos

### 📊 Análisis y Reportes
- Estadísticas detalladas
- Gráficas interactivas
- Métricas de rendimiento
- Análisis de contenido

---

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Python 3.8+**
- **PostgreSQL 12+**
- **Node.js** (opcional, para algunas herramientas)
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

# Instalar dependencias de autenticación
pip install bcrypt==4.1.2 PyJWT==2.8.0
```

### 3. Configurar Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb news_db

# Configurar variables de entorno
cp env_example.txt .env
# Editar .env con tus credenciales:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=news_db
# DB_USER=postgres
# DB_PASSWORD=tu_password
# JWT_SECRET_KEY=tu_secret_key_seguro
```

### 4. Inicializar Base de Datos

```bash
# Ejecutar script de inicialización
python init_database.py

# Inicializar esquema de autenticación
python api/scripts/init_auth_schema.py
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

- **Frontend Público**: http://localhost:8080
- **Panel Admin**: http://localhost:8080/admin/login.html
- **API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Credenciales Admin**: 
  - Email: `admin@biznews.com`
  - Password: `admin123`

---

## 🗄️ Base de Datos

### Esquema Principal

#### Tabla: `noticias`
Almacena noticias en su estado original (raw).

```sql
CREATE TABLE noticias (
    id SERIAL PRIMARY KEY,
    titulo TEXT,
    fecha TIMESTAMP,
    hora TIME,
    resumen TEXT,
    contenido TEXT,
    categoria VARCHAR(100),
    autor VARCHAR(200),
    tags TEXT,
    url TEXT UNIQUE,
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imagenes TEXT,
    fuente VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: `noticias_limpia`
Noticias procesadas y normalizadas.

```sql
CREATE TABLE noticias_limpia (
    id SERIAL PRIMARY KEY,
    titulo TEXT,
    fecha DATE,
    hora TIME,
    anio INTEGER,
    mes INTEGER,
    dia INTEGER,
    dia_semana VARCHAR(20),
    resumen TEXT,
    contenido TEXT,
    categoria VARCHAR(100),
    autor VARCHAR(200),
    keywords TEXT,
    url TEXT UNIQUE,
    dominio VARCHAR(255),
    fecha_extraccion TIMESTAMP,
    imagen_principal TEXT,
    cantidad_imagenes INTEGER,
    tiene_imagenes BOOLEAN,
    fuente VARCHAR(100),
    longitud_titulo INTEGER,
    longitud_resumen FLOAT,
    tipo_contenido VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: `noticias_bert_clean`
Noticias procesadas con IA (Ollama).

```sql
CREATE TABLE noticias_bert_clean (
    id SERIAL PRIMARY KEY,
    noticia_id INTEGER REFERENCES noticias_limpia(id),
    titulo TEXT,
    resumen TEXT,
    contenido_limpio TEXT,
    contenido_raw TEXT,
    num_parrafos_total INTEGER,
    num_parrafos_relevantes INTEGER,
    num_parrafos_irrelevantes INTEGER,
    parrafos_relevantes JSONB,
    parrafos_irrelevantes JSONB,
    url TEXT,
    fuente VARCHAR(100),
    fecha DATE,
    modelo_usado VARCHAR(100),
    procesado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    porcentaje_relevancia FLOAT
);
```

#### Tabla: `usuarios`
Gestión de usuarios del sistema.

```sql
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255),
    activo BOOLEAN DEFAULT true,
    rol VARCHAR(50) DEFAULT 'user' CHECK (rol IN ('admin', 'user', 'moderator')),
    plan VARCHAR(50) DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'business', 'enterprise')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    email_verificado BOOLEAN DEFAULT false
);
```

#### Tabla: `api_keys`
API keys para acceso programático.

```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    key VARCHAR(255) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    activo BOOLEAN DEFAULT true,
    requests_today INT DEFAULT 0,
    requests_total BIGINT DEFAULT 0,
    last_reset DATE DEFAULT CURRENT_DATE,
    last_used TIMESTAMP,
    fuente_permitida VARCHAR(100),
    max_sources INT DEFAULT 1,
    keywords TEXT[],
    webhook_url VARCHAR(500),
    historial_dias INT DEFAULT 0,
    limite_diario INT DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

#### Otras Tablas
- `scraping_control`: Control de ejecución de scrapers
- `permisos`: Permisos del sistema
- `usuario_permisos`: Relación usuarios-permisos
- `sesiones`: Gestión de sesiones activas
- `search_history`: Historial de búsquedas

### Índices

```sql
CREATE INDEX idx_noticias_fuente ON noticias(fuente);
CREATE INDEX idx_noticias_fecha ON noticias(fecha);
CREATE INDEX idx_noticias_url ON noticias(url);
CREATE INDEX idx_noticias_limpia_fuente ON noticias_limpia(fuente);
CREATE INDEX idx_noticias_limpia_categoria ON noticias_limpia(categoria);
CREATE INDEX idx_noticias_limpia_fecha ON noticias_limpia(fecha);
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_api_keys_key ON api_keys(key);
```

---

## 🔌 Backend API - Documentación Completa

### Base URL
```
http://127.0.0.1:8000
```

### Autenticación

La mayoría de endpoints requieren autenticación mediante JWT:

```http
Authorization: Bearer <token>
```

---

### 📰 Endpoints de Noticias (`/news`)

#### `GET /news`
Lista todas las noticias con paginación y filtros.

**Query Parameters:**
- `limit` (int, default: 20): Número de resultados
- `skip` (int, default: 0): Registros a omitir
- `order` (str, default: "desc"): Orden (asc/desc)
- `q` (str, optional): Búsqueda en título, contenido o resumen
- `categoria` (str, optional): Filtrar por categoría
- `fuente` (str, optional): Filtrar por fuente
- `fecha_desde` (str, optional): Fecha desde (YYYY-MM-DD)
- `fecha_hasta` (str, optional): Fecha hasta (YYYY-MM-DD)

**Ejemplo:**
```http
GET /news?limit=50&skip=0&order=desc&categoria=Política
```

**Respuesta:**
```json
{
  "total": 150,
  "items": [
    {
      "id": 1,
      "titulo": "Título de la noticia",
      "fecha": "2025-01-15T00:00:00",
      "resumen": "Resumen...",
      "contenido": "Contenido completo...",
      "categoria": "Política",
      "fuente": "Pachamama Radio",
      "url": "https://ejemplo.com/noticia",
      ...
    }
  ]
}
```

#### `GET /news/{news_id}`
Obtiene una noticia específica por ID.

#### `GET /news/fuentes/{fuente_name}`
Lista noticias de una fuente específica.

#### `GET /news/categorias/{categoria_name}`
Lista noticias de una categoría específica.

#### `GET /news/fuentes/listar`
Lista todas las fuentes disponibles.

#### `GET /news/categorias/listar`
Lista todas las categorías disponibles.

---

### 🔍 Búsqueda Avanzada (`/api`)

#### `GET /api/search`
Búsqueda avanzada con múltiples filtros.

**Query Parameters:**
- `q` (str, optional): Búsqueda de texto
- `categoria` (str, optional): Filtrar por categoría
- `fuente` (str, optional): Filtrar por fuente
- `dominio` (str, optional): Filtrar por dominio
- `anio` (int, optional): Filtrar por año
- `mes` (int, optional): Filtrar por mes (1-12)
- `dia` (int, optional): Filtrar por día del mes
- `dia_semana` (str, optional): Filtrar por día de la semana
- `tipo_contenido` (str, optional): Filtrar por tipo de contenido
- `tiene_imagenes` (bool, optional): Filtrar por noticias con/sin imágenes
- `longitud_titulo_min` (int, optional): Longitud mínima del título
- `longitud_titulo_max` (int, optional): Longitud máxima del título
- `longitud_resumen_min` (float, optional): Longitud mínima del resumen
- `longitud_resumen_max` (float, optional): Longitud máxima del resumen
- `fecha_desde` (str, optional): Fecha desde (YYYY-MM-DD)
- `fecha_hasta` (str, optional): Fecha hasta (YYYY-MM-DD)
- `keywords` (str, optional): Búsqueda en keywords
- `skip` (int, default: 0): Registros a omitir
- `limit` (int, default: 20): Número de resultados
- `order` (str, default: "desc"): Orden
- `include_stats` (bool, default: false): Incluir estadísticas

**Requisitos:** Autenticación (cualquier usuario con cuenta)

**Ejemplo:**
```http
GET /api/search?q=puno&categoria=Política&fecha_desde=2025-01-01&limit=50
```

#### `GET /api/stats`
Obtiene estadísticas detalladas de las noticias.

**Requisitos:** Autenticación

#### `GET /api/metrics`
Obtiene métricas del sistema.

#### `GET /api/by-year/{year}`
Noticias por año específico.

#### `GET /api/by-month/{year}/{month}`
Noticias por mes específico.

#### `GET /api/with-images`
Noticias que tienen imágenes.

#### `GET /api/trending`
Noticias trending/populares.

---

### 🔐 Autenticación (`/auth`)

#### `POST /auth/register`
Registra un nuevo usuario.

**Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123",
  "nombre": "Juan",
  "apellido": "Pérez",
  "plan": "free"
}
```

#### `POST /auth/login`
Inicia sesión y obtiene token JWT.

**Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123"
}
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "nombre": "Juan",
    "rol": "user",
    "plan": "free"
  }
}
```

#### `POST /auth/refresh`
Refresca el token de acceso.

**Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### `POST /auth/logout`
Cierra sesión.

**Requisitos:** Autenticación

#### `GET /auth/me`
Obtiene información del usuario actual.

**Requisitos:** Autenticación

---

### 👥 Gestión de Usuarios (`/users`)

#### `GET /users`
Lista todos los usuarios.

**Requisitos:** Autenticación (admin, user, moderator)

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 20)
- `activo` (bool, optional): Filtrar por estado

#### `GET /users/{user_id}`
Obtiene un usuario específico.

**Requisitos:** Autenticación

#### `POST /users`
Crea un nuevo usuario.

**Requisitos:** Autenticación (admin)

**Body:**
```json
{
  "email": "nuevo@ejemplo.com",
  "password": "password123",
  "nombre": "Nuevo",
  "apellido": "Usuario",
  "plan": "free",
  "rol": "user"
}
```

#### `PUT /users/{user_id}`
Actualiza un usuario.

**Requisitos:** Autenticación (admin puede actualizar cualquier campo, usuarios solo pueden actualizar sus propios datos)

**Body:**
```json
{
  "nombre": "Nombre Actualizado",
  "plan": "pro",
  "rol": "user"
}
```

#### `DELETE /users/{user_id}`
Elimina un usuario.

**Requisitos:** Autenticación (admin)

---

### 🔑 Gestión de API Keys (`/api-keys`)

#### `GET /api-keys`
Lista todas las API keys del usuario.

**Requisitos:** Autenticación

#### `GET /api-keys/{key_id}`
Obtiene una API key específica.

**Requisitos:** Autenticación

#### `POST /api-keys`
Crea una nueva API key.

**Requisitos:** Autenticación

**Body:**
```json
{
  "nombre": "Mi API Key",
  "plan": "free",
  "fuente_permitida": "Pachamama Radio",
  "limite_diario": 50
}
```

#### `PUT /api-keys/{key_id}`
Actualiza una API key.

**Requisitos:** Autenticación

#### `DELETE /api-keys/{key_id}`
Elimina una API key.

**Requisitos:** Autenticación

#### `GET /api-keys/{key_id}/stats`
Obtiene estadísticas de uso de una API key.

**Requisitos:** Autenticación

---

### 🤖 Limpieza con IA (`/api/nlp`)

#### `POST /api/nlp/limpiar`
Procesa noticias con IA para limpieza de contenido.

**Requisitos:** Autenticación (admin, enterprise, premium)

**Body:**
```json
{
  "noticia_id": 123,
  "titulo": "Buscar por título",
  "categoria": "Política",
  "fuente": "Pachamama Radio",
  "cantidad": 10,
  "fecha_desde": "2025-01-01",
  "fecha_hasta": "2025-01-31",
  "modelo": "deepseek-r1:8b",
  "tabla_origen": "noticias"
}
```

**Respuesta:**
```json
{
  "procesadas": 10,
  "exitosas": 9,
  "errores": 1,
  "detalles": [...]
}
```

#### `GET /api/nlp/limpiadas`
Lista noticias procesadas con IA.

**Requisitos:** Autenticación (admin, enterprise)

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 50)
- `order` (str, default: "desc")

#### `GET /api/nlp/limpiadas/{noticia_id}`
Obtiene detalles completos de una noticia procesada.

**Requisitos:** Autenticación (admin, enterprise)

#### `GET /api/nlp/public`
Lista noticias procesadas con IA (vista pública).

**Requisitos:** Autenticación (enterprise, premium, admin)

#### `GET /api/nlp/public/{noticia_id}`
Obtiene una noticia procesada con IA (vista pública).

**Requisitos:** Autenticación (enterprise, premium, admin)

#### `GET /api/nlp/estadisticas`
Obtiene estadísticas de procesamiento con IA.

**Requisitos:** Autenticación (admin)

---

### 🕷️ Gestión de Scrapers (`/api/scrapers`)

#### `POST /api/scrapers/run`
Ejecuta scrapers de noticias.

**Requisitos:** Autenticación (admin)

**Body:**
```json
{
  "type": "single",
  "source": "pachamamaradio",
  "date_start": "2025-01-01",
  "date_end": "2025-01-31",
  "limit": 50,
  "categoria": "Política"
}
```

**Tipos disponibles:**
- `single`: Una fuente específica
- `all`: Todas las fuentes
- `dateRange`: Rango de fechas
- `recent`: Noticias recientes

**Respuesta:**
```json
{
  "job_id": "scraping_20250115_120000",
  "status": "running",
  "message": "Scraping iniciado"
}
```

#### `GET /api/scrapers/status/{job_id}`
Obtiene el estado de un trabajo de scraping.

**Requisitos:** Autenticación (admin)

#### `GET /api/scrapers/sources`
Lista todas las fuentes disponibles para scraping.

**Requisitos:** Autenticación (admin)

#### `POST /api/scrapers/run-source/{source_id}`
Ejecuta un scraper específico.

**Requisitos:** Autenticación (admin)

#### `DELETE /api/scrapers/status/{job_id}`
Cancela un trabajo de scraping.

**Requisitos:** Autenticación (admin)

#### `POST /api/scrapers/migrate`
Inicia migración de datos de `noticias` a `noticias_limpia`.

**Requisitos:** Autenticación (admin)

**Respuesta:**
```json
{
  "job_id": "migration_20250115_120000",
  "status": "running"
}
```

#### `GET /api/scrapers/migrate/status/{job_id}`
Obtiene el estado de una migración.

**Requisitos:** Autenticación (admin)

---

### 🛠️ Panel de Administración (`/api/admin`)

#### `POST /api/admin/news`
Crea una nueva noticia.

**Requisitos:** Autenticación (admin)

#### `PUT /api/admin/news/{news_id}`
Actualiza una noticia.

**Requisitos:** Autenticación (admin)

#### `DELETE /api/admin/news/{news_id}`
Elimina una noticia.

**Requisitos:** Autenticación (admin)

#### `GET /api/admin/sources`
Lista todas las fuentes.

**Requisitos:** Autenticación (admin)

#### `POST /api/admin/sources`
Crea una nueva fuente.

**Requisitos:** Autenticación (admin)

#### `PUT /api/admin/sources/{old_name}`
Actualiza una fuente.

**Requisitos:** Autenticación (admin)

#### `DELETE /api/admin/sources/{source_name}`
Elimina una fuente.

**Requisitos:** Autenticación (admin)

#### `GET /api/admin/categories`
Lista todas las categorías.

**Requisitos:** Autenticación (admin)

#### `POST /api/admin/categories`
Crea una nueva categoría.

**Requisitos:** Autenticación (admin)

#### `PUT /api/admin/categories/{old_name}`
Actualiza una categoría.

**Requisitos:** Autenticación (admin)

#### `DELETE /api/admin/categories/{category_name}`
Elimina una categoría.

**Requisitos:** Autenticación (admin)

---

### 📤 Exportación (`/api/export`)

#### `GET /api/export`
Exporta noticias en diferentes formatos.

**Query Parameters:**
- `format` (str): csv, json, excel
- `fecha_desde` (str, optional)
- `fecha_hasta` (str, optional)
- `fuente` (str, optional)
- `categoria` (str, optional)

**Requisitos:** Autenticación (admin)

#### `GET /api/export/info`
Obtiene información sobre exportaciones disponibles.

**Requisitos:** Autenticación (admin)

---

### 📊 Metadatos (`/news`)

#### `GET /news/dominios/listar`
Lista todos los dominios únicos.

#### `GET /news/tipos-contenido/listar`
Lista todos los tipos de contenido.

#### `GET /news/dias-semana/listar`
Lista todos los días de la semana disponibles.

#### `GET /news/anos/listar`
Lista todos los años disponibles.

#### `GET /news/meses/listar`
Lista todos los meses disponibles.

---

### 📱 Noticias Sociales (`/social`)

#### `POST /social/scrape`
Extrae posts desde fuentes sociales predefinidas.

**Requisitos:** Autenticación (admin)

#### `GET /social/news`
Obtiene noticias de fuentes sociales.

**Query Parameters:**
- `limit` (int, default: 20)
- `skip` (int, default: 0)
- `q` (str, optional): Búsqueda de texto

---

## 🌐 Frontend - Páginas Públicas

### Página Principal (`index.html`)

**URL:** `http://localhost:8080`

**Características:**
- Hero section con estadísticas
- Noticias destacadas
- Noticias recientes
- Categorías populares
- Navegación dinámica

**JavaScript:** `js/news-api.js`

---

### Fuentes (`page/fuentes.html`)

**URL:** `http://localhost:8080/page/fuentes.html`

**Características:**
- Lista todas las fuentes disponibles
- Filtros por fuente
- Visualización de noticias por fuente
- Paginación

**JavaScript:** `js/fuentes.js`

---

### Categorías (`page/categorias.html`)

**URL:** `http://localhost:8080/page/categorias.html`

**Características:**
- Lista todas las categorías
- Filtros por categoría
- Visualización de noticias por categoría
- Paginación

**JavaScript:** `js/categorias.js`

---

### Búsqueda Avanzada (`page/busqueda.html`)

**URL:** `http://localhost:8080/page/busqueda.html`

**Características:**
- Búsqueda de texto
- Filtros múltiples:
  - Fuente
  - Categoría
  - Dominio
  - Año, mes, día
  - Tipo de contenido
  - Rango de fechas
  - Longitud de título/resumen
  - Keywords
- Resultados paginados
- Estadísticas de búsqueda

**Requisitos:** Autenticación (cualquier usuario con cuenta)

**JavaScript:** `js/busqueda.js`

---

### Noticias con IA (`page/noticias-ia.html`)

**URL:** `http://localhost:8080/page/noticias-ia.html`

**Características:**
- Visualización de noticias procesadas con IA
- Filtros por categoría
- Información de relevancia
- Modelo usado
- Porcentaje de relevancia

**Requisitos:** Autenticación (enterprise, premium, admin)

**JavaScript:** `js/noticias-ia.js`

---

### Detalle Noticia IA (`page/detalle-noticia-ia.html`)

**URL:** `http://localhost:8080/page/detalle-noticia-ia.html?id={id}`

**Características:**
- Contenido limpio completo
- Párrafos relevantes destacados
- Párrafos irrelevantes
- Estadísticas de procesamiento
- Información del modelo usado

**Requisitos:** Autenticación (enterprise, premium, admin)

**JavaScript:** `js/detalle-noticia-ia.js`

---

### Detalle Noticia (`page/detalle_noticias.html`)

**URL:** `http://localhost:8080/page/detalle_noticias.html?id={id}`

**Características:**
- Contenido completo de la noticia
- Información de fuente y categoría
- Imágenes
- Fecha y autor

**JavaScript:** `js/detalle.js`

---

### Servicios (`page/servicios.html`)

**URL:** `http://localhost:8080/page/servicios.html`

**Características:**
- Información de planes disponibles
- Comparación de características
- Formulario de suscripción
- Modal de registro

**JavaScript:** `js/subscribe.js`

---

### Login (`page/login.html`)

**URL:** `http://localhost:8080/page/login.html`

**Características:**
- Formulario de inicio de sesión
- Opciones post-login:
  - Ir al Dashboard (si es admin)
  - Continuar en página pública

**JavaScript:** `js/public-auth.js`

---

### Contacto (`page/contact.html`)

**URL:** `http://localhost:8080/page/contact.html`

**Características:**
- Formulario de contacto
- Información de la empresa

**JavaScript:** `js/contact.js`

---

### Componente de Suscripción (CTA)

**Archivo:** `js/subscription-cta.js`, `css/subscription-cta.css`

**Características:**
- Banner flotante elegante
- Aparece en páginas públicas
- No se muestra si el usuario está autenticado
- Se puede cerrar (recordado por 7 días)
- Invita a suscribirse o iniciar sesión

---

## 🎛️ Panel de Administración

### Dashboard (`admin/dashboard.html`)

**URL:** `http://localhost:8080/admin/dashboard.html`

**Características:**
- Métricas en tiempo real:
  - Total de noticias
  - Noticias con/sin imágenes
  - Promedio de longitud
  - Fuentes activas
- Estadísticas detalladas:
  - Por fuente
  - Por categoría
  - Por mes
  - Por día de la semana
- Tabla de noticias recientes
- Filtros:
  - Tiempo (hoy, semana, mes, año)
  - Fuente
  - Categoría
- Paginación
- Acciones rápidas:
  - Ejecutar Scrapers
  - Exportar Datos
  - Ver Noticias

**JavaScript:** `admin/js/dashboard.js`

---

### Gestión de Noticias (`admin/noticias.html`)

**URL:** `http://localhost:8080/admin/noticias.html`

**Características:**
- Lista completa de noticias
- Búsqueda y filtros
- Paginación
- Acciones:
  - Ver detalle
  - Editar
  - Eliminar
- Crear nueva noticia

**JavaScript:** `admin/js/noticias.js`

---

### Gestión de Usuarios (`admin/usuarios.html`)

**URL:** `http://localhost:8080/admin/usuarios.html`

**Características:**
- Lista de usuarios
- Crear usuario
- Editar usuario:
  - Nombre, apellido, email
  - Rol (admin, user, moderator)
  - Plan (free, pro, business, enterprise)
  - Estado activo/inactivo
- Eliminar usuario
- Paginación
- Sincronización automática de planes entre `usuarios` y `api_keys`

**JavaScript:** `admin/js/usuarios.js`

---

### Gestión de API Keys (`admin/api-keys.html`)

**URL:** `http://localhost:8080/admin/api-keys.html`

**Características:**
- Lista de API keys
- Crear API key
- Editar API key:
  - Nombre
  - Plan
  - Límite diario
  - Fuente permitida
  - Keywords
  - Webhook URL
- Eliminar API key
- Ver estadísticas de uso
- Sincronización automática de planes con usuario

**JavaScript:** `admin/js/api-keys.js`

---

### Gestión de Scrapers (`admin/scrapers.html`)

**URL:** `http://localhost:8080/admin/scrapers.html`

**Características:**
- Ejecutar scrapers:
  - Tipo: Últimas, Todas, Por fecha, Por fuente
  - Filtros avanzados:
    - Cantidad (5, 10, 20, 50, 100, Sin límite)
    - Fuente específica
    - Categoría
    - Rango de fechas
- Ver estado de trabajos
- Estadísticas de scraping
- Migración de datos:
  - Iniciar migración de `noticias` a `noticias_limpia`
  - Ver progreso en tiempo real
  - Logs detallados
  - Resultados finales
- Notificaciones toast después de scraping

**JavaScript:** `admin/js/scrapers.js`

---

### Limpieza con IA (`admin/limpieza.html`)

**URL:** `http://localhost:8080/admin/limpieza.html`

**Características:**
- Procesar noticias con IA:
  - Por ID específico
  - Por título (búsqueda)
  - Por categoría
  - Por fuente
  - Por cantidad
  - Por rango de fechas
  - Prompt personalizado
  - Selección de modelo
- Lista de noticias procesadas:
  - Información de relevancia
  - Porcentaje de relevancia
  - Modelo usado
  - Fecha de procesamiento
- Acciones:
  - Ver detalle completo
  - Reprocesar noticia
- Búsqueda por título:
  - Lista noticias encontradas
  - Selección múltiple
  - Procesar seleccionadas
- Paginación

**JavaScript:** `admin/js/limpieza.js`

---

### Gestión de Fuentes (`admin/fuentes.html`)

**URL:** `http://localhost:8080/admin/fuentes.html`

**Características:**
- Lista de fuentes
- Crear fuente
- Editar fuente
- Eliminar fuente

**JavaScript:** `admin/js/fuentes.js`

---

### Gestión de Categorías (`admin/categorias.html`)

**URL:** `http://localhost:8080/admin/categorias.html`

**Características:**
- Lista de categorías
- Crear categoría
- Editar categoría
- Eliminar categoría

**JavaScript:** `admin/js/categorias.js`

---

### Reportes (`admin/reportes.html`)

**URL:** `http://localhost:8080/admin/reportes.html`

**Características:**
- Gráficas interactivas:
  - Distribución por fuente (Dona)
  - Distribución por categoría (Barras)
  - Tendencia mensual (Línea)
  - Días de la semana (Polar)
  - Top noticias (Barras horizontales)
- Resumen estadístico
- Exportación de reportes

**JavaScript:** `admin/js/reportes.js`

---

## 🔐 Sistema de Autenticación

### Autenticación JWT

El sistema usa JWT (JSON Web Tokens) para autenticación:

- **Access Token**: Válido por 24 horas
- **Refresh Token**: Válido por 30 días
- **Algoritmo**: HS256
- **Secret Key**: Configurable en variables de entorno

### Roles

- **admin**: Acceso completo al sistema
- **user**: Usuario regular
- **moderator**: Moderador con permisos limitados

### Planes

- **free**: Plan gratuito básico
- **pro**: Plan profesional ($12/mes)
- **business**: Plan empresarial ($64/mes)
- **enterprise**: Plan enterprise ($350/mes)

### Flujo de Autenticación

1. Usuario se registra o inicia sesión
2. Servidor genera access_token y refresh_token
3. Cliente almacena tokens en localStorage
4. Cliente incluye token en header `Authorization: Bearer <token>`
5. Servidor valida token en cada request
6. Si token expira, usar refresh_token para obtener nuevo access_token

### Seguridad

- Contraseñas hasheadas con bcrypt
- Tokens firmados con secret key
- Validación de expiración
- Protección CSRF
- Rate limiting (implementable)

---

## 🕷️ Sistema de Scraping

### Scrapers Disponibles

1. **Pachamama Radio** (`pachamamaradio_local.py`)
2. **Puno Noticias** (`punonoticias_local.py`)
3. **Los Andes** (`losandes_local.py`)
4. **Sin Fronteras** (`sinfronteras_local.py`)
5. **Test Scraper** (`test_scraper_local.py`) - Deshabilitado por defecto

### Ejecución de Scrapers

#### Desde el Panel de Administración

1. Ir a `admin/scrapers.html`
2. Seleccionar tipo de scraping
3. Configurar filtros
4. Ejecutar
5. Ver progreso en tiempo real

#### Desde la API

```http
POST /api/scrapers/run
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "single",
  "source": "pachamamaradio",
  "limit": 50,
  "categoria": "Política"
}
```

### Filtros Disponibles

- **Cantidad**: 5, 10, 20, 50, 100, Sin límite
- **Fuente**: Específica o todas
- **Categoría**: Filtrar por categoría
- **Rango de fechas**: Desde-hasta
- **Tipo**: Últimas, Todas, Por fecha, Por fuente

### Control de Duplicados

El sistema previene duplicados normalizando URLs:
- Elimina trailing slashes
- Elimina query parameters
- Compara URLs normalizadas antes de insertar

### Trabajos en Background

Los scrapers se ejecutan en background tasks de FastAPI:
- No bloquean la API
- Progreso visible en tiempo real
- Logs detallados
- Estado persistente

---

## 🤖 Sistema de Limpieza con IA

### Modelos Disponibles

- **deepseek-r1:8b** (por defecto)
- Cualquier modelo compatible con Ollama

### Proceso de Limpieza

1. **Extracción**: Obtiene noticias de `noticias` o `noticias_limpia`
2. **Procesamiento**: Envía contenido a Ollama para análisis
3. **Análisis**: El modelo identifica párrafos relevantes e irrelevantes
4. **Almacenamiento**: Guarda resultados en `noticias_bert_clean`

### Funcionalidades

- **Limpieza de contenido**: Elimina párrafos irrelevantes
- **Análisis de relevancia**: Calcula porcentaje de relevancia
- **Separación de párrafos**: Identifica párrafos relevantes e irrelevantes
- **Múltiples modelos**: Soporte para diferentes modelos de IA
- **Prompts personalizados**: Permite personalizar el prompt de limpieza

### Endpoints

- `POST /api/nlp/limpiar`: Procesa noticias
- `GET /api/nlp/limpiadas`: Lista noticias procesadas
- `GET /api/nlp/limpiadas/{id}`: Detalle de noticia procesada
- `GET /api/nlp/public`: Vista pública (requiere plan)
- `GET /api/nlp/public/{id}`: Detalle público

### Configuración de Ollama

El sistema requiere Ollama corriendo localmente:

```bash
# Instalar Ollama
# https://ollama.ai

# Descargar modelo
ollama pull deepseek-r1:8b

# Iniciar Ollama
ollama serve
```

---

## 📦 Sistema de Migración de Datos

### Migración de `noticias` a `noticias_limpia`

El sistema incluye un proceso ETL completo para migrar y transformar datos:

#### Características

- **Extracción**: Lee datos de `noticias`
- **Transformación**:
  - Parsing de fechas
  - Procesamiento de imágenes
  - Limpieza de URLs
  - Extracción de dominio
  - Extracción de keywords
  - Categorización
  - Creación de resúmenes
  - Identificación de tipo de contenido
- **Carga**: Inserta en `noticias_limpia` con `ON CONFLICT DO NOTHING`

#### Ejecución

**Desde el Panel:**
1. Ir a `admin/scrapers.html`
2. Sección "Migración de Datos"
3. Click en "Iniciar Migración"
4. Ver progreso en tiempo real

**Desde la API:**
```http
POST /api/scrapers/migrate
Authorization: Bearer <token>
```

#### Progreso

- Barra de progreso visual
- Porcentaje completado
- Paso actual
- Logs detallados
- Resultados finales

---

## 💼 Sistema de Suscripciones y Planes

### Planes Disponibles

#### FREE (Gratis)
- Acceso al sitio web público
- Visualización de noticias
- Búsqueda básica
- Sin acceso a API
- Sin noticias con IA

#### PRO ($12/mes)
- Todo lo de FREE
- Acceso a API básica
- Búsqueda avanzada
- 2,000 noticias/día
- Hasta 5 fuentes
- Historial de 7 días

#### BUSINESS ($64/mes)
- Todo lo de PRO
- Scraping bajo demanda
- Sistema de alertas
- Dashboards avanzados
- Historial de 1 año
- Soporte prioritario

#### ENTERPRISE ($350/mes)
- Todo lo de BUSINESS
- Noticias procesadas con IA
- Scraping personalizado
- Integraciones personalizadas
- SLA garantizado
- Soporte 24/7

### Gestión de Planes

- Los planes se gestionan desde `admin/usuarios.html`
- Sincronización automática entre `usuarios` y `api_keys`
- Cambio de plan actualiza todas las API keys del usuario

---

## ⚙️ Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` en `scraping-project/`:

```env
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=news_db
DB_USER=postgres
DB_PASSWORD=tu_password

# JWT
JWT_SECRET_KEY=tu_secret_key_muy_seguro_aqui

# CORS
FRONTEND_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Ollama (para limpieza con IA)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b

# Redis (opcional)
REDIS_URL=redis://localhost:6379
```

### Pool de Conexiones

El sistema usa un pool de conexiones PostgreSQL:
- Tamaño mínimo: 5
- Tamaño máximo: 20
- Timeout: 30 segundos

### Logging

Los logs se guardan en:
- `scraping-project/logs/api.log`
- `scraping-project/logs/scraping.log`

Configurar nivel de logging en `api/main.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

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

#### Backend con Gunicorn

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend con Nginx

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    # Frontend
    location / {
        root /ruta/a/biznews;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker (Opcional)

```bash
cd scraping-project
docker-compose up -d
```

---

## 🐛 Solución de Problemas

### Error de CORS

**Problema:** `Access-Control-Allow-Origin` error

**Solución:**
1. Verificar `FRONTEND_ORIGINS` en `.env`
2. Verificar configuración en `api/main.py`
3. Asegurar que el frontend esté en un origen permitido

### Error de Base de Datos

**Problema:** No se puede conectar a PostgreSQL

**Solución:**
```bash
# Verificar que PostgreSQL esté corriendo
pg_isready

# Verificar credenciales en .env
# Verificar que la base de datos exista
psql -U postgres -l
```

### Error de Autenticación

**Problema:** Token inválido o expirado

**Solución:**
1. Verificar que `JWT_SECRET_KEY` esté configurado
2. Intentar refrescar el token
3. Iniciar sesión nuevamente

### Scrapers No Funcionan

**Problema:** Scrapers no insertan noticias

**Solución:**
1. Verificar que las dependencias estén instaladas (bs4, requests)
2. Verificar conectividad a las fuentes
3. Revisar logs en `logs/scraping.log`
4. Verificar que las URLs de las fuentes no hayan cambiado

### Limpieza con IA No Funciona

**Problema:** Error al procesar con Ollama

**Solución:**
1. Verificar que Ollama esté corriendo: `ollama list`
2. Verificar que el modelo esté descargado: `ollama pull deepseek-r1:8b`
3. Verificar `OLLAMA_BASE_URL` en configuración
4. Probar conexión: `curl http://localhost:11434/api/tags`

### Migración Falla

**Problema:** Error durante migración

**Solución:**
1. Verificar que `noticias` tenga datos
2. Verificar que `noticias_limpia` exista
3. Revisar logs de migración
4. Verificar espacio en disco

---

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

## 👥 Autores

- **Desarrollador Principal**: [Tu Nombre]
- **Minería de Datos**: Ciclo 8
- **Universidad**: [Nombre de la Universidad]

---

## 📞 Soporte

Para soporte técnico o preguntas:
- **Email**: [tu-email@ejemplo.com]
- **Issues**: [GitHub Issues]
- **Documentación**: Este README

---

## 🎯 Roadmap

### Versión 2.1
- [ ] Mejoras en UI/UX
- [ ] Optimización de rendimiento
- [ ] Más modelos de IA
- [ ] Exportación a más formatos

### Versión 3.0
- [ ] Aplicación móvil
- [ ] Integración con redes sociales
- [ ] Análisis de sentimientos
- [ ] Detección de fake news

---

**¡Gracias por usar BizNews! 🚀**

---

## 📚 Referencias Adicionales

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
- [Documentación de Ollama](https://ollama.ai/docs)
- [Documentación de Scrapy](https://docs.scrapy.org/)

---

*Última actualización: Enero 2025*
