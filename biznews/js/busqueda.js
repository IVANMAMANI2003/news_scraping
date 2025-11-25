(function() {
    "use strict";

    const API_BASE_URL = "http://127.0.0.1:8000";
    const ADVANCED_ENDPOINT = API_BASE_URL + "/api";
    const METADATA_ENDPOINT = API_BASE_URL + "/news";

    let currentFilters = {};
    let currentPage = 1;
    let totalResults = 0;
    let isLoading = false;

    // Elementos del DOM
    let searchForm = document.getElementById('search-form');
    let searchResults = document.getElementById('search-results');
    let resultsCount = document.getElementById('results-count');
    let totalResultsEl = document.getElementById('total-results');
    let activeFiltersEl = document.getElementById('active-filters');
    let filterTagsEl = document.getElementById('filter-tags');
    let clearFiltersBtn = document.getElementById('clear-filters');

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

    // Verificar autenticación
    async function checkAuthentication() {
        const token = getAuthToken();
        if (!token) {
            const container = document.querySelector('.main-content');
            if (container) {
                container.innerHTML = `
                    <div class="content-card">
                        <div class="alert alert-warning text-center" style="max-width: 600px; margin: 4rem auto; padding: 3rem;">
                            <i class="fas fa-lock fa-3x mb-3 text-warning"></i>
                            <h4>Acceso Restringido</h4>
                            <p>La búsqueda avanzada está disponible solo para usuarios autenticados.</p>
                            <p class="mb-3">Por favor, <a href="../page/login.html">inicia sesión</a> para acceder a esta funcionalidad.</p>
                            <a href="../page/login.html" class="btn btn-primary">
                                <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
                            </a>
                        </div>
                    </div>
                `;
            }
            return false;
        }
        
        // Verificar que el token sea válido
        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                const container = document.querySelector('.main-content');
                if (container) {
                    container.innerHTML = `
                        <div class="content-card">
                            <div class="alert alert-warning text-center" style="max-width: 600px; margin: 4rem auto; padding: 3rem;">
                                <i class="fas fa-lock fa-3x mb-3 text-warning"></i>
                                <h4>Acceso Restringido</h4>
                                <p>Tu sesión ha expirado. Por favor, <a href="../page/login.html">inicia sesión</a> nuevamente.</p>
                                <a href="../page/login.html" class="btn btn-primary">
                                    <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
                                </a>
                            </div>
                        </div>
                    `;
                }
                return false;
            }
            
            return true;
        } catch (error) {
            console.error('Error verificando autenticación:', error);
            return false;
        }
    }

    // Inicialización
    document.addEventListener('DOMContentLoaded', async function() {
        // Verificar autenticación primero
        const isAuthenticated = await checkAuthentication();
        if (!isAuthenticated) {
            return; // No continuar si no está autenticado
        }
        
        initializeForm();
        loadMetadata();
        setupEventListeners();
    });

    function initializeForm() {
        // No establecer valores por defecto, dejar que el usuario elija
    }

    function setupEventListeners() {
        if (!searchForm) return;
        
        // Formulario de búsqueda
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });

        // Botón limpiar filtros
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', function() {
                clearAllFilters();
            });
        }
    }

    async function loadMetadata() {
        try {
            // Cargar fuentes
            const fuentes = await fetchMetadata('fuentes');
            populateSelect('fuente', fuentes);

            // Cargar categorías
            const categorias = await fetchMetadata('categorias');
            populateSelect('categoria', categorias);

            // Cargar años
            const anos = await fetchMetadata('anos');
            populateSelect('anio', anos, true);
            
            // Cargar meses
            const meses = await fetchMetadata('meses');
            populateSelect('mes', meses, true);
            
            // Cargar días de la semana
            const diasSemana = await fetchMetadata('dias-semana');
            populateSelect('dia_semana', diasSemana);

        } catch (error) {
            console.error('Error cargando metadatos:', error);
        }
    }

    function populateSelect(selectId, data, isNumeric = false) {
        const select = document.getElementById(selectId);
        if (!select) return;

        // Limpiar opciones existentes (excepto la primera)
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        // Agregar nuevas opciones
        data.forEach(item => {
            const option = document.createElement('option');
            option.value = isNumeric ? item : item;
            option.textContent = isNumeric ? item : item;
            select.appendChild(option);
        });
    }

    async function fetchMetadata(type) {
        try {
            // Incluir token de autenticación si está disponible
            const token = getAuthToken();
            const headers = {};
            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }
            
            const response = await fetch(`${METADATA_ENDPOINT}/${type}/listar`, { headers });
            if (!response.ok) {
                throw new Error(`Error fetching ${type}: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${type}:`, error);
            return [];
        }
    }

    async function performSearch() {
        if (isLoading) return;

        isLoading = true;
        showLoading();

        try {
            // Recopilar filtros del formulario
            currentFilters = collectFilters();
            
            // Realizar búsqueda
            const results = await searchNews(currentFilters);
            
            // Mostrar resultados
            displayResults(results);
            
        } catch (error) {
            console.error('Error en la búsqueda:', error);
            showError('Error al realizar la búsqueda. Inténtalo de nuevo.');
        } finally {
            isLoading = false;
            hideLoading();
        }
    }

    function collectFilters() {
        const filters = {};
        
        // Texto de búsqueda (query)
        const query = document.getElementById('query')?.value.trim();
        if (query) filters.q = query;

        // Filtros de selección
        const selectFilters = ['fuente', 'categoria', 'anio', 'mes', 'dia_semana'];
        selectFilters.forEach(id => {
            const element = document.getElementById(id);
            if (element && element.value) {
                const filterKey = id === 'dia_semana' ? 'dia_semana' : id;
                filters[filterKey] = element.value;
            }
        });

        // Filtros de fecha
        const fechaDesde = document.getElementById('fecha_desde')?.value;
        if (fechaDesde) filters.fecha_desde = fechaDesde;

        const fechaHasta = document.getElementById('fecha_hasta')?.value;
        if (fechaHasta) filters.fecha_hasta = fechaHasta;

        // Límite de resultados (por defecto 50)
        filters.limit = 50;
        filters.order = 'desc'; // Más recientes primero

        return filters;
    }

    async function searchNews(filters) {
        try {
            const params = new URLSearchParams();
            Object.keys(filters).forEach(key => {
                if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
                    params.append(key, filters[key]);
                }
            });

            const url = `${ADVANCED_ENDPOINT}/search?${params.toString()}`;
            console.log('Buscando en:', url);

            // Incluir token de autenticación
            const token = getAuthToken();
            const headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            };
            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(url, { headers });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Se requiere autenticación para acceder a la búsqueda avanzada. Por favor, inicia sesión.');
                } else if (response.status === 403) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'No tienes permisos para acceder a esta funcionalidad');
                }
                throw new Error(`Error en la búsqueda: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error en searchNews:', error);
            throw error;
        }
    }

    function displayResults(data) {
        if (!searchResults) return;
        
        const { total, items } = data;
        totalResults = total || 0;

        // Actualizar contadores
        if (resultsCount) {
            resultsCount.textContent = `${total || 0} resultados encontrados`;
        }
        if (totalResultsEl) {
            totalResultsEl.textContent = total || 0;
        }

        // Limpiar resultados anteriores
        searchResults.innerHTML = '';

        if (!items || items.length === 0) {
            showNoResults();
            return;
        }

        // Crear contenedor de resultados
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'row';
        
        // Mostrar resultados
        items.forEach(news => {
            const newsCard = createNewsCard(news);
            resultsContainer.appendChild(newsCard);
        });
        
        searchResults.appendChild(resultsContainer);
        searchResults.classList.add('fade-in');

        // Mostrar filtros activos
        showActiveFilters();
    }

    function createNewsCard(news) {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-4';
        
        const imageUrl = parseFirstImage(news.imagenes || news.imagen_principal || '') || '../img/news-700x435-1.jpg';
        const date = formatDate(news.fecha || news.created_at);
        const resumen = cleanContent(news.resumen || news.contenido || '');
        const titulo = news.titulo || 'Sin título';
        const categoria = news.categoria || 'General';
        const fuente = news.fuente || 'Sin fuente';
        
        card.innerHTML = `
            <div class="news-card">
                <img src="${imageUrl}" class="news-image" alt="${titulo}" 
                     onerror="this.src='../img/news-700x435-1.jpg'">
                <div class="news-content">
                    <div class="news-category">${categoria}</div>
                    <h3 class="news-title">
                        <a href="../page/detalle_noticias.html?id=${news.id}">${titulo}</a>
                    </h3>
                    <p class="news-summary">${resumen.length > 150 ? resumen.substring(0, 150) + '...' : resumen}</p>
                    <div class="news-meta">
                        <div class="news-author">
                            <i class="fas fa-rss"></i>
                            <span>${fuente}</span>
                        </div>
                        <div class="news-date">
                            <i class="fas fa-calendar"></i>
                            <span>${date}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        return card;
    }

    function showActiveFilters() {
        if (!activeFiltersEl || !filterTagsEl) return;
        
        const activeFilters = Object.entries(currentFilters)
            .filter(([key, value]) => value !== null && value !== undefined && value !== '' && key !== 'limit' && key !== 'order')
            .map(([key, value]) => ({ key, value }));

        if (activeFilters.length === 0) {
            activeFiltersEl.style.display = 'none';
            return;
        }

        activeFiltersEl.style.display = 'block';
        filterTagsEl.innerHTML = activeFilters.map(filter => `
            <span class="filter-tag">
                ${getFilterDisplayName(filter.key)}: ${filter.value}
                <span class="remove" onclick="removeFilter('${filter.key}')">&times;</span>
            </span>
        `).join('');
    }

    function getFilterDisplayName(key) {
        const names = {
            'q': 'Palabras clave',
            'fuente': 'Fuente',
            'categoria': 'Categoría',
            'anio': 'Año',
            'mes': 'Mes',
            'dia_semana': 'Día de la semana',
            'fecha_desde': 'Fecha desde',
            'fecha_hasta': 'Fecha hasta'
        };
        return names[key] || key;
    }

    function removeFilter(key) {
        // Remover filtro del objeto
        delete currentFilters[key];
        
        // Limpiar campo del formulario
        const fieldMap = {
            'q': 'query',
            'fuente': 'fuente',
            'categoria': 'categoria',
            'anio': 'anio',
            'mes': 'mes',
            'dia_semana': 'dia_semana',
            'fecha_desde': 'fecha_desde',
            'fecha_hasta': 'fecha_hasta'
        };

        const fieldId = fieldMap[key];
        if (fieldId) {
            const field = document.getElementById(fieldId);
            if (field) {
                field.value = '';
            }
        }

        // Realizar nueva búsqueda
        performSearch();
    }

    function clearAllFilters() {
        if (!searchForm) return;
        
        // Limpiar todos los campos del formulario
        searchForm.reset();
        
        // Limpiar filtros actuales
        currentFilters = {};
        
        // Limpiar resultados
        if (searchResults) {
            searchResults.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-search"></i>
                    </div>
                    <h3 class="empty-title">Realiza una búsqueda</h3>
                    <p class="empty-description">Usa los filtros de arriba para encontrar noticias específicas</p>
                </div>
            `;
        }
        
        // Ocultar filtros activos
        if (activeFiltersEl) {
            activeFiltersEl.style.display = 'none';
        }
        
        // Actualizar contadores
        if (resultsCount) {
            resultsCount.textContent = '0 resultados encontrados';
        }
        if (totalResultsEl) {
            totalResultsEl.textContent = '-';
        }
    }

    function showLoading() {
        if (!searchResults) return;
        searchResults.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <div class="loading-text">Buscando noticias...</div>
            </div>
        `;
    }

    function hideLoading() {
        // Se maneja en displayResults
    }

    function showNoResults() {
        if (!searchResults) return;
        searchResults.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-search"></i>
                </div>
                <h3 class="empty-title">No se encontraron resultados</h3>
                <p class="empty-description">Intenta ajustar los filtros de búsqueda o usar términos diferentes</p>
            </div>
        `;
    }

    function showError(message) {
        if (!searchResults) return;
        searchResults.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-exclamation-triangle text-danger"></i>
                </div>
                <h3 class="empty-title">Error</h3>
                <p class="empty-description">${message}</p>
            </div>
        `;
    }

    // Funciones auxiliares (reutilizadas de news-api.js)
    function parseFirstImage(imagenes) {
        if (!imagenes || imagenes === 'null' || imagenes === 'undefined' || imagenes === 'NaN' || 
            imagenes === '' || imagenes === 'null' || imagenes === 'undefined') {
            return 'img/news-700x435-1.jpg';
        }
        
        let firstImg = null;
        
        if (Array.isArray(imagenes)) {
            firstImg = imagenes[0];
        } else {
            const cleanImagenes = String(imagenes).trim();
            if (cleanImagenes === 'null' || cleanImagenes === 'undefined' || cleanImagenes === 'NaN' || 
                cleanImagenes === '' || cleanImagenes === 'null' || cleanImagenes === 'undefined') {
                return 'img/news-700x435-1.jpg';
            }
            
            const parts = cleanImagenes.split(/[|,;\n]/).map(s => s.trim()).filter(Boolean);
            firstImg = parts[0];
        }
        
        if (!firstImg || firstImg === 'null' || firstImg === 'undefined' || firstImg === 'NaN' || 
            firstImg === '' || firstImg === 'null' || firstImg === 'undefined') {
            return 'img/news-700x435-1.jpg';
        }
        
        if (firstImg.startsWith('http://') || firstImg.startsWith('https://')) {
            if (firstImg.includes('pachamamaradio.org') || firstImg.includes('punonoticias.com') || 
                firstImg.includes('losandes.com.pe') || firstImg.includes('sinfronteras.pe')) {
                return `https://images.weserv.nl/?url=${encodeURIComponent(firstImg)}`;
            }
            return firstImg;
        }
        
        if (firstImg.startsWith('data:image/')) {
            return firstImg;
        }
        
        if (firstImg.startsWith('/') || firstImg.startsWith('./') || firstImg.includes('.')) {
            return firstImg;
        }
        
        return 'img/news-700x435-1.jpg';
    }

    function formatDate(dateStr) {
        if (!dateStr) return "";
        try {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) return String(dateStr);
            return d.toLocaleDateString('es-ES');
        } catch (e) {
            return String(dateStr);
        }
    }

    function cleanContent(content) {
        if (!content) return '';
        
        let clean = String(content);
        
        clean = clean.replace(/\[tdc_zone[^\]]*\]/g, '');
        clean = clean.replace(/\[vc_row[^\]]*\]/g, '');
        clean = clean.replace(/\[vc_column[^\]]*\]/g, '');
        clean = clean.replace(/\[vc_[^\]]*\]/g, '');
        clean = clean.replace(/\[[^\]]*\]/g, '');
        clean = clean.replace(/<[^>]*>/g, '');
        clean = clean.replace(/eyJhbGwiOnsibWFyZ2luLXRvcCI6IjQ4IiwibWFyZ2luLWI[^"]*"/g, '');
        clean = clean.replace(/eyJhbGwiOnsibWFyZ2luLXRvcCI6IjAiLCJtYXJna[^"]*"/g, '');
        clean = clean.replace(/\s+/g, ' ').trim();
        
        if (clean.length < 10 || 
            clean.includes('eyJhbGwiOnsibWFyZ2luLXRvcCI6IjQ4IiwibWFyZ2luLWI') ||
            clean.includes('eyJhbGwiOnsibWFyZ2luLXRvcCI6IjAiLCJtYXJna') ||
            clean.match(/^[A-Za-z0-9+/=]+$/) ||
            clean.includes('tdc_css=')) {
            return 'Contenido no disponible';
        }
        
        return clean;
    }

    // Hacer funciones globales para uso en HTML
    window.removeFilter = removeFilter;

})();
