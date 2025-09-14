# 🌐 BizNews Frontend

Interfaz web responsive para el sistema de noticias BizNews, construida con HTML5, CSS3, JavaScript y Chart.js.

## 🚀 Inicio Rápido

### Opción 1: Servidor Python (Recomendado)

```bash
# Navegar al directorio frontend
cd biznews

# Iniciar servidor HTTP local
python serve.py

# Abrir en navegador
# http://localhost:8080
```

### Opción 2: Script Batch (Windows)

```bash
# Doble clic en el archivo
start_server.bat

# O desde terminal
cd biznews
start_server.bat
```

### Opción 3: Servidor HTTP Simple

```bash
# Python 3
python -m http.server 8080

# Python 2
python -m SimpleHTTPServer 8080
```

## 📁 Estructura del Proyecto

```
biznews/
├── index.html              # Página principal
├── fuentes.html            # Página de fuentes de noticias
├── categorias.html         # Página de categorías
├── reportes.html           # Dashboard de estadísticas
├── detalle_noticias.html   # Página de noticia individual
├── contact.html            # Página de contacto
├── serve.py               # Servidor HTTP local
├── start_server.bat       # Script de inicio (Windows)
├── js/                    # JavaScript
│   ├── news-api.js        # Cliente de API
│   ├── fuentes.js         # Lógica de fuentes
│   ├── categorias.js      # Lógica de categorías
│   └── reportes.js        # Gráficas y estadísticas
├── css/                   # Estilos
│   ├── style.css          # Estilos principales
│   ├── custom-fixes.css   # Correcciones personalizadas
│   └── reportes.css       # Estilos de reportes
├── img/                   # Imágenes y assets
├── lib/                   # Librerías externas
│   ├── owlcarousel/       # Carousel responsive
│   └── easing/            # Animaciones
└── scss/                  # Archivos SCSS (opcional)
```

## 🎨 Páginas Disponibles

### 🏠 Portada (`index.html`)
- **Noticias destacadas**: Carousel con últimas noticias
- **Noticias de Puno**: Sección especializada con 4 noticias
- **Noticias Trending**: Lista de noticias populares
- **Navegación**: Menú principal con enlaces a todas las secciones

### 📰 Fuentes (`fuentes.html`)
- **Tarjetas de fuentes**: Visualización por fuente de noticias
- **Filtros de tiempo**: Hoy, semana, mes, año
- **Conteo dinámico**: Número real de noticias por fuente
- **Enlaces directos**: Acceso a noticias de cada fuente

### 📂 Categorías (`categorias.html`)
- **Tarjetas de categorías**: Organización por temas
- **Filtros de tiempo**: Filtrado por período
- **Conteo preciso**: Estadísticas actualizadas
- **Navegación intuitiva**: Acceso fácil a contenido

### 📊 Reportes (`reportes.html`)
- **5 Gráficas interactivas**:
  - 🍩 Noticias por Fuente (Dona)
  - 📊 Noticias por Categoría (Barras)
  - 📈 Tendencia Mensual (Línea)
  - 🎯 Días de la Semana (Polar)
  - 🏆 Top 10 Noticias (Barras horizontales)
- **Resumen estadístico**: Métricas clave
- **Botón de actualización**: Recargar datos
- **Responsive**: Adaptable a móviles

### 📄 Detalle de Noticias (`detalle_noticias.html`)
- **Contenido completo**: Artículo completo
- **Metadatos**: Fecha, autor, fuente, categoría
- **Imágenes**: Galería de imágenes
- **Navegación**: Enlaces relacionados

## 🔧 Configuración

### Variables de Configuración

Editar en `js/news-api.js`:

```javascript
const API_BASE_URL = 'http://127.0.0.1:8000';  // URL del backend
```

### CORS (Cross-Origin Resource Sharing)

El backend debe estar configurado para permitir requests desde:
- `http://localhost:8080`
- `http://127.0.0.1:8080`
- `file://` (para desarrollo local)

## 📱 Responsive Design

### Breakpoints
- **Desktop**: > 1200px
- **Tablet**: 768px - 1199px
- **Mobile**: < 768px

### Características Responsive
- **Grid adaptativo**: Se ajusta al tamaño de pantalla
- **Menú colapsable**: Hamburger menu en móviles
- **Gráficas responsivas**: Chart.js se adapta al contenedor
- **Imágenes optimizadas**: Carga diferida y tamaños apropiados

## 🎯 Funcionalidades JavaScript

### `news-api.js`
- **Cliente de API**: Comunicación con backend
- **Filtros de contenido**: Limpieza de HTML problemático
- **Manejo de imágenes**: Procesamiento de URLs de imágenes
- **Cache local**: Almacenamiento temporal de datos

### `fuentes.js`
- **Carga de fuentes**: Obtención de fuentes disponibles
- **Filtros de tiempo**: Implementación de filtros temporales
- **Conteo dinámico**: Cálculo de noticias por fuente
- **Renderizado**: Generación de tarjetas de fuentes

### `categorias.js`
- **Carga de categorías**: Obtención de categorías disponibles
- **Filtros de tiempo**: Filtrado por período
- **Conteo preciso**: Estadísticas actualizadas
- **Renderizado**: Generación de tarjetas de categorías

### `reportes.js`
- **Gráficas interactivas**: Chart.js para visualizaciones
- **Procesamiento de datos**: Transformación de datos para gráficas
- **Control de tamaño**: Prevención de agrandamiento de gráficas
- **Actualización**: Botón para recargar datos

## 🎨 Estilos CSS

### `style.css`
- **Bootstrap personalizado**: Tema adaptado para noticias
- **Componentes**: Tarjetas, botones, formularios
- **Layout**: Grid system y flexbox
- **Tipografía**: Fuentes y jerarquía visual

### `custom-fixes.css`
- **Correcciones específicas**: Ajustes para el proyecto
- **Overflow**: Control de desbordamiento de texto
- **Spacing**: Márgenes y padding personalizados
- **Responsive**: Ajustes para móviles

### `reportes.css`
- **Contenedores de gráficas**: Tamaños fijos para Chart.js
- **Responsive charts**: Adaptación a diferentes pantallas
- **Overflow control**: Prevención de desbordamiento
- **Mobile optimization**: Optimización para móviles

## 🔌 Integración con Backend

### Endpoints Utilizados

```javascript
// Noticias
GET /news                           // Listar noticias
GET /news/{id}                     // Noticia específica
GET /news/fuentes/{fuente}         // Noticias por fuente
GET /news/categorias/{categoria}   // Noticias por categoría

// Metadatos
GET /news/fuentes/listar           // Listar fuentes
GET /news/categorias/listar        // Listar categorías
```

### Manejo de Errores

```javascript
// Ejemplo de manejo de errores
try {
    const response = await fetch(`${API_BASE_URL}/news`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
} catch (error) {
    console.error('Error fetching data:', error);
    // Mostrar mensaje de error al usuario
}
```

## 🚀 Optimizaciones

### Rendimiento
- **Lazy loading**: Carga diferida de imágenes
- **Debouncing**: Evitar requests excesivos
- **Cache**: Almacenamiento temporal de datos
- **Minificación**: Archivos CSS/JS optimizados

### SEO
- **Meta tags**: Descripción y keywords
- **Semantic HTML**: Estructura semántica
- **Alt text**: Texto alternativo para imágenes
- **URLs amigables**: Enlaces descriptivos

### Accesibilidad
- **ARIA labels**: Etiquetas para lectores de pantalla
- **Keyboard navigation**: Navegación por teclado
- **Color contrast**: Contraste adecuado
- **Focus indicators**: Indicadores de foco

## 🐛 Solución de Problemas

### Error de CORS
```bash
# Verificar que el backend esté corriendo
curl http://127.0.0.1:8000/news

# Verificar configuración CORS en backend
```

### Error de Gráficas
```bash
# Verificar que Chart.js esté cargado
# Abrir DevTools > Console
# Debe mostrar: "Chart.js loaded"
```

### Error de Imágenes
```bash
# Verificar que las imágenes existan
# Verificar permisos de archivos
# Verificar rutas relativas
```

## 📊 Monitoreo

### Métricas de Rendimiento
- **Tiempo de carga**: < 3 segundos
- **Tamaño de página**: < 2MB
- **Requests HTTP**: < 20 por página
- **Tiempo de API**: < 500ms

### Herramientas de Debug
- **Console logs**: Información de debug
- **Network tab**: Monitoreo de requests
- **Performance tab**: Análisis de rendimiento
- **Lighthouse**: Auditoría de calidad

## 🔄 Actualizaciones

### Versionado
- **v1.0**: Versión inicial
- **v1.1**: Agregado sistema de reportes
- **v1.2**: Mejoras en responsive design
- **v1.3**: Optimizaciones de rendimiento

### Changelog
```markdown
## v1.3.0
- ✅ Corregido problema de gráficas que se agrandan
- ✅ Mejorado responsive design
- ✅ Agregado botón de actualización en reportes
- ✅ Optimizado rendimiento de carga

## v1.2.0
- ✅ Agregado sistema de filtros de tiempo
- ✅ Implementado conteo dinámico de noticias
- ✅ Mejorado manejo de errores de API
- ✅ Agregado sistema de reportes con Chart.js
```

## 🤝 Contribución

### Estándares de Código
- **JavaScript**: ES6+ con async/await
- **CSS**: BEM methodology
- **HTML**: Semantic markup
- **Comentarios**: JSDoc para funciones

### Proceso de Desarrollo
1. Fork del repositorio
2. Crear rama feature
3. Implementar cambios
4. Testing local
5. Pull request

## 📞 Soporte

Para soporte técnico:
- **Issues**: GitHub Issues
- **Email**: [tu-email@ejemplo.com]
- **Documentación**: README principal

---

**¡Disfruta usando BizNews Frontend! 🚀**