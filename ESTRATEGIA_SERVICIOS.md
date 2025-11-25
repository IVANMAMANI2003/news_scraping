# 📋 Estrategia de Servicios - BizNews

## 🔍 Análisis del Sistema Actual

### Infraestructura Disponible

#### Backend API (FastAPI)
- **Endpoints de Noticias**: `/news`, `/news/{id}`, `/news/fuentes/{fuente}`, `/news/categorias/{categoria}`
- **Filtros Avanzados**: Por fecha, categoría, fuente, dominio, año, mes, día, keywords, imágenes
- **Metadatos**: `/news/fuentes/listar`, `/news/categorias/listar`
- **Búsqueda Avanzada**: `/api/advanced/search` con múltiples filtros
- **Sistema de Scraping**: `/api/scrapers` para ejecutar scrapers bajo demanda
- **Admin Panel**: CRUD completo para noticias, fuentes y categorías
- **Base de Datos**: PostgreSQL con tablas `noticias_limpia` (procesadas) y `noticias` (raw)

#### Frontend Público
- **Sitio Web**: Visualización de noticias por fuentes y categorías
- **Búsqueda Avanzada**: Filtros múltiples para usuarios
- **Reportes y Estadísticas**: Gráficas y análisis de datos
- **Responsive Design**: Accesible desde cualquier dispositivo

#### Fuentes de Datos
- Pachamama Radio
- Puno Noticias
- Los Andes
- Sin Fronteras

---

## 💼 Propuesta de Servicios

### 🟢 NIVEL 1: SERVICIO PÚBLICO GRATUITO (Web)

**Descripción**: Acceso web gratuito a noticias para usuarios finales.

**Características**:
- ✅ Acceso ilimitado al sitio web público
- ✅ Visualización de noticias por fuente y categoría
- ✅ Búsqueda básica en el sitio web
- ✅ Filtros de tiempo (hoy, semana, mes, año)
- ✅ Reportes y estadísticas públicas
- ✅ Sin necesidad de registro
- ✅ Sin límites de visualización

**Limitaciones**:
- ❌ No acceso a API
- ❌ No descarga de datos
- ❌ No scraping personalizado
- ❌ Sin historial de búsquedas guardadas

**Monetización**:
- Publicidad en el sitio web
- Patrocinios de contenido
- Banner ads

**Implementación**:
- Ya está implementado en `biznews/`
- Solo necesita optimización SEO y publicidad

---

### 🔵 NIVEL 2: API BÁSICA (FREE - Starter)

**Descripción**: API REST para desarrolladores que quieren integrar noticias en sus aplicaciones.

**Características Técnicas**:
```http
# Endpoints Disponibles
GET /news                    # Listar noticias (limitado)
GET /news/{id}              # Noticia específica
GET /news/fuentes/{fuente}  # Noticias por fuente
GET /news/categorias/{cat}  # Noticias por categoría
GET /news/fuentes/listar    # Listar fuentes
GET /news/categorias/listar # Listar categorías
```

**Límites**:
- 📊 **50 noticias/día** por API Key
- 🔑 **1 fuente** de noticias (seleccionable)
- 🔍 **Búsqueda simple** por categoría
- ⏱️ **Actualización**: Cada 3 horas
- 📝 **Formato**: JSON únicamente
- 🚫 **Sin historial**
- 🚫 **Sin webhooks**
- 🚫 **Sin descarga CSV**

**Implementación Necesaria**:
1. **Sistema de API Keys**:
   ```python
   # Crear tabla de API keys
   CREATE TABLE api_keys (
       id SERIAL PRIMARY KEY,
       key VARCHAR(255) UNIQUE,
       plan VARCHAR(50) DEFAULT 'free',
       user_email VARCHAR(255),
       created_at TIMESTAMP,
       requests_today INT DEFAULT 0,
       last_reset DATE,
       fuente_permitida VARCHAR(100),
       activo BOOLEAN DEFAULT true
   );
   ```

2. **Middleware de Autenticación**:
   ```python
   # En main.py o nuevo archivo auth.py
   from fastapi import Header, HTTPException
   
   async def verify_api_key(x_api_key: str = Header(...)):
       # Verificar key, límites, etc.
       pass
   ```

3. **Rate Limiting**:
   ```python
   # Contador de requests por día
   # Reset diario a medianoche
   ```

4. **Filtrado por Plan**:
   ```python
   # En news.py, agregar filtro de fuente según plan
   if plan == 'free' and api_key.fuente_permitida:
       where_conditions.append("fuente = %s")
   ```

**Precio**: **Gratis**

**Público Objetivo**:
- Estudiantes
- Proyectos personales
- Pruebas de concepto
- Apps experimentales

---

### 🟦 NIVEL 3: API PROFESIONAL (PRO - $10-15/mes)

**Descripción**: API completa para desarrolladores y pequeñas empresas.

**Características Técnicas**:
```http
# Todos los endpoints del plan FREE +
GET /api/advanced/search    # Búsqueda avanzada
GET /news?q=keyword         # Búsqueda por keywords
GET /news?date_from=...     # Filtros de fecha
GET /news?limit=100        # Más resultados
```

**Límites**:
- 📊 **2,000 noticias/día**
- 🔑 **Hasta 5 fuentes** simultáneas
- 🔍 **Palabras clave personalizadas** (hasta 20)
- ⏱️ **Actualización**: Cada 1 hora
- 📝 **Formatos**: JSON, CSV
- 📚 **Historial**: 7 días
- 🔔 **Webhooks**: 1 activo
- 📧 **Soporte**: Por email

**Implementación Necesaria**:
1. **Extender API Keys**:
   ```python
   ALTER TABLE api_keys ADD COLUMN max_sources INT DEFAULT 1;
   ALTER TABLE api_keys ADD COLUMN keywords TEXT[];
   ALTER TABLE api_keys ADD COLUMN webhook_url VARCHAR(500);
   ALTER TABLE api_keys ADD COLUMN historial_dias INT DEFAULT 0;
   ```

2. **Sistema de Webhooks**:
   ```python
   # Nuevo router: webhooks.py
   @router.post("/webhooks/trigger")
   async def trigger_webhook(api_key: str, event: str):
       # Enviar notificación HTTP POST al webhook_url
       pass
   ```

3. **Exportación CSV**:
   ```python
   @router.get("/news/export")
   async def export_news(format: str = "csv"):
       # Generar CSV/JSON y devolver
       pass
   ```

4. **Historial de Búsquedas**:
   ```python
   CREATE TABLE search_history (
       id SERIAL PRIMARY KEY,
       api_key_id INT,
       query_params JSONB,
       results_count INT,
       created_at TIMESTAMP
   );
   ```

**Precio**: **$10-15 USD/mes**

**Público Objetivo**:
- Startups
- Medios pequeños
- Investigadores
- Proyectos académicos

---

### 🟧 NIVEL 4: API EMPRESARIAL (BUSINESS - $49-79/mes)

**Descripción**: Solución completa para empresas que necesitan monitoreo en tiempo real.

**Características Técnicas**:
```http
# Todos los endpoints del plan PRO +
GET /api/metrics           # Métricas y estadísticas
GET /api/stats             # Estadísticas avanzadas
POST /api/scrapers/run     # Scraping bajo demanda (limitado)
```

**Límites**:
- 📊 **20,000 noticias/día**
- 🔑 **TODAS las fuentes** disponibles
- 🔍 **Palabras clave ilimitadas**
- ⏱️ **Actualización**: Cada 15 minutos
- 📝 **Formatos**: JSON, CSV, XML
- 📚 **Historial**: 1 año
- 🔔 **Webhooks**: Ilimitados
- 📊 **Dashboards**: Avanzados con gráficas
- 📧 **Soporte**: Prioritario

**Implementación Necesaria**:
1. **Sistema de Métricas**:
   ```python
   # Usar endpoints existentes en advanced.py
   # GET /api/metrics ya existe
   # Agregar más métricas personalizadas
   ```

2. **Scraping Bajo Demanda**:
   ```python
   # Ya existe en scrapers.py
   # Agregar límites según plan
   # Solo permitir para planes BUSINESS+
   ```

3. **Alertas por Email/Telegram/Slack**:
   ```python
   # Nuevo módulo: alerts.py
   @router.post("/alerts/create")
   async def create_alert(api_key: str, keywords: List[str], channels: List[str]):
       # Configurar alertas
       pass
   ```

4. **Dashboards Avanzados**:
   ```python
   # Endpoint para datos de gráficas
   @router.get("/api/dashboard/stats")
   async def get_dashboard_stats(api_key: str):
       # Retornar datos para gráficas
       pass
   ```

5. **Exportación XML**:
   ```python
   # Agregar formato XML a exportación
   ```

**Precio**: **$49-79 USD/mes**

**Público Objetivo**:
- Agencias de marketing
- Departamentos de comunicación
- Consultoras
- Analistas de datos

---

### 🟥 NIVEL 5: ENTERPRISE (A la Medida - $200-500+/mes)

**Descripción**: Soluciones personalizadas para grandes empresas.

**Características Técnicas**:
```http
# Todos los endpoints del plan BUSINESS +
POST /api/scrapers/custom  # Scraping personalizado
POST /api/integrations/db  # Integración con BD externa
POST /api/ai/analyze       # Análisis con IA
GET /api/export/bulk      # Exportación masiva
```

**Características Especiales**:
- 📊 **Noticias ilimitadas** (o límite personalizado)
- 🕷️ **Scraping personalizado** para nuevas páginas
- 🔗 **Integración** con bases de datos internas
- 🤖 **IA integrada**:
  - Resumen automático de noticias
  - Clasificación por sentimiento
  - Detección de entidades (personas, lugares, empresas)
- 📚 **Historial completo** de datos
- 📥 **Exportación masiva**: JSON, CSV, XML, Parquet
- ⏱️ **Frecuencia**: Cada 5 minutos
- 📊 **SLA garantizado**: 99.9%
- 🚀 **Escalado dedicado**
- 📞 **Soporte 24/7** y gestor de cuenta

**Implementación Necesaria**:
1. **Scraping Personalizado**:
   ```python
   # Extender scrapers.py
   @router.post("/api/scrapers/custom")
   async def create_custom_scraper(api_key: str, config: CustomScraperConfig):
       # Crear scraper dinámico según configuración
       pass
   ```

2. **Integración con IA**:
   ```python
   # Nuevo módulo: ai_analysis.py
   # Integrar con servicios de IA (OpenAI, Google AI, etc.)
   @router.post("/api/ai/analyze")
   async def analyze_news(news_ids: List[int], analysis_type: str):
       # Análisis de sentimiento, resumen, entidades
       pass
   ```

3. **Integración con Bases de Datos**:
   ```python
   # Nuevo módulo: integrations.py
   @router.post("/api/integrations/sync")
   async def sync_to_external_db(api_key: str, db_config: DatabaseConfig):
       # Sincronizar datos con BD externa
       pass
   ```

4. **Exportación Masiva**:
   ```python
   # Mejorar exportación para grandes volúmenes
   # Usar streaming para archivos grandes
   # Soporte para Parquet
   ```

5. **Sistema de SLA y Monitoreo**:
   ```python
   # Monitoreo de uptime
   # Alertas automáticas
   # Dashboard de métricas en tiempo real
   ```

**Precio**: **$200-500+ USD/mes** (personalizado)

**Público Objetivo**:
- Bancos
- Gobiernos
- Grandes corporaciones
- Medios internacionales

---

## 🛠️ Implementación Técnica Prioritaria

### Fase 1: Sistema de API Keys (CRÍTICO)
**Prioridad**: ALTA
**Tiempo estimado**: 1-2 semanas

1. Crear tabla de API keys
2. Middleware de autenticación
3. Rate limiting básico
4. Panel de administración de keys
5. Documentación de API

### Fase 2: Plan FREE
**Prioridad**: ALTA
**Tiempo estimado**: 1 semana

1. Implementar límites del plan FREE
2. Filtrado por fuente única
3. Contador de requests diarios
4. Página de registro para API keys

### Fase 3: Plan PRO
**Prioridad**: MEDIA
**Tiempo estimado**: 2-3 semanas

1. Múltiples fuentes
2. Sistema de webhooks
3. Exportación CSV
4. Historial de búsquedas

### Fase 4: Plan BUSINESS
**Prioridad**: MEDIA
**Tiempo estimado**: 3-4 semanas

1. Scraping bajo demanda
2. Sistema de alertas
3. Dashboards avanzados
4. Exportación XML

### Fase 5: Plan ENTERPRISE
**Prioridad**: BAJA (solo bajo demanda)
**Tiempo estimado**: Variable

1. Scraping personalizado
2. Integración con IA
3. Integraciones externas
4. Exportación masiva

---

## 📊 Modelo de Monetización

### Ingresos por Plan

| Plan | Precio/mes | Usuarios estimados | Ingreso mensual |
|------|-----------|-------------------|-----------------|
| FREE | $0 | 100-500 | $0 (publicidad) |
| PRO | $12 | 20-50 | $240-600 |
| BUSINESS | $64 | 5-15 | $320-960 |
| ENTERPRISE | $350 | 1-5 | $350-1,750 |
| **TOTAL** | | | **$910-3,310/mes** |

### Ingresos Adicionales

1. **Publicidad en sitio web**: $200-500/mes
2. **Servicios personalizados**: $500-2,000/mes (variable)
3. **Consultoría**: $100-200/hora

---

## 🎯 Estrategia de Lanzamiento

### Etapa 1: Validación (Mes 1-2)
- ✅ Lanzar sitio web público (ya está)
- ✅ Implementar plan FREE
- ✅ Obtener primeros 10-20 usuarios de API
- ✅ Recolectar feedback

### Etapa 2: Crecimiento (Mes 3-6)
- ✅ Lanzar plan PRO
- ✅ Marketing y promoción
- ✅ Mejorar documentación
- ✅ Objetivo: 50-100 usuarios API

### Etapa 3: Escalado (Mes 7-12)
- ✅ Lanzar plan BUSINESS
- ✅ Mejorar infraestructura
- ✅ Soporte profesional
- ✅ Objetivo: 200-500 usuarios API

### Etapa 4: Enterprise (Año 2+)
- ✅ Lanzar plan ENTERPRISE
- ✅ Servicios personalizados
- ✅ Expansión de fuentes
- ✅ Objetivo: 5-10 clientes enterprise

---

## 📝 Checklist de Implementación

### Sistema Base
- [ ] Crear tabla `api_keys` en PostgreSQL
- [ ] Middleware de autenticación API
- [ ] Rate limiting por API key
- [ ] Sistema de contadores diarios
- [ ] Panel admin para gestionar API keys

### Plan FREE
- [ ] Límite de 50 noticias/día
- [ ] Filtro por 1 fuente
- [ ] Reset diario de contadores
- [ ] Página de registro/obtener API key

### Plan PRO
- [ ] Múltiples fuentes (hasta 5)
- [ ] Sistema de webhooks
- [ ] Exportación CSV
- [ ] Historial de 7 días
- [ ] Sistema de pagos (Stripe/PayPal)

### Plan BUSINESS
- [ ] Scraping bajo demanda
- [ ] Sistema de alertas
- [ ] Dashboards avanzados
- [ ] Exportación XML
- [ ] Historial de 1 año

### Plan ENTERPRISE
- [ ] Scraping personalizado
- [ ] Integración con IA
- [ ] Integraciones externas
- [ ] Exportación masiva
- [ ] SLA y monitoreo

### Documentación
- [ ] Documentación de API (Swagger/OpenAPI)
- [ ] Guías de integración
- [ ] Ejemplos de código
- [ ] FAQ
- [ ] Términos y condiciones

### Marketing
- [ ] Página de precios (ya está)
- [ ] Landing page para desarrolladores
- [ ] Blog con casos de uso
- [ ] Redes sociales
- [ ] Email marketing

---

## 🔐 Consideraciones de Seguridad

1. **API Keys**: Almacenar hasheadas (bcrypt)
2. **Rate Limiting**: Por IP y por API key
3. **CORS**: Configurar correctamente
4. **Validación**: Validar todos los inputs
5. **Logging**: Registrar todas las requests
6. **Monitoreo**: Alertas de uso anormal
7. **Backup**: Backup diario de base de datos

---

## 📈 Métricas a Monitorear

1. **Uso de API**:
   - Requests por día/mes
   - Endpoints más usados
   - Errores y timeouts
   - Tiempo de respuesta

2. **Usuarios**:
   - Registros nuevos
   - Conversión FREE → PRO
   - Churn rate
   - Lifetime value

3. **Infraestructura**:
   - Uptime
   - Latencia
   - Uso de recursos
   - Costos de servidor

---

## 🚀 Próximos Pasos Inmediatos

1. **Crear sistema de API Keys** (1-2 semanas)
2. **Implementar plan FREE** (1 semana)
3. **Crear página de registro** (3 días)
4. **Documentación básica** (1 semana)
5. **Beta testing** con 5-10 usuarios (2 semanas)

---

## 💡 Recomendaciones Adicionales

1. **Empezar Simple**: Lanzar plan FREE primero, luego agregar planes
2. **Feedback Continuo**: Recolectar feedback de usuarios constantemente
3. **Documentación Clara**: Invertir tiempo en buena documentación
4. **Soporte Rápido**: Responder preguntas rápidamente al inicio
5. **Casos de Uso**: Mostrar ejemplos reales de uso
6. **Comunidad**: Crear comunidad de desarrolladores (Discord/Slack)
7. **Blog Técnico**: Escribir sobre casos de uso y tutoriales

---

**Fecha de creación**: 2025-01-17
**Versión**: 1.0

