/**
 * Noticias con IA - Sistema para mostrar noticias procesadas con IA
 * Carga noticias de la tabla noticias_bert_clean con relación a noticias_limpia
 */

const API_BASE_URL = 'http://127.0.0.1:8000';
const ITEMS_PER_PAGE = 12;

class NoticiasIASystem {
    constructor() {
        this.currentCategory = 'all';
        this.currentPage = 1;
        this.totalPages = 1;
        this.categories = [];
        this.news = [];
        
        this.init();
    }

    async init() {
        console.log('🤖 Inicializando sistema de Noticias con IA...');
        
        // Verificar acceso del usuario
        const hasAccess = await this.checkAccess();
        if (!hasAccess) {
            return; // El método checkAccess ya muestra el mensaje de error
        }
        
        await this.loadCategories();
        await this.loadNews();
    }
    
    /**
     * Obtener token de autenticación (puede ser de publicAuthManager o authManager)
     */
    getAuthToken() {
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

    /**
     * Verificar si el usuario tiene acceso a noticias con IA
     */
    async checkAccess() {
        const container = document.getElementById('news-container');
        if (!container) return false;
        
        try {
            // Obtener token
            const token = this.getAuthToken();
            if (!token) {
                container.innerHTML = `
                    <div class="alert alert-warning text-center" style="max-width: 600px; margin: 2rem auto;">
                        <i class="fas fa-lock fa-3x mb-3 text-warning"></i>
                        <h4>Acceso Restringido</h4>
                        <p>Esta funcionalidad requiere autenticación y un plan Enterprise o Premium.</p>
                        <p class="mb-3">Por favor, <a href="login.html">inicia sesión</a> o <a href="servicios.html">actualiza tu plan</a> para acceder a las noticias procesadas con IA.</p>
                        <a href="login.html" class="btn btn-primary me-2">
                            <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
                        </a>
                        <a href="servicios.html" class="btn btn-outline-primary">
                            <i class="fas fa-crown me-2"></i>Ver Planes
                        </a>
                    </div>
                `;
                return false;
            }
            
            // Verificar plan del usuario
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                container.innerHTML = `
                    <div class="alert alert-warning text-center" style="max-width: 600px; margin: 2rem auto;">
                        <i class="fas fa-lock fa-3x mb-3 text-warning"></i>
                        <h4>Acceso Restringido</h4>
                        <p>No se pudo verificar tu autenticación. Por favor, <a href="login.html">inicia sesión</a> nuevamente.</p>
                    </div>
                `;
                return false;
            }
            
            const user = await response.json();
            const userPlan = (user.plan || 'free').toLowerCase();
            const userRole = (user.rol || 'user').toLowerCase();
            
            // Solo admin, enterprise y premium tienen acceso
            if (userRole === 'admin' || userPlan === 'enterprise' || userPlan === 'premium') {
                return true;
            }
            
            container.innerHTML = `
                <div class="alert alert-warning text-center" style="max-width: 600px; margin: 2rem auto;">
                    <i class="fas fa-crown fa-3x mb-3 text-warning"></i>
                    <h4>Plan Requerido</h4>
                    <p>Esta funcionalidad solo está disponible para usuarios con plan <strong>Enterprise</strong> o <strong>Premium</strong>.</p>
                    <p class="mb-3">Tu plan actual: <strong>${userPlan.toUpperCase()}</strong></p>
                    <a href="servicios.html" class="btn btn-primary">
                        <i class="fas fa-crown me-2"></i>Actualizar Plan
                    </a>
                </div>
            `;
            return false;
            
        } catch (error) {
            console.error('Error verificando acceso:', error);
            container.innerHTML = `
                <div class="alert alert-danger text-center" style="max-width: 600px; margin: 2rem auto;">
                    <i class="fas fa-exclamation-triangle fa-3x mb-3 text-danger"></i>
                    <h4>Error</h4>
                    <p>Ocurrió un error al verificar tu acceso. Por favor, intenta nuevamente.</p>
                </div>
            `;
            return false;
        }
    }

    /**
     * Cargar categorías disponibles
     */
    async loadCategories() {
        try {
            const response = await fetch(`${API_BASE_URL}/news/categorias/listar`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const categories = await response.json();
            this.categories = Array.isArray(categories) ? categories : [];
            
            this.renderCategoryFilters();
            console.log('✅ Categorías cargadas:', this.categories.length);
        } catch (error) {
            console.error('❌ Error cargando categorías:', error);
            this.categories = [];
        }
    }

    /**
     * Renderizar filtros de categorías
     */
    renderCategoryFilters() {
        const container = document.getElementById('categoryFilters');
        if (!container) return;

        // Botón "Todas" ya existe, agregar categorías
        this.categories.forEach(category => {
            const btn = document.createElement('button');
            btn.className = 'filter-btn';
            btn.setAttribute('data-category', category);
            btn.innerHTML = `<i class="fas fa-tag"></i> ${category}`;
            btn.addEventListener('click', () => this.filterByCategory(category));
            container.appendChild(btn);
        });

        // Agregar listener al botón "Todas"
        const allBtn = container.querySelector('[data-category="all"]');
        if (allBtn) {
            allBtn.addEventListener('click', () => this.filterByCategory('all'));
        }
    }

    /**
     * Filtrar por categoría
     */
    filterByCategory(category) {
        this.currentCategory = category;
        this.currentPage = 1;
        
        // Actualizar botones activos
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-category') === category) {
                btn.classList.add('active');
            }
        });

        this.loadNews();
    }

    /**
     * Cargar noticias con IA
     */
    async loadNews() {
        const container = document.getElementById('news-container');
        if (!container) return;

        // Mostrar loading
        container.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p>Cargando noticias con IA...</p>
            </div>
        `;

        try {
            // Construir URL con parámetros
            let url = `${API_BASE_URL}/api/nlp/public?limit=${ITEMS_PER_PAGE}&skip=${(this.currentPage - 1) * ITEMS_PER_PAGE}&order=desc`;
            
            if (this.currentCategory !== 'all') {
                url += `&categoria=${encodeURIComponent(this.currentCategory)}`;
            }

            console.log('📡 Cargando noticias desde:', url);
            // Incluir token de autenticación si está disponible
            const token = this.getAuthToken();
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch(url, { headers });
            
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Se requiere autenticación para acceder a las noticias con IA');
                } else if (response.status === 403) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'No tienes permisos para acceder a esta funcionalidad');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ Noticias cargadas:', data.items.length, 'de', data.total);

            this.news = data.items;
            this.totalPages = Math.ceil(data.total / ITEMS_PER_PAGE);

            this.renderNews();
            this.renderPagination();
        } catch (error) {
            console.error('❌ Error cargando noticias:', error);
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error al cargar noticias</h3>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Renderizar noticias
     */
    renderNews() {
        const container = document.getElementById('news-container');
        if (!container) return;

        if (this.news.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <h3>No hay noticias disponibles</h3>
                    <p>No se encontraron noticias con IA para esta categoría.</p>
                </div>
            `;
            return;
        }

        const newsHTML = this.news.map(noticia => this.renderNewsCard(noticia)).join('');
        container.innerHTML = `<div class="row">${newsHTML}</div>`;
    }

    /**
     * Renderizar tarjeta de noticia
     */
    renderNewsCard(noticia) {
        const imagen = noticia.imagen_principal || '../img/news-700x435-1.jpg';
        const categoria = noticia.categoria || 'General';
        const fecha = noticia.fecha ? new Date(noticia.fecha).toLocaleDateString('es-ES') : 'Fecha no disponible';
        const fuente = noticia.fuente || 'Fuente desconocida';
        
        // Calcular porcentaje de relevancia
        const porcentaje = noticia.porcentaje_relevancia || 0;
        let relevanciaClass = 'baja';
        let relevanciaText = 'Baja';
        if (porcentaje >= 70) {
            relevanciaClass = 'alta';
            relevanciaText = 'Alta';
        } else if (porcentaje >= 50) {
            relevanciaClass = 'media';
            relevanciaText = 'Media';
        }

        // Resumen o contenido limpio
        const resumen = noticia.resumen || 
                       (noticia.contenido_limpio ? noticia.contenido_limpio.substring(0, 1150) + '...' : 'Sin resumen disponible');

        // URL para detalle de noticia con IA
        const detalleUrl = `detalle-noticia-ia.html?id=${noticia.noticia_id}`;

        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="news-card">
                    <img src="${imagen}" alt="${noticia.titulo}" class="news-image" 
                         onerror="this.src='../img/news-700x435-1.jpg'">
                    <div class="news-content">
                        <span class="news-category">${categoria}</span>
                        <h3 class="news-title">
                            <a href="${detalleUrl}">${noticia.titulo || 'Sin título'}</a>
                        </h3>
                        <p class="news-summary">${resumen}</p>
                        <div class="news-meta">
                            <div class="news-meta-item">
                                <i class="fas fa-calendar"></i>
                                <span>${fecha}</span>
                            </div>
                            <div class="news-meta-item">
                                <i class="fas fa-newspaper"></i>
                                <span>${fuente}</span>
                            </div>
                        </div>
                        <div class="mt-2 d-flex gap-2 flex-wrap">
                            <span class="ai-indicator">
                                <i class="fas fa-robot"></i>
                                ${noticia.modelo_usado || 'IA'}
                            </span>
                            <span class="relevancia-badge ${relevanciaClass}">
                                <i class="fas fa-chart-line"></i>
                                ${relevanciaText} (${porcentaje.toFixed(0)}%)
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderizar paginación
     */
    renderPagination() {
        const container = document.getElementById('pagination');
        if (!container) return;

        if (this.totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let paginationHTML = '';

        // Botón anterior
        paginationHTML += `
            <button class="page-btn" ${this.currentPage === 1 ? 'disabled' : ''} 
                    onclick="noticiasIASystem.goToPage(${this.currentPage - 1})">
                <i class="fas fa-chevron-left"></i> Anterior
            </button>
        `;

        // Números de página
        const maxPages = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxPages / 2));
        let endPage = Math.min(this.totalPages, startPage + maxPages - 1);

        if (endPage - startPage < maxPages - 1) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }

        if (startPage > 1) {
            paginationHTML += `<button class="page-btn" onclick="noticiasIASystem.goToPage(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += `<span class="page-btn" style="border: none; cursor: default;">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="page-btn ${i === this.currentPage ? 'active' : ''}" 
                        onclick="noticiasIASystem.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                paginationHTML += `<span class="page-btn" style="border: none; cursor: default;">...</span>`;
            }
            paginationHTML += `
                <button class="page-btn" onclick="noticiasIASystem.goToPage(${this.totalPages})">
                    ${this.totalPages}
                </button>
            `;
        }

        // Botón siguiente
        paginationHTML += `
            <button class="page-btn" ${this.currentPage === this.totalPages ? 'disabled' : ''} 
                    onclick="noticiasIASystem.goToPage(${this.currentPage + 1})">
                Siguiente <i class="fas fa-chevron-right"></i>
            </button>
        `;

        container.innerHTML = paginationHTML;
    }

    /**
     * Ir a página específica
     */
    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.loadNews();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Inicializar sistema cuando el DOM esté listo
let noticiasIASystem;
document.addEventListener('DOMContentLoaded', () => {
    noticiasIASystem = new NoticiasIASystem();
});

