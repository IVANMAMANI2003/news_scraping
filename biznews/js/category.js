/**
 * BizNews Category Page - Sistema Profesional de Noticias
 * Versión completamente reescrita desde cero
 * 
 * @author BizNews Team
 * @version 2.0.0
 * @description Sistema robusto para mostrar noticias por fuente y categoría
 */

class NewsCategorySystem {
    constructor() {
        // Configuración del sistema
        this.config = {
            apiBaseUrl: 'http://127.0.0.1:8000',
            itemsPerPage: 20,
            maxRetries: 3,
            retryDelay: 1000,
            imageProxy: 'https://images.weserv.nl/?url=',
            defaultImage: 'img/news-700x435-1.jpg',
            animationDuration: 300,
            debounceDelay: 300
        };

        // Estado del sistema
        this.state = {
            currentFilter: 'all',
            currentNews: [],
            isLoading: false,
            hasError: false,
            lastUpdate: null,
            retryCount: 0
        };

        // Cache para optimización
        this.cache = {
            news: new Map(),
            metadata: new Map(),
            lastFetch: new Map()
        };

        // Elementos DOM
        this.elements = {
            pageTitle: document.getElementById('page-title'),
            pageSubtitle: document.getElementById('page-subtitle'),
            totalNews: document.getElementById('total-news'),
            totalSources: document.getElementById('total-sources'),
            totalCategories: document.getElementById('total-categories'),
            newsContainer: document.getElementById('news-container'),
            trendingNews: document.getElementById('trending-news'),
            popularCategories: document.getElementById('popular-categories'),
            filterButtons: document.querySelectorAll('.filter-btn')
        };

        // Inicializar el sistema
        this.init();
    }

    /**
     * Inicializar el sistema
     */
    async init() {
        try {
            console.log('🚀 Inicializando NewsCategorySystem...');
            
            // Obtener parámetros de la URL
            const params = this.getUrlParams();
            console.log('📋 Parámetros de URL:', params);

            // Configurar la página
            this.setupPage(params);

            // Configurar event listeners
            this.setupEventListeners();

            // Cargar datos iniciales
            await this.loadInitialData(params);

            // Configurar actualizaciones automáticas
            this.setupAutoRefresh();

            console.log('✅ Sistema inicializado correctamente');

        } catch (error) {
            console.error('❌ Error en inicialización:', error);
            this.handleError('Error al inicializar el sistema', error);
        }
    }

    /**
     * Obtener parámetros de la URL
     */
    getUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        return {
            fuente: urlParams.get('fuente'),
            categoria: urlParams.get('categoria'),
            filter: urlParams.get('filter') || 'all'
        };
    }

    /**
     * Configurar la página según los parámetros
     */
    setupPage(params) {
        const { fuente, categoria } = params;
        
        // Configurar título y subtítulo
        if (fuente && categoria) {
            this.elements.pageTitle.textContent = `${fuente} - ${categoria}`;
            this.elements.pageSubtitle.textContent = `Noticias de ${fuente} en la categoría ${categoria}`;
        } else if (fuente) {
            this.elements.pageTitle.textContent = fuente;
            this.elements.pageSubtitle.textContent = `Todas las noticias de ${fuente}`;
        } else if (categoria) {
            this.elements.pageTitle.textContent = categoria;
            this.elements.pageSubtitle.textContent = `Todas las noticias de la categoría ${categoria}`;
        } else {
            this.elements.pageTitle.textContent = 'Noticias';
            this.elements.pageSubtitle.textContent = 'Explora las últimas noticias';
        }

        // Configurar filtro activo
        this.state.currentFilter = params.filter;
        this.setActiveFilter(params.filter);
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Filtros de tiempo
        this.elements.filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.currentTarget.getAttribute('data-filter');
                this.handleFilterChange(filter);
            });
        });

        // Botón de actualizar (si existe)
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // Detectar cambios en la URL (para navegación del navegador)
        window.addEventListener('popstate', () => {
            const params = this.getUrlParams();
            this.setupPage(params);
            this.loadNews(params);
        });

        // Detectar visibilidad de la página para pausar/reanudar actualizaciones
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoRefresh();
            } else {
                this.resumeAutoRefresh();
            }
        });
    }

    /**
     * Cargar datos iniciales
     */
    async loadInitialData(params) {
        this.showLoading();
        
        try {
            // Cargar noticias principales
            await this.loadNews(params);
            
            // Cargar datos del sidebar en paralelo
            await Promise.all([
                this.loadTrendingNews(),
                this.loadPopularCategories()
            ]);
            
            // Actualizar estadísticas
            this.updateStatistics();

        } catch (error) {
            console.error('❌ Error cargando datos iniciales:', error);
            this.handleError('Error al cargar los datos', error);
        }
    }

    /**
     * Cargar noticias según los parámetros
     */
    async loadNews(params) {
        if (this.state.isLoading) return;
        
        this.state.isLoading = true;
        this.state.hasError = false;

        try {
            const { fuente, categoria, filter } = params;
            let news = [];

            // Generar clave de cache
            const cacheKey = `${fuente || 'all'}-${categoria || 'all'}-${filter}`;
            
            // Verificar cache
            if (this.cache.news.has(cacheKey) && this.isCacheValid(cacheKey)) {
                console.log('📦 Usando datos del cache');
                news = this.cache.news.get(cacheKey);
            } else {
                console.log('🌐 Obteniendo datos de la API');
                
                if (fuente && categoria) {
                    news = await this.fetchNewsByFuenteAndCategoria(fuente, categoria, filter);
                } else if (fuente) {
                    news = await this.fetchNewsByFuente(fuente, filter);
                } else if (categoria) {
                    news = await this.fetchNewsByCategoria(categoria, filter);
                } else {
                    news = await this.fetchGeneralNews(filter);
                }

                // Guardar en cache
                this.cache.news.set(cacheKey, news);
                this.cache.lastFetch.set(cacheKey, Date.now());
            }

            this.state.currentNews = news;
            this.state.lastUpdate = new Date();
            this.state.retryCount = 0;

            this.renderNews(news);

        } catch (error) {
            console.error('❌ Error cargando noticias:', error);
            this.handleError('Error al cargar las noticias', error);
        } finally {
            this.state.isLoading = false;
        }
    }

    /**
     * Obtener noticias por fuente
     */
    async fetchNewsByFuente(fuente, filter = 'all') {
        const endpoint = `${this.config.apiBaseUrl}/news/fuentes/${encodeURIComponent(fuente)}`;
        const params = this.buildFilterParams(filter);
        
        console.log(`📡 Obteniendo noticias de fuente: ${fuente}`);
        
        const response = await this.makeRequest(`${endpoint}?${params}`);
        return this.processNewsData(response);
    }

    /**
     * Obtener noticias por categoría
     */
    async fetchNewsByCategoria(categoria, filter = 'all') {
        const endpoint = `${this.config.apiBaseUrl}/news/categorias/${encodeURIComponent(categoria)}`;
        const params = this.buildFilterParams(filter);
        
        console.log(`📡 Obteniendo noticias de categoría: ${categoria}`);
        
        const response = await this.makeRequest(`${endpoint}?${params}`);
        return this.processNewsData(response);
    }

    /**
     * Obtener noticias por fuente y categoría
     */
    async fetchNewsByFuenteAndCategoria(fuente, categoria, filter = 'all') {
        const news = await this.fetchNewsByFuente(fuente, filter);
        return news.filter(article => 
            article.categoria && 
            article.categoria.toLowerCase() === categoria.toLowerCase()
        );
    }

    /**
     * Obtener noticias generales
     */
    async fetchGeneralNews(filter = 'all') {
        const endpoint = `${this.config.apiBaseUrl}/news`;
        const params = this.buildFilterParams(filter);
        
        console.log('📡 Obteniendo noticias generales');
        
        const response = await this.makeRequest(`${endpoint}?${params}`);
        return this.processNewsData(response);
    }

    /**
     * Construir parámetros de filtro
     */
    buildFilterParams(filter) {
        const params = new URLSearchParams();
        params.set('limit', this.config.itemsPerPage);
        
        if (filter !== 'all') {
            const now = new Date();
            let startDate;
            
            switch (filter) {
                case 'today':
                    startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                    break;
                case 'week':
                    startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    break;
                case 'month':
                    startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                    break;
                case 'year':
                    startDate = new Date(now.getFullYear(), 0, 1);
                    break;
            }
            
            if (startDate) {
                params.set('fecha_desde', startDate.toISOString().split('T')[0]);
            }
        }
        
        return params.toString();
    }

    /**
     * Procesar datos de noticias
     */
    processNewsData(response) {
        const news = Array.isArray(response) ? response : (response.items || []);
        
        // Aplicar filtros de limpieza
        return news.filter(article => this.isValidNews(article));
    }

    /**
     * Validar si una noticia es válida
     */
    isValidNews(article) {
        const titulo = article.titulo || '';
        const resumen = article.resumen || '';
        
        // Filtros básicos
        if (!titulo || titulo.trim() === '' || titulo === 'null' || titulo === 'undefined') {
            return false;
        }
        
        if (titulo.toLowerCase().includes('login/register')) {
            return false;
        }
        
        if (titulo.toLowerCase().includes('pachamama radio') && resumen.includes('[tdc_zone')) {
            return false;
        }
        
        if (resumen.includes('[tdc_zone type="tdc_content"]')) {
            return false;
        }
        
        return true;
    }

    /**
     * Renderizar noticias
     */
    renderNews(news) {
        if (!news || news.length === 0) {
            this.renderEmptyState();
            return;
        }
        
        console.log(`🎨 Renderizando ${news.length} noticias`);
        
        const newsHTML = news.map(article => this.createNewsCard(article)).join('');
        
        this.elements.newsContainer.innerHTML = `
            <div class="row fade-in">
                ${newsHTML}
            </div>
        `;

        // Animar la aparición
        setTimeout(() => {
            const cards = this.elements.newsContainer.querySelectorAll('.news-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('slide-in');
                }, index * 50);
            });
        }, 100);
    }

    /**
     * Crear card de noticia
     */
    createNewsCard(article) {
        const image = this.getNewsImage(article);
        const date = this.formatDate(article.fecha || article.created_at);
        const summary = this.cleanContent(article.resumen || article.contenido || '');
        const title = this.cleanContent(article.titulo || 'Sin título');
        const category = article.categoria || 'General';
        const author = article.autor || 'Autor desconocido';
        const id = article.id || '0';
        
        return `
            <div class="col-lg-6 mb-4">
                <div class="news-card hover-lift">
                    <img src="${image}" alt="${title}" class="news-image" loading="lazy">
                    <div class="news-content">
                        <span class="news-category">${category}</span>
                        <h3 class="news-title">
                            <a href="detalle_noticias.html?id=${encodeURIComponent(id)}">${title}</a>
                        </h3>
                        <p class="news-summary">${summary}</p>
                        <div class="news-meta">
                            <div class="news-author">
                                <img src="img/user.jpg" alt="Autor" loading="lazy">
                                <span>${author}</span>
                            </div>
                            <div class="news-date">
                                <i class="fas fa-calendar"></i>
                                ${date}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Obtener imagen de noticia
     */
    getNewsImage(article) {
        const imagenes = article.imagenes || article.imagen_principal;
        
        if (!imagenes || imagenes === 'null' || imagenes === 'undefined') {
            return this.config.defaultImage;
        }
        
        let firstImg = null;
        
        if (Array.isArray(imagenes)) {
            firstImg = imagenes[0];
        } else {
            const parts = String(imagenes).split(/[|,;\n]/).map(s => s.trim()).filter(Boolean);
            firstImg = parts[0];
        }
        
        if (!firstImg || firstImg === 'null' || firstImg === 'undefined') {
            return this.config.defaultImage;
        }
        
        // Usar proxy para imágenes externas
        if (firstImg.startsWith('http://') || firstImg.startsWith('https://')) {
            if (firstImg.includes('pachamamaradio.org') || 
                firstImg.includes('punonoticias.com') || 
                firstImg.includes('losandes.com.pe') || 
                firstImg.includes('sinfronteras.pe')) {
                return `${this.config.imageProxy}${encodeURIComponent(firstImg)}`;
            }
            return firstImg;
        }
        
        return firstImg;
    }

    /**
     * Limpiar contenido
     */
    cleanContent(content) {
        if (!content) return '';
        
        let clean = String(content);
        
        // Limpiar contenido problemático
        clean = clean.replace(/\[tdc_zone[^\]]*\]/g, '');
        clean = clean.replace(/\[vc_row[^\]]*\]/g, '');
        clean = clean.replace(/\[vc_column[^\]]*\]/g, '');
        clean = clean.replace(/\[vc_[^\]]*\]/g, '');
        clean = clean.replace(/<[^>]*>/g, '');
        clean = clean.replace(/\s+/g, ' ').trim();
        
        // Verificar si es contenido válido
        if (clean.length < 3 || 
            clean.includes('eyJhbGwiOnsibWFyZ2luLXRvcCI6IjQ4IiwibWFyZ2luLWI') ||
            clean.includes('eyJhbGwiOnsibWFyZ2luLXRvcCI6IjAiLCJtYXJna') ||
            clean.includes('tdc_css=') ||
            clean === 'null' ||
            clean === 'undefined' ||
            clean === 'NaN') {
            return 'Contenido no disponible';
        }
        
        return clean;
    }

    /**
     * Formatear fecha
     */
    formatDate(dateStr) {
        if (!dateStr) return 'Fecha no disponible';
        
        try {
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return 'Fecha no disponible';
            
            return date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch (error) {
            return 'Fecha no disponible';
        }
    }

    /**
     * Manejar cambio de filtro
     */
    async handleFilterChange(filter) {
        if (this.state.isLoading || filter === this.state.currentFilter) return;
        
        console.log(`🔄 Cambiando filtro a: ${filter}`);
        
        this.state.currentFilter = filter;
        this.setActiveFilter(filter);
        
        // Actualizar URL
        const url = new URL(window.location);
        url.searchParams.set('filter', filter);
        window.history.pushState({}, '', url);
        
        // Recargar noticias
        const params = this.getUrlParams();
        await this.loadNews(params);
    }

    /**
     * Establecer filtro activo
     */
    setActiveFilter(filter) {
        this.elements.filterButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-filter') === filter) {
                btn.classList.add('active');
            }
        });
    }

    /**
     * Cargar noticias trending
     */
    async loadTrendingNews() {
        try {
            const response = await this.makeRequest(`${this.config.apiBaseUrl}/api/trending?limit=5`);
            const news = Array.isArray(response) ? response : (response.items || []);
            
            if (news.length === 0) {
                this.elements.trendingNews.innerHTML = '<div class="text-center text-muted">No hay noticias destacadas</div>';
                return;
            }
            
            const html = news.map(article => `
                <div class="trending-item">
                    <img src="${this.getNewsImage(article)}" alt="${article.titulo}" class="trending-image" loading="lazy">
                    <div class="trending-content">
                        <div class="trending-title">
                            <a href="detalle_noticias.html?id=${encodeURIComponent(article.id)}">
                                ${this.cleanContent(article.titulo || 'Sin título')}
                            </a>
                        </div>
                        <div class="trending-meta">
                            <span>${article.categoria || 'General'}</span>
                            <span>•</span>
                            <span>${this.formatDate(article.fecha)}</span>
                        </div>
                    </div>
                </div>
            `).join('');
            
            this.elements.trendingNews.innerHTML = html;
            
        } catch (error) {
            console.error('❌ Error cargando trending news:', error);
            this.elements.trendingNews.innerHTML = '<div class="text-center text-muted">Error cargando noticias destacadas</div>';
        }
    }

    /**
     * Cargar categorías populares
     */
    async loadPopularCategories() {
        try {
            const response = await this.makeRequest(`${this.config.apiBaseUrl}/news/categorias/listar`);
            const categories = Array.isArray(response) ? response : [];
            
            if (categories.length === 0) {
                this.elements.popularCategories.innerHTML = '<div class="text-center text-muted">No hay categorías disponibles</div>';
                return;
            }
            
            const html = categories.slice(0, 5).map(category => `
                <div class="trending-item">
                    <div class="trending-content">
                        <div class="trending-title">
                            <a href="categorias.html?categoria=${encodeURIComponent(category)}">
                                <i class="fas fa-tag"></i>
                                ${category}
                            </a>
                        </div>
                    </div>
                </div>
            `).join('');
            
            this.elements.popularCategories.innerHTML = html;
            
        } catch (error) {
            console.error('❌ Error cargando categorías:', error);
            this.elements.popularCategories.innerHTML = '<div class="text-center text-muted">Error cargando categorías</div>';
        }
    }

    /**
     * Actualizar estadísticas
     */
    updateStatistics() {
        const totalNews = this.state.currentNews.length;
        const sources = [...new Set(this.state.currentNews.map(n => n.fuente).filter(Boolean))].length;
        const categories = [...new Set(this.state.currentNews.map(n => n.categoria).filter(Boolean))].length;
        
        this.elements.totalNews.textContent = totalNews;
        this.elements.totalSources.textContent = sources;
        this.elements.totalCategories.textContent = categories;
    }

    /**
     * Mostrar estado de carga
     */
    showLoading() {
        this.elements.newsContainer.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p class="loading-text">Cargando noticias...</p>
            </div>
        `;
    }

    /**
     * Mostrar estado vacío
     */
    renderEmptyState() {
        this.elements.newsContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-newspaper"></i>
                </div>
                <h3 class="empty-title">No hay noticias disponibles</h3>
                <p class="empty-description">No se encontraron noticias con los filtros aplicados.</p>
                <button class="btn btn-primary" onclick="location.reload()">
                    <i class="fas fa-refresh"></i>
                    Actualizar
                </button>
            </div>
        `;
    }

    /**
     * Manejar errores
     */
    handleError(message, error) {
        console.error('❌ Error:', error);
        
        this.elements.newsContainer.innerHTML = `
            <div class="error-state">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3 class="error-title">Error</h3>
                <p class="error-description">${message}</p>
                <button class="btn btn-primary" onclick="location.reload()">
                    <i class="fas fa-refresh"></i>
                    Reintentar
                </button>
            </div>
        `;
        
        this.state.hasError = true;
    }

    /**
     * Hacer petición HTTP con reintentos
     */
    async makeRequest(url, retries = 0) {
        try {
            const response = await fetch(url, {
                headers: { 'Accept': 'application/json' }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            if (retries < this.config.maxRetries) {
                console.warn(`⚠️ Reintentando petición (${retries + 1}/${this.config.maxRetries}):`, error.message);
                await this.delay(this.config.retryDelay * (retries + 1));
                return this.makeRequest(url, retries + 1);
            }
            throw error;
        }
    }

    /**
     * Verificar si el cache es válido
     */
    isCacheValid(cacheKey) {
        const lastFetch = this.cache.lastFetch.get(cacheKey);
        if (!lastFetch) return false;
        
        const now = Date.now();
        const cacheAge = now - lastFetch;
        const maxAge = 5 * 60 * 1000; // 5 minutos
        
        return cacheAge < maxAge;
    }

    /**
     * Configurar actualizaciones automáticas
     */
    setupAutoRefresh() {
        // Actualizar cada 5 minutos
        this.autoRefreshInterval = setInterval(() => {
            if (!document.hidden && !this.state.isLoading) {
                this.refreshData();
            }
        }, 5 * 60 * 1000);
    }

    /**
     * Pausar actualizaciones automáticas
     */
    pauseAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    }

    /**
     * Reanudar actualizaciones automáticas
     */
    resumeAutoRefresh() {
        this.setupAutoRefresh();
    }

    /**
     * Refrescar datos
     */
    async refreshData() {
        console.log('🔄 Refrescando datos...');
        
        // Limpiar cache
        this.cache.news.clear();
        this.cache.lastFetch.clear();
        
        // Recargar datos
        const params = this.getUrlParams();
        await this.loadNews(params);
    }

    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Destruir el sistema
     */
    destroy() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        this.cache.news.clear();
        this.cache.metadata.clear();
        this.cache.lastFetch.clear();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.newsSystem = new NewsCategorySystem();
});

// Exportar para uso global
window.NewsCategorySystem = NewsCategorySystem;
