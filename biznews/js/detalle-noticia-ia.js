/**
 * Detalle de Noticia con IA
 * Carga y muestra los detalles de una noticia procesada con IA
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

// Obtener ID de la URL
function getNewsIdFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    if (!id) {
        throw new Error('ID de noticia no proporcionado');
    }
    return id;
}

// Formatear fecha
function formatDate(dateStr) {
    if (!dateStr) return "Fecha no disponible";
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return String(dateStr);
        return d.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return String(dateStr);
    }
}

// Formatear contenido limpio
function formatCleanContent(content) {
    if (!content) return '';
    // Dividir por párrafos (doble salto de línea)
    const paragraphs = content.split(/\n\n+/).filter(p => p.trim());
    return paragraphs.map(p => `<p>${p.trim()}</p>`).join('');
}

// Obtener token de autenticación
function getAuthToken() {
    // Intentar obtener token de publicAuthManager
    if (window.publicAuthManager) {
        const token = window.publicAuthManager.getAccessToken();
        if (token) return token;
    }
    
    // Intentar obtener token de authManager (admin)
    if (window.authManager) {
        const token = window.authManager.getAccessToken();
        if (token) return token;
    }
    
    // Intentar obtener directamente de localStorage
    try {
        const publicSession = localStorage.getItem('biznews_session');
        if (publicSession) {
            const session = JSON.parse(publicSession);
            if (session.access_token) return session.access_token;
        }
        
        const adminSession = localStorage.getItem('biznews_admin_session');
        if (adminSession) {
            const session = JSON.parse(adminSession);
            if (session.access_token) return session.access_token;
        }
    } catch (e) {
        // Ignorar errores
    }
    
    return null;
}

// Cargar noticia con IA
async function loadNoticiaIA() {
    const container = document.getElementById('article-container');
    if (!container) return;

    try {
        const noticiaId = getNewsIdFromURL();
        console.log('📡 Cargando noticia con IA ID:', noticiaId);

        // Incluir token de autenticación
        const token = getAuthToken();
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}/api/nlp/public/${noticiaId}`, { headers });
        
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Se requiere autenticación para acceder a las noticias con IA');
            } else if (response.status === 403) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'No tienes permisos para acceder a esta funcionalidad');
            } else if (response.status === 404) {
                throw new Error('Noticia con IA no encontrada');
            }
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }

        const noticia = await response.json();
        console.log('✅ Noticia cargada:', noticia);

        renderNoticia(noticia);
        
    } catch (error) {
        console.error('❌ Error cargando noticia:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4><i class="fas fa-exclamation-triangle me-2"></i>Error</h4>
                <p>${error.message}</p>
                <a href="noticias-ia.html" class="btn btn-primary mt-3">
                    <i class="fas fa-arrow-left me-2"></i>Volver a Noticias con IA
                </a>
            </div>
        `;
    }
}

// Renderizar noticia
function renderNoticia(noticia) {
    const container = document.getElementById('article-container');
    if (!container) return;

    const imagen = noticia.imagen_principal || '../img/news-700x435-1.jpg';
    const categoria = noticia.categoria || 'General';
    const fecha = formatDate(noticia.fecha);
    const fuente = noticia.fuente || 'Fuente desconocida';
    const autor = noticia.autor || 'Autor no disponible';
    
    // Calcular porcentaje de relevancia
    const porcentaje = noticia.porcentaje_relevancia || 0;
    let relevanciaClass = 'baja';
    let relevanciaText = 'Baja Relevancia';
    if (porcentaje >= 70) {
        relevanciaClass = 'alta';
        relevanciaText = 'Alta Relevancia';
    } else if (porcentaje >= 50) {
        relevanciaClass = 'media';
        relevanciaText = 'Media Relevancia';
    }

    // Contenido limpio
    const contenidoLimpio = formatCleanContent(noticia.contenido_limpio || noticia.resumen || 'Contenido no disponible');

    // Párrafos relevantes
    const parrafosRelevantesHTML = noticia.parrafos_relevantes && noticia.parrafos_relevantes.length > 0
        ? `
            <div class="parrafos-relevantes">
                <h3>
                    <i class="fas fa-check-circle"></i>
                    Párrafos Relevantes (${noticia.parrafos_relevantes.length})
                </h3>
                ${noticia.parrafos_relevantes.map((p, idx) => `
                    <div class="parrafo-relevante">
                        <strong class="text-success">Párrafo ${idx + 1}:</strong>
                        <p class="mb-0 mt-1">${p}</p>
                    </div>
                `).join('')}
            </div>
        `
        : '';

    // Estadísticas
    const statsHTML = `
        <div class="stats-section">
            <h4 class="mb-3"><i class="fas fa-chart-bar me-2"></i>Estadísticas de Procesamiento</h4>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value text-success">${noticia.num_parrafos_relevantes || 0}</div>
                    <div class="stat-label">Párrafos Relevantes</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value text-danger">${noticia.num_parrafos_irrelevantes || 0}</div>
                    <div class="stat-label">Párrafos Irrelevantes</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value text-primary">${noticia.num_parrafos_total || 0}</div>
                    <div class="stat-label">Total de Párrafos</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: ${porcentaje >= 70 ? '#10b981' : porcentaje >= 50 ? '#f59e0b' : '#ef4444'}">
                        ${porcentaje.toFixed(1)}%
                    </div>
                    <div class="stat-label">% Relevancia</div>
                </div>
            </div>
        </div>
    `;

    // Keywords/Tags
    const keywords = noticia.keywords ? noticia.keywords.split(/[|,;\n]/).map(k => k.trim()).filter(Boolean) : [];
    const tagsHTML = keywords.length > 0
        ? `
            <div class="mt-4">
                <strong class="d-block mb-2"><i class="fas fa-tags me-2"></i>Etiquetas:</strong>
                <div class="d-flex flex-wrap gap-2">
                    ${keywords.map(k => `
                        <span class="badge bg-secondary">${k}</span>
                    `).join('')}
                </div>
            </div>
        `
        : '';

    const html = `
        <div class="article-header">
            <img src="${imagen}" alt="${noticia.titulo}" class="article-image" 
                 onerror="this.src='../img/news-700x435-1.jpg'">
            <div class="article-header-content">
                <span class="article-category">${categoria}</span>
                <h1 class="article-title">${noticia.titulo || 'Sin título'}</h1>
                <div class="d-flex flex-wrap gap-3 align-items-center mb-3">
                    <span class="ai-badge">
                        <i class="fas fa-robot"></i>
                        Procesado con ${noticia.modelo_usado || 'IA'}
                    </span>
                    <span class="relevancia-badge ${relevanciaClass}">
                        <i class="fas fa-chart-line"></i>
                        ${relevanciaText} (${porcentaje.toFixed(1)}%)
                    </span>
                </div>
                <div class="article-meta">
                    <div class="article-meta-item">
                        <i class="fas fa-calendar"></i>
                        <span>${fecha}</span>
                    </div>
                    <div class="article-meta-item">
                        <i class="fas fa-newspaper"></i>
                        <span>${fuente}</span>
                    </div>
                    <div class="article-meta-item">
                        <i class="fas fa-user"></i>
                        <span>${autor}</span>
                    </div>
                    ${noticia.url ? `
                        <div class="article-meta-item">
                            <i class="fas fa-external-link-alt"></i>
                            <a href="${noticia.url}" target="_blank" class="text-decoration-none">Ver original</a>
                        </div>
                    ` : ''}
                </div>
                ${noticia.resumen ? `
                    <div class="article-summary">
                        <strong><i class="fas fa-quote-left me-2"></i>Resumen:</strong>
                        <p class="mb-0 mt-2">${noticia.resumen}</p>
                    </div>
                ` : ''}
            </div>
        </div>

        <div class="article-content">
            <h2 class="mb-4">
                <i class="fas fa-magic me-2 text-primary"></i>
                Contenido Limpio Procesado con IA
            </h2>
            <div class="article-text">
                ${contenidoLimpio || '<p class="text-muted">Contenido no disponible</p>'}
            </div>
            
            ${parrafosRelevantesHTML}
            
            ${statsHTML}
            
            ${tagsHTML}
        </div>

        <div class="text-center mt-4">
            <a href="noticias-ia.html" class="btn btn-primary btn-lg">
                <i class="fas fa-arrow-left me-2"></i>
                Volver a Noticias con IA
            </a>
        </div>
    `;

    container.innerHTML = html;

    // Actualizar título de la página
    document.title = `${noticia.titulo || 'Noticia con IA'} - BizNews`;
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    loadNoticiaIA();
});

