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
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');
    const searchStats = document.getElementById('searchStats');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const noResults = document.getElementById('noResults');
    const clearFiltersBtn = document.getElementById('clearFilters');

    // Inicialización
    document.addEventListener('DOMContentLoaded', function() {
        initializeForm();
        loadMetadata();
        setupEventListeners();
    });

    function initializeForm() {
        // Configurar valores por defecto
        const today = new Date();
        const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
        
        document.getElementById('fechaDesde').value = lastMonth.toISOString().split('T')[0];
        document.getElementById('fechaHasta').value = today.toISOString().split('T')[0];
    }

    function setupEventListeners() {
        // Formulario de búsqueda
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });

        // Botón limpiar filtros
        clearFiltersBtn.addEventListener('click', function() {
            clearAllFilters();
        });

        // Búsqueda en tiempo real (opcional)
        const searchInputs = ['searchText', 'searchKeywords'];
        searchInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                let timeout;
                input.addEventListener('input', function() {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        if (this.value.length >= 3 || this.value.length === 0) {
                            performSearch();
                        }
                    }, 500);
                });
            }
        });
    }

    async function loadMetadata() {
        try {
            // Cargar fuentes
            const fuentes = await fetchMetadata('fuentes');
            populateSelect('fuente', fuentes);

            // Cargar categorías
            const categorias = await fetchMetadata('categorias');
            populateSelect('categoria', categorias);

            // Cargar dominios
            const dominios = await fetchMetadata('dominios');
            populateSelect('dominio', dominios);

            // Cargar años
            const anos = await fetchMetadata('anos');
            populateSelect('anio', anos, true);

            // Cargar tipos de contenido
            const tipos = await fetchMetadata('tipos-contenido');
            populateSelect('tipoContenido', tipos);

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
            const response = await fetch(`${METADATA_ENDPOINT}/${type}/listar`);
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
        
        // Texto de búsqueda
        const searchText = document.getElementById('searchText').value.trim();
        if (searchText) filters.q = searchText;

        // Keywords
        const keywords = document.getElementById('searchKeywords').value.trim();
        if (keywords) filters.keywords = keywords;

        // Filtros de selección
        const selectFilters = ['fuente', 'categoria', 'dominio', 'anio', 'mes', 'diaSemana', 'tipoContenido', 'tieneImagenes'];
        selectFilters.forEach(id => {
            const value = document.getElementById(id).value;
            if (value) {
                const filterKey = id === 'diaSemana' ? 'dia_semana' : 
                                 id === 'tipoContenido' ? 'tipo_contenido' : 
                                 id === 'tieneImagenes' ? 'tiene_imagenes' : id;
                filters[filterKey] = value;
            }
        });

        // Filtros numéricos
        const numericFilters = ['longitudTituloMin', 'longitudTituloMax'];
        numericFilters.forEach(id => {
            const value = document.getElementById(id).value;
            if (value) {
                const filterKey = id === 'longitudTituloMin' ? 'longitud_titulo_min' : 'longitud_titulo_max';
                filters[filterKey] = parseInt(value);
            }
        });

        // Filtros de fecha
        const fechaDesde = document.getElementById('fechaDesde').value;
        if (fechaDesde) filters.fecha_desde = fechaDesde;

        const fechaHasta = document.getElementById('fechaHasta').value;
        if (fechaHasta) filters.fecha_hasta = fechaHasta;

        // Límite de resultados
        const limit = document.getElementById('limit').value;
        if (limit) filters.limit = parseInt(limit);

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

            const response = await fetch(url, {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            });

            if (!response.ok) {
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
        const { total, items } = data;
        totalResults = total;

        // Actualizar estadísticas
        updateStats(total, items.length);

        // Limpiar resultados anteriores
        searchResults.innerHTML = '';

        if (items.length === 0) {
            showNoResults();
            return;
        }

        // Mostrar resultados
        items.forEach(news => {
            const newsCard = createNewsCard(news);
            searchResults.appendChild(newsCard);
        });

        // Mostrar filtros activos
        showActiveFilters();
    }

    function createNewsCard(news) {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-4';
        
        const imageUrl = parseFirstImage(news.imagenes || news.imagen_principal) || 'img/news-700x435-1.jpg';
        const date = formatDate(news.fecha || news.created_at);
        const resumen = cleanContent(news.resumen || news.contenido || '');
        
        card.innerHTML = `
            <div class="search-card">
                <img src="${imageUrl}" class="card-img" alt="${news.titulo || 'Noticia'}">
                <div class="card-body">
                    <div class="mb-2">
                        <span class="badge badge-primary mr-2">${news.categoria || 'General'}</span>
                        <span class="badge badge-secondary mr-2">${news.fuente || 'Sin fuente'}</span>
                        <small class="text-muted">${date}</small>
                    </div>
                    <h5 class="card-title">
                        <a href="detalle_noticias.html?id=${news.id}" class="text-decoration-none text-dark">
                            ${news.titulo || 'Sin título'}
                        </a>
                    </h5>
                    <p class="card-text">${resumen.length > 150 ? resumen.substring(0, 150) + '...' : resumen}</p>
                    <div class="card-meta">
                        <div>
                            <small class="text-muted">
                                <i class="fa fa-calendar mr-1"></i>${date}
                            </small>
                        </div>
                        <div>
                            <a href="detalle_noticias.html?id=${news.id}" class="btn btn-sm btn-outline-primary">
                                Leer más
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;

        return card;
    }

    function updateStats(total, displayed) {
        searchStats.innerHTML = `
            <div class="search-stats">
                <div class="stat-item">
                    <span class="stat-number">${total}</span> resultados encontrados
                </div>
                <div class="stat-item">
                    <span class="stat-number">${displayed}</span> mostrados
                </div>
                <div class="stat-item">
                    <span class="stat-number">${Object.keys(currentFilters).length}</span> filtros activos
                </div>
            </div>
        `;
    }

    function showActiveFilters() {
        const activeFilters = Object.entries(currentFilters)
            .filter(([key, value]) => value !== null && value !== undefined && value !== '')
            .map(([key, value]) => ({ key, value }));

        if (activeFilters.length === 0) return;

        const filtersContainer = document.createElement('div');
        filtersContainer.className = 'active-filters';
        filtersContainer.innerHTML = `
            <h6>Filtros activos:</h6>
            <div class="filter-tags">
                ${activeFilters.map(filter => `
                    <span class="filter-tag">
                        ${getFilterDisplayName(filter.key)}: ${filter.value}
                        <span class="remove" onclick="removeFilter('${filter.key}')">&times;</span>
                    </span>
                `).join('')}
            </div>
        `;

        searchResults.insertBefore(filtersContainer, searchResults.firstChild);
    }

    function getFilterDisplayName(key) {
        const names = {
            'q': 'Texto',
            'keywords': 'Palabras clave',
            'fuente': 'Fuente',
            'categoria': 'Categoría',
            'dominio': 'Dominio',
            'anio': 'Año',
            'mes': 'Mes',
            'dia_semana': 'Día',
            'tipo_contenido': 'Tipo',
            'tiene_imagenes': 'Imágenes',
            'longitud_titulo_min': 'Título min',
            'longitud_titulo_max': 'Título max',
            'fecha_desde': 'Desde',
            'fecha_hasta': 'Hasta'
        };
        return names[key] || key;
    }

    function removeFilter(key) {
        // Remover filtro del objeto
        delete currentFilters[key];
        
        // Limpiar campo del formulario
        const fieldMap = {
            'q': 'searchText',
            'keywords': 'searchKeywords',
            'fuente': 'fuente',
            'categoria': 'categoria',
            'dominio': 'dominio',
            'anio': 'anio',
            'mes': 'mes',
            'dia_semana': 'diaSemana',
            'tipo_contenido': 'tipoContenido',
            'tiene_imagenes': 'tieneImagenes',
            'longitud_titulo_min': 'longitudTituloMin',
            'longitud_titulo_max': 'longitudTituloMax',
            'fecha_desde': 'fechaDesde',
            'fecha_hasta': 'fechaHasta'
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
        // Limpiar todos los campos del formulario
        searchForm.reset();
        
        // Restablecer valores por defecto
        initializeForm();
        
        // Limpiar filtros actuales
        currentFilters = {};
        
        // Limpiar resultados
        searchResults.innerHTML = '';
        searchStats.innerHTML = '';
        hideNoResults();
    }

    function showLoading() {
        loadingSpinner.style.display = 'block';
        searchResults.style.display = 'none';
        noResults.style.display = 'none';
    }

    function hideLoading() {
        loadingSpinner.style.display = 'none';
        searchResults.style.display = 'block';
    }

    function showNoResults() {
        noResults.style.display = 'block';
        searchResults.style.display = 'none';
    }

    function hideNoResults() {
        noResults.style.display = 'none';
    }

    function showError(message) {
        searchResults.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fa fa-exclamation-triangle mr-2"></i>
                ${message}
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
