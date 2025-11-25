/**
 * BizNews Admin Dashboard JavaScript
 * Versión 1.0.0
 * 
 * @author BizNews Team
 * @description JavaScript para el dashboard de administración
 */

class AdminDashboard {
    constructor() {
        this.charts = new Map();
        this.apiBaseUrl = 'http://127.0.0.1:8000';
        this.isInitialized = false;
        this.loadingOverlay = document.getElementById('loadingOverlay');
        // Variables de paginación
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalPages = 1;
        this.chartColors = {
            primary: '#007bff',
            secondary: '#6c757d',
            success: '#28a745',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8',
            light: '#f8f9fa',
            dark: '#343a40'
        };
        this.gradientColors = [
            'rgba(0, 123, 255, 0.8)',
            'rgba(40, 167, 69, 0.8)',
            'rgba(255, 193, 7, 0.8)',
            'rgba(220, 53, 69, 0.8)',
            'rgba(23, 162, 184, 0.8)',
            'rgba(111, 66, 193, 0.8)',
            'rgba(233, 84, 140, 0.8)',
            'rgba(253, 126, 20, 0.8)'
        ];
    }

    async init() {
        if (this.isInitialized) return;
        
        console.log('Inicializando AdminDashboard...');
        
        this.showLoading();

        try {
            // Cargar métricas primero
            console.log('📊 Paso 1: Cargando métricas...');
            await this.loadMetricsData();
            console.log('✅ Paso 1 completado');
            
            // Luego cargar estadísticas
            console.log('📊 Paso 2: Cargando estadísticas...');
            await this.loadStatsData();
            console.log('✅ Paso 2 completado');
            
            // Cargar tabla de noticias
            console.log('📊 Paso 3: Cargando tabla de noticias...');
            await this.loadNewsTable();
            console.log('✅ Paso 3 completado');
            
            // Configurar filtros
            console.log('📊 Paso 4: Configurando filtros...');
            await this.setupFilters();
            console.log('✅ Paso 4 completado');
            
            // Configurar eventos
            console.log('📊 Paso 5: Configurando eventos...');
            this.setupEventListeners();
            console.log('✅ Paso 5 completado');
            
            this.isInitialized = true;
            console.log('AdminDashboard inicializado correctamente');
        } catch (error) {
            console.error('❌ Error inicializando AdminDashboard:', error);
            console.error('Stack trace:', error.stack);
            this.showError('Error al cargar el dashboard');
        } finally {
            this.hideLoading();
        }
    }

    async loadStatsData() {
        try {
            console.log('Cargando datos de estadísticas...');
            if (!window.authManager) {
                throw new Error('AuthManager no está disponible');
            }
            const response = await window.authManager.authenticatedFetch(`${this.apiBaseUrl}/api/stats`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const apiData = await response.json();
            console.log('Datos de estadísticas cargados desde API:', apiData);
            
            // Transformar datos de la API al formato esperado
            this.statsData = this.transformStatsData(apiData);
            
            // Actualizar estadísticas en el hero
            this.updateHeroStats();
            
            // Renderizar resumen y gráficos
            this.renderStatsSummary();
            this.renderCharts();
        } catch (error) {
            console.error('Error cargando estadísticas:', error);
            this.showError('Error al cargar los datos de estadísticas desde la API');
        }
    }

    transformStatsData(apiData) {
        // Nombres de meses
        const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        
        // Nombres de días
        const ordenDias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

        // Transformar noticias por fuente
        const news_by_source = Object.entries(apiData.noticias_por_fuente || {})
            .map(([source, count]) => ({ source, count }))
            .sort((a, b) => b.count - a.count);

        // Transformar noticias por categoría
        const news_by_category = Object.entries(apiData.noticias_por_categoria || {})
            .map(([category, count]) => ({ category, count }))
            .sort((a, b) => b.count - a.count);

        // Transformar noticias por mes
        const news_by_month = [];
        for (let i = 1; i <= 12; i++) {
            const count = apiData.noticias_por_mes?.[String(i)] || 0;
            news_by_month.push({
                month: meses[i - 1],
                count: count
            });
        }

        // Transformar noticias por día de la semana
        const news_by_day = ordenDias.map(day => {
            const count = apiData.noticias_por_dia_semana?.[day] || 
                         apiData.noticias_por_dia_semana?.[day.replace('é', 'e')] || 0;
            return { day, count };
        });

        return {
            total_news: apiData.total_noticias || 0,
            total_sources: news_by_source.length,
            total_categories: news_by_category.length,
            news_by_source: news_by_source,
            news_by_category: news_by_category,
            news_by_month: news_by_month,
            news_by_day: news_by_day
        };
    }

    updateHeroStats() {
        const data = this.statsData || {};
        const totalNewsEl = document.getElementById('total-news-stats');
        const totalSourcesEl = document.getElementById('total-sources-stats');
        const totalCategoriesEl = document.getElementById('total-categories-stats');
        
        if (totalNewsEl) totalNewsEl.textContent = (data.total_news || 0).toLocaleString();
        if (totalSourcesEl) totalSourcesEl.textContent = data.total_sources || 0;
        if (totalCategoriesEl) totalCategoriesEl.textContent = data.total_categories || 0;
    }

    async loadMetricsData() {
        try {
            console.log('Cargando datos de métricas...');
            if (!window.authManager) {
                throw new Error('AuthManager no está disponible');
            }
            const response = await window.authManager.authenticatedFetch(`${this.apiBaseUrl}/api/metrics`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const apiData = await response.json();
            console.log('Datos de métricas cargados desde API:', apiData);
            
            // Calcular métricas adicionales
            const statsResponse = await window.authManager.authenticatedFetch(`${this.apiBaseUrl}/api/stats`);
            let statsData = null;
            if (statsResponse.ok) {
                statsData = await statsResponse.json();
            }
            
            // Calcular promedio de noticias por día
            let average_news_per_day = 0;
            if (statsData && statsData.rango_fechas) {
                const fechaMin = new Date(statsData.rango_fechas.fecha_min);
                const fechaMax = new Date(statsData.rango_fechas.fecha_max);
                if (fechaMin && fechaMax && !isNaN(fechaMin.getTime()) && !isNaN(fechaMax.getTime())) {
                    const diffTime = Math.abs(fechaMax - fechaMin);
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    if (diffDays > 0) {
                        average_news_per_day = (apiData.total / diffDays).toFixed(1);
                    }
                }
            }
            
            // Fuente más activa
            let most_active_source = 'N/A';
            if (statsData && statsData.noticias_por_fuente) {
                const sources = Object.entries(statsData.noticias_por_fuente)
                    .sort((a, b) => b[1] - a[1]);
                if (sources.length > 0) {
                    most_active_source = sources[0][0];
                }
            }
            
            // Categoría más popular
            let most_popular_category = 'N/A';
            if (statsData && statsData.noticias_por_categoria) {
                const categories = Object.entries(statsData.noticias_por_categoria)
                    .sort((a, b) => b[1] - a[1]);
                if (categories.length > 0) {
                    most_popular_category = categories[0][0];
                }
            }
            
            // Calcular tasa de crecimiento
            let growth_rate = 0;
            if (statsData && statsData.noticias_por_mes) {
                const meses = Object.entries(statsData.noticias_por_mes)
                    .map(([mes, count]) => ({ mes: parseInt(mes), count }))
                    .sort((a, b) => a.mes - b.mes);
                if (meses.length >= 2) {
                    const ultimo = meses[meses.length - 1].count;
                    const penultimo = meses[meses.length - 2].count;
                    if (penultimo > 0) {
                        growth_rate = ((ultimo - penultimo) / penultimo).toFixed(2);
                    }
                }
            }
            
            this.metricsData = {
                average_news_per_day: parseFloat(average_news_per_day) || 0,
                peak_hour: '14:00',
                most_active_source: most_active_source,
                most_popular_category: most_popular_category,
                growth_rate: parseFloat(growth_rate) || 0,
                total: apiData.total,
                con_imagenes: apiData.con_imagenes,
                sin_imagenes: apiData.sin_imagenes,
                promedio_titulo: apiData.promedio_titulo,
                promedio_resumen: apiData.promedio_resumen,
                fuentes_activas: apiData.fuentes_activas,
                categorias_activas: apiData.categorias_activas,
                dominios_unicos: apiData.dominios_unicos
            };
        } catch (error) {
            console.error('Error cargando métricas:', error);
            this.showError('Error al cargar los datos de métricas desde la API');
        }
    }

    renderStatsSummary() {
        const container = document.getElementById('statsSummary');
        if (!container) return;

        const data = this.statsData || {};
        const metrics = this.metricsData || {};

        container.innerHTML = `
            <div class="stat-card primary">
                <div class="stat-icon">
                    <i class="fas fa-newspaper"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-number">${(data.total_news || 0).toLocaleString()}</div>
                    <div class="stat-label">Total Noticias</div>
                </div>
            </div>
            <div class="stat-card success">
                <div class="stat-icon">
                    <i class="fas fa-rss"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-number">${data.total_sources || 0}</div>
                    <div class="stat-label">Fuentes</div>
                </div>
            </div>
            <div class="stat-card warning">
                <div class="stat-icon">
                    <i class="fas fa-tags"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-number">${data.total_categories || 0}</div>
                    <div class="stat-label">Categorías</div>
                </div>
            </div>
            <div class="stat-card info">
                <div class="stat-icon">
                    <i class="fas fa-calendar-day"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-number">${(metrics.average_news_per_day || 0).toFixed(1)}</div>
                    <div class="stat-label">Noticias/Día</div>
                </div>
            </div>
            <div class="stat-card danger">
                <div class="stat-icon">
                    <i class="fas fa-clock"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-number">${metrics.peak_hour || 'N/A'}</div>
                    <div class="stat-label">Hora Pico</div>
                </div>
            </div>
            <div class="stat-card secondary">
                <div class="stat-icon">
                    <i class="fas fa-trending-up"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-number">${((metrics.growth_rate || 0) * 100).toFixed(1)}%</div>
                    <div class="stat-label">Crecimiento</div>
                </div>
            </div>
        `;
    }

    renderCharts() {
        this.renderFuentesChart();
        this.renderCategoriasChart();
        this.renderMensualChart();
        this.renderDiasChart();
    }

    renderFuentesChart() {
        const canvas = document.getElementById('newsBySourceChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = this.statsData?.news_by_source || [];
        
        if (data.length === 0) return;

        if (this.charts.has('fuentesChart')) {
            this.charts.get('fuentesChart').destroy();
        }

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(item => item.source),
                datasets: [{
                    data: data.map(item => item.count),
                    backgroundColor: this.gradientColors.slice(0, data.length),
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        this.charts.set('fuentesChart', chart);
    }

    renderCategoriasChart() {
        const canvas = document.getElementById('newsByCategoryChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = this.statsData?.news_by_category || [];
        
        if (data.length === 0) return;

        if (this.charts.has('categoriasChart')) {
            this.charts.get('categoriasChart').destroy();
        }

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.category),
                datasets: [{
                    label: 'Noticias',
                    data: data.map(item => item.count),
                    backgroundColor: this.gradientColors.slice(0, data.length),
                    borderColor: this.gradientColors.slice(0, data.length),
                    borderWidth: 1,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        this.charts.set('categoriasChart', chart);
    }

    renderMensualChart() {
        const canvas = document.getElementById('newsByMonthChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = this.statsData?.news_by_month || [];
        
        if (data.length === 0) return;

        if (this.charts.has('mensualChart')) {
            this.charts.get('mensualChart').destroy();
        }

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(item => item.month),
                datasets: [{
                    label: 'Noticias',
                    data: data.map(item => item.count),
                    borderColor: this.chartColors.primary,
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        this.charts.set('mensualChart', chart);
    }

    renderDiasChart() {
        const canvas = document.getElementById('newsByDayChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = this.statsData?.news_by_day || [];
        
        if (data.length === 0) return;

        if (this.charts.has('diasChart')) {
            this.charts.get('diasChart').destroy();
        }

        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.map(item => item.day),
                datasets: [{
                    label: 'Noticias',
                    data: data.map(item => item.count),
                    backgroundColor: 'rgba(0, 123, 255, 0.2)',
                    borderColor: this.chartColors.primary,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true
                    }
                }
            }
        });

        this.charts.set('diasChart', chart);
    }

    async setupFilters() {
        try {
            if (!window.authManager) {
                console.warn('AuthManager no está disponible para cargar filtros');
                return;
            }
            
            // Cargar fuentes desde el endpoint correcto
            const sourcesRes = await window.authManager.authenticatedFetch(`${this.apiBaseUrl}/api/admin/sources`);
            if (sourcesRes.ok) {
                const sources = await sourcesRes.json();
                const sourceSelect = document.getElementById('sourceFilter');
                if (sourceSelect) {
                    sources.forEach(source => {
                        const option = document.createElement('option');
                        option.value = source.nombre || source;
                        option.textContent = source.nombre || source;
                        sourceSelect.appendChild(option);
                    });
                }
            } else {
                console.warn('No se pudieron cargar las fuentes:', sourcesRes.status);
            }

            // Cargar categorías desde el endpoint correcto
            const categoriesRes = await window.authManager.authenticatedFetch(`${this.apiBaseUrl}/api/admin/categories`);
            if (categoriesRes.ok) {
                const categories = await categoriesRes.json();
                const categorySelect = document.getElementById('categoryFilter');
                if (categorySelect) {
                    categories.forEach(category => {
                        const option = document.createElement('option');
                        option.value = category.nombre || category;
                        option.textContent = category.nombre || category;
                        categorySelect.appendChild(option);
                    });
                }
            } else {
                console.warn('No se pudieron cargar las categorías:', categoriesRes.status);
            }
        } catch (error) {
            console.error('Error cargando filtros:', error);
        }
    }

    async loadNewsTable() {
        console.log('🔄 loadNewsTable() llamado');
        try {
            const skip = (this.currentPage - 1) * this.pageSize;
            
            // Obtener valores de filtros
            const timeFilter = document.getElementById('timeFilter')?.value || 'all';
            const sourceFilter = document.getElementById('sourceFilter')?.value || 'all';
            const categoryFilter = document.getElementById('categoryFilter')?.value || 'all';
            
            // Construir URL con filtros
            const params = new URLSearchParams();
            params.append('skip', skip);
            params.append('limit', this.pageSize);
            params.append('order', 'desc');
            
            // Aplicar filtros de fecha
            if (timeFilter !== 'all') {
                const now = new Date();
                let fecha_desde = null;
                switch (timeFilter) {
                    case 'today':
                        fecha_desde = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString().split('T')[0];
                        break;
                    case 'week':
                        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        fecha_desde = weekAgo.toISOString().split('T')[0];
                        break;
                    case 'month':
                        fecha_desde = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
                        break;
                    case 'year':
                        fecha_desde = new Date(now.getFullYear(), 0, 1).toISOString().split('T')[0];
                        break;
                }
                if (fecha_desde) {
                    params.append('date_from', fecha_desde);
                }
            }
            
            // Aplicar filtros de fuente y categoría
            if (sourceFilter !== 'all') {
                params.append('fuente', sourceFilter);
            }
            
            if (categoryFilter !== 'all') {
                params.append('categoria', categoryFilter);
            }
            
            const url = `${this.apiBaseUrl}/news?${params.toString()}`;
            
            if (!window.authManager) {
                throw new Error('AuthManager no está disponible');
            }
            const response = await window.authManager.authenticatedFetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            const news = data.items || [];
            const total = data.total || 0;
            
            // Calcular total de páginas
            this.totalPages = Math.ceil(total / this.pageSize);
            
            console.log('📊 Dashboard - Datos recibidos:', {
                total,
                pageSize: this.pageSize,
                totalPages: this.totalPages,
                currentPage: this.currentPage,
                newsCount: news.length,
                dataKeys: Object.keys(data)
            });
            
            const tbody = document.getElementById('newsTableBody');
            if (!tbody) {
                console.error('❌ No se encontró newsTableBody');
                return;
            }

            if (news.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center">No hay noticias disponibles</td></tr>';
                this.renderPagination();
                return;
            }

            let html = news.map(article => `
                <tr>
                    <td>${article.id || '-'}</td>
                    <td>${this.truncateText(article.titulo || 'Sin título', 50)}</td>
                    <td>${article.fuente || '-'}</td>
                    <td>${article.categoria || '-'}</td>
                    <td>${article.fecha ? new Date(article.fecha).toLocaleDateString('es-ES') : '-'}</td>
                    <td>${article.tiene_imagenes ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-danger"></i>'}</td>
                    <td>
                        <div class="table-actions">
                            <a href="../page/detalle_noticias.html?id=${article.id}" class="btn btn-sm btn-primary" title="Ver">
                                <i class="fas fa-eye"></i>
                            </a>
                        </div>
                    </td>
                </tr>
            `).join('');
            
            tbody.innerHTML = html;
            
            // Renderizar paginación
            console.log('📄 Llamando a renderPagination()...');
            this.renderPagination();
            console.log('✅ renderPagination() completado');
        } catch (error) {
            console.error('❌ Error cargando tabla de noticias:', error);
            console.error('Stack trace:', error.stack);
            const tbody = document.getElementById('newsTableBody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error al cargar las noticias</td></tr>';
            }
        }
    }
    
    renderPagination() {
        const pagination = document.getElementById('paginationDashboard');
        if (!pagination) {
            console.error('❌ No se encontró el elemento paginationDashboard');
            console.log('🔍 Buscando elementos de paginación:', {
                paginationDashboard: document.getElementById('paginationDashboard'),
                allNavs: document.querySelectorAll('nav'),
                allPagination: document.querySelectorAll('.pagination')
            });
            return;
        }
        
        console.log('🔢 Renderizando paginación:', {
            currentPage: this.currentPage,
            totalPages: this.totalPages,
            pageSize: this.pageSize,
            elementFound: !!pagination
        });
        
        if (this.totalPages <= 1) {
            pagination.innerHTML = '';
            console.log('⚠️ Solo hay 1 página o menos, no se muestra paginación. totalPages:', this.totalPages);
            return;
        }
        
        let html = '';
        
        // Botón anterior
        html += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="window.adminDashboard.changePage(${this.currentPage - 1}); return false;">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
        
        // Números de página
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(this.totalPages, this.currentPage + 2);
        
        if (startPage > 1) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="window.adminDashboard.changePage(1); return false;">1</a></li>`;
            if (startPage > 2) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="window.adminDashboard.changePage(${i}); return false;">${i}</a>
                </li>
            `;
        }
        
        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            html += `<li class="page-item"><a class="page-link" href="#" onclick="window.adminDashboard.changePage(${this.totalPages}); return false;">${this.totalPages}</a></li>`;
        }
        
        // Botón siguiente
        html += `
            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="window.adminDashboard.changePage(${this.currentPage + 1}); return false;">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
        
        pagination.innerHTML = html;
        console.log('✅ Paginación renderizada. HTML length:', html.length, 'Element:', pagination);
        console.log('🔍 Verificación - Elemento visible:', {
            display: window.getComputedStyle(pagination.parentElement).display,
            visibility: window.getComputedStyle(pagination.parentElement).visibility,
            innerHTML: pagination.innerHTML.substring(0, 100)
        });
    }
    
    changePage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.loadNewsTable();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    setupEventListeners() {
        // Botón actualizar datos
        const refreshBtn = document.getElementById('btn-refresh-data');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // Botón exportar datos
        const exportBtn = document.getElementById('btn-export-data');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportData());
        }

        // Botón ejecutar scrapers
        const scrapersBtn = document.getElementById('btn-run-scrapers');
        if (scrapersBtn) {
            scrapersBtn.addEventListener('click', () => this.runScrapers());
        }

        // Botón ver logs
        const logsBtn = document.getElementById('btn-view-logs');
        if (logsBtn) {
            logsBtn.addEventListener('click', () => this.viewLogs());
        }

        // Aplicar filtros
        const applyFiltersBtn = document.getElementById('applyFilters');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        }
    }

    async refreshData() {
        this.currentPage = 1; // Resetear a primera página
        this.showLoading();
        try {
            await this.loadMetricsData();
            await this.loadStatsData();
            await this.loadNewsTable();
            this.showNotification('Datos actualizados correctamente', 'success');
        } catch (error) {
            console.error('Error actualizando datos:', error);
            this.showNotification('Error al actualizar los datos', 'error');
        } finally {
            this.hideLoading();
        }
    }

    exportData() {
        // Redirigir a la página de scrapers (donde está la migración)
        window.location.href = 'noticias.html';
    }

    runScrapers() {
        // Redirigir a la página de scrapers
        window.location.href = 'scrapers.html';
    }

    viewLogs() {
        // Redirigir a la página de noticias
        window.location.href = 'noticias.html';
    }

    async applyFilters() {
        this.currentPage = 1; // Resetear a primera página al aplicar filtros
        const timeFilter = document.getElementById('timeFilter')?.value || 'all';
        const sourceFilter = document.getElementById('sourceFilter')?.value || 'all';
        const categoryFilter = document.getElementById('categoryFilter')?.value || 'all';

        this.showLoading();
        try {
            // Intentar actualizar estadísticas (puede fallar, pero no bloquea la tabla)
            try {
                let url = `${this.apiBaseUrl}/api/stats?`;
                const params = [];

                if (timeFilter !== 'all') {
                    const now = new Date();
                    let fecha_desde = null;
                    switch (timeFilter) {
                        case 'today':
                            fecha_desde = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString().split('T')[0];
                            break;
                        case 'week':
                            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                            fecha_desde = weekAgo.toISOString().split('T')[0];
                            break;
                        case 'month':
                            fecha_desde = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
                            break;
                        case 'year':
                            fecha_desde = new Date(now.getFullYear(), 0, 1).toISOString().split('T')[0];
                            break;
                    }
                    if (fecha_desde) params.push(`fecha_desde=${fecha_desde}`);
                }

                if (sourceFilter !== 'all') {
                    params.push(`fuente=${encodeURIComponent(sourceFilter)}`);
                }

                if (categoryFilter !== 'all') {
                    params.push(`categoria=${encodeURIComponent(categoryFilter)}`);
                }

                url += params.join('&');

                if (window.authManager) {
                    const response = await window.authManager.authenticatedFetch(url);
                    if (response.ok) {
                        const apiData = await response.json();
                        this.statsData = this.transformStatsData(apiData);
                        this.renderStatsSummary();
                        this.renderCharts();
                    }
                }
            } catch (statsError) {
                // Silenciar error de estadísticas, la tabla es más importante
            }
            
            // Siempre recargar tabla de noticias (esto es lo más importante)
            await this.loadNewsTable();
            
            this.showNotification('Filtros aplicados correctamente', 'success');
        } catch (error) {
            console.error('Error aplicando filtros:', error);
            this.showNotification('Error al aplicar los filtros', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showNotification(message, type = 'info') {
        const toast = document.getElementById('notificationToast');
        const toastMessage = document.getElementById('toastMessage');
        if (toast && toastMessage) {
            toastMessage.textContent = message;
            const toastInstance = new bootstrap.Toast(toast);
            toastInstance.show();
        }
    }

    showError(message) {
        console.error(message);
        this.showNotification(message, 'error');
    }

    showLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'flex';
        }
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }

    truncateText(text, maxLength) {
        if (!text) return '-';
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }

    destroy() {
        this.charts.forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts.clear();
        this.isInitialized = false;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.adminDashboard = new AdminDashboard();
    window.adminDashboard.init();
});

// Limpiar al salir de la página
window.addEventListener('beforeunload', () => {
    if (window.adminDashboard) {
        window.adminDashboard.destroy();
    }
});

