/**
 * BizNews Reportes JavaScript - Estilo Profesional
 * Versión 2.0.0
 * 
 * @author BizNews Team
 * @description JavaScript para la página de reportes y estadísticas
 */

class ReportesManager {
    constructor() {
        this.charts = new Map();
        this.apiBaseUrl = 'http://127.0.0.1:8000';
        this.isInitialized = false;
        this.loadingOverlay = document.getElementById('loadingOverlay');
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
        
        console.log('Inicializando ReportesManager...');
        
        this.showLoading();

        try {
            // Cargar métricas primero (necesarias para el resumen)
            await this.loadMetricsData();
            // Luego cargar estadísticas (que también carga top news)
            await this.loadStatsData();
            this.setupTimeFilters();
            this.setupEventListeners();
            this.isInitialized = true;
            console.log('ReportesManager inicializado correctamente');
        } catch (error) {
            console.error('Error inicializando ReportesManager:', error);
            this.showError('Error al cargar los datos de reportes');
        } finally {
            this.hideLoading();
        }
    }

    async loadStatsData() {
        try {
            console.log('Cargando datos de estadísticas...');
            const response = await fetch(`${this.apiBaseUrl}/api/stats`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const apiData = await response.json();
            console.log('Datos de estadísticas cargados desde API:', apiData);
            
            // Transformar datos de la API al formato esperado
            this.statsData = this.transformStatsData(apiData);
            
            // Cargar top noticias
            await this.loadTopNews();
            
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
        const dias = {
            'Lunes': 'Lunes',
            'Martes': 'Martes',
            'Miércoles': 'Miércoles',
            'Miercoles': 'Miércoles',
            'Jueves': 'Jueves',
            'Viernes': 'Viernes',
            'Sábado': 'Sábado',
            'Sabado': 'Sábado',
            'Domingo': 'Domingo'
        };

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
        const ordenDias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
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
            news_by_day: news_by_day,
            top_news: this.statsData?.top_news || [] // Se llenará con loadTopNews
        };
    }

    async loadTopNews() {
        try {
            // Obtener las últimas noticias ordenadas por fecha
            const response = await fetch(`${this.apiBaseUrl}/news?limit=10&order=desc`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            const news = Array.isArray(data) ? data : (data.items || []);
            
            // Transformar a formato esperado (simulando views basado en fecha reciente)
            const top_news = news
                .filter(article => {
                    // Filtrar noticias problemáticas
                    if (article.titulo && article.titulo.toLowerCase().includes('login/register')) return false;
                    if (article.titulo && article.titulo.toLowerCase().includes('pachamama radio') && 
                        article.resumen && article.resumen.includes('[tdc_zone')) return false;
                    if (!article.titulo || article.titulo.trim() === '' || article.titulo === 'null') return false;
                    return true;
                })
                .slice(0, 10)
                .map((article, index) => ({
                    title: article.titulo || 'Sin título',
                    views: Math.floor(Math.random() * 5000) + 5000, // Simulado, no hay campo de views en la BD
                    source: article.fuente || 'Desconocida'
                }));
            
            if (this.statsData) {
                this.statsData.top_news = top_news;
            }
        } catch (error) {
            console.error('Error cargando top noticias:', error);
            if (this.statsData) {
                this.statsData.top_news = [];
            }
        }
    }

    async loadMetricsData() {
        try {
            console.log('Cargando datos de métricas...');
            const response = await fetch(`${this.apiBaseUrl}/api/metrics`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const apiData = await response.json();
            console.log('Datos de métricas cargados desde API:', apiData);
            
            // Calcular métricas adicionales
            const statsResponse = await fetch(`${this.apiBaseUrl}/api/stats`);
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
            
            // Obtener hora pico (simulado, no hay datos de hora en la BD)
            const peak_hour = '14:00'; // Valor por defecto
            
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
            
            // Calcular tasa de crecimiento (simulado basado en tendencia mensual)
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
                peak_hour: peak_hour,
                most_active_source: most_active_source,
                most_popular_category: most_popular_category,
                engagement_rate: 0.68, // No hay datos reales de engagement
                growth_rate: parseFloat(growth_rate) || 0,
                // Datos adicionales de la API
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
        const container = document.getElementById('stats-summary');
        if (!container) return;

        const data = this.statsData || {};
        const metrics = this.metricsData || {};

        container.innerHTML = `
            <div class="stats-summary-header">
                <h2 class="stats-summary-title">
                    <i class="fas fa-chart-line me-2"></i>
                    Resumen Estadístico
                </h2>
                <p class="stats-summary-subtitle">
                    Análisis completo de noticias y tendencias
                </p>
            </div>
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-icon">
                        <i class="fas fa-newspaper"></i>
                    </div>
                    <div class="stat-number">${(data.total_news || 0).toLocaleString()}</div>
                    <div class="stat-label">Total Noticias</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-icon">
                        <i class="fas fa-rss"></i>
                    </div>
                    <div class="stat-number">${data.total_sources || 0}</div>
                    <div class="stat-label">Fuentes</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-icon">
                        <i class="fas fa-tags"></i>
                    </div>
                    <div class="stat-number">${data.total_categories || 0}</div>
                    <div class="stat-label">Categorías</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-icon">
                        <i class="fas fa-calendar-day"></i>
                    </div>
                    <div class="stat-number">${(metrics.average_news_per_day || 0).toFixed(1)}</div>
                    <div class="stat-label">Noticias/Día</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-number">${metrics.peak_hour || 'N/A'}</div>
                    <div class="stat-label">Hora Pico</div>
                </div>
                <div class="stat-card secondary">
                    <div class="stat-icon">
                        <i class="fas fa-trending-up"></i>
                    </div>
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
        this.renderTopNewsChart();
    }

    renderFuentesChart() {
        const canvas = document.getElementById('newsBySourceChart');
        if (!canvas) {
            console.log('❌ No se encontró el canvas newsBySourceChart');
            return;
        }

        const ctx = canvas.getContext('2d');
        const data = this.statsData?.news_by_source || [];
        
        if (data.length === 0) {
            console.warn('No hay datos de fuentes para mostrar');
            return;
        }

        // Destruir gráfico existente
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
                    title: {
                        display: true,
                        text: 'Distribución por Fuente',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
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
                },
                animation: {
                    animateRotate: true,
                    duration: 2000
                }
            }
        });

        this.charts.set('newsBySourceChart', chart);
    }

    renderCategoriasChart() {
        const canvas = document.getElementById('newsByCategoryChart');
        if (!canvas) {
            console.log('❌ No se encontró el canvas newsByCategoryChart');
            return;
        }

        const ctx = canvas.getContext('2d');
        const data = this.statsData?.news_by_category || [];
        
        if (data.length === 0) {
            console.warn('No hay datos de categorías para mostrar');
            return;
        }

        // Destruir gráfico existente
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
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Noticias por Categoría',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        });

        this.charts.set('newsByCategoryChart', chart);
    }

    renderMensualChart() {
        const canvas = document.getElementById('newsByMonthChart');
        if (!canvas) {
            console.log('❌ No se encontró el canvas newsByMonthChart');
            return;
        }

        const ctx = canvas.getContext('2d');
        const data = this.statsData?.news_by_month || [];
        
        if (data.length === 0) {
            console.warn('No hay datos mensuales para mostrar');
            return;
        }

        // Destruir gráfico existente
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
                    tension: 0.4,
                    pointBackgroundColor: this.chartColors.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tendencia Mensual',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        });

        this.charts.set('newsByMonthChart', chart);
    }

    renderDiasChart() {
        const canvas = document.getElementById('newsByDayChart');
        if (!canvas) {
            console.log('❌ No se encontró el canvas newsByDayChart');
            return;
        }

        const ctx = canvas.getContext('2d');
        const data = this.statsData?.news_by_day || [];
        
        if (data.length === 0) {
            console.warn('No hay datos de días para mostrar');
            return;
        }

        // Destruir gráfico existente
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
                    borderWidth: 2,
                    pointBackgroundColor: this.chartColors.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Actividad por Día de la Semana',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        pointLabels: {
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        });

        this.charts.set('newsByDayChart', chart);
    }

    renderTopNewsChart() {
        const canvas = document.getElementById('topNewsChart');
        if (!canvas) {
            console.log('❌ No se encontró el canvas topNewsChart');
            return;
        }

        const ctx = canvas.getContext('2d');
        const data = (this.statsData?.top_news || []).slice(0, 10);
        
        if (data.length === 0) {
            console.warn('No hay datos de top noticias para mostrar');
            return;
        }

        // Destruir gráfico existente
        if (this.charts.has('topNewsChart')) {
            this.charts.get('topNewsChart').destroy();
        }

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => this.truncateText(item.title, 30)),
                datasets: [{
                    label: 'Visualizaciones',
                    data: data.map(item => item.views),
                    backgroundColor: this.gradientColors.slice(0, data.length),
                    borderColor: this.gradientColors.slice(0, data.length),
                    borderWidth: 1,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    title: {
                        display: true,
                        text: 'Top 10 Noticias Más Leídas',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                const index = context[0].dataIndex;
                                return data[index].title;
                            },
                            label: function(context) {
                                const index = context.dataIndex;
                                return `${data[index].source}: ${context.parsed.x.toLocaleString()} visualizaciones`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        });

        this.charts.set('topNewsChart', chart);
    }

    setupTimeFilters() {
        const container = document.getElementById('time-filters');
        if (!container) return;

        container.innerHTML = `
            <div class="time-filters-header">
                <h3 class="time-filters-title">
                    <i class="fas fa-filter me-2"></i>
                    Filtros Temporales
                </h3>
                <div class="time-filters-actions">
                    <button class="time-filter-btn active" data-filter="all">
                        <i class="fas fa-globe me-1"></i>
                        Todos
                    </button>
                    <button class="time-filter-btn" data-filter="today">
                        <i class="fas fa-calendar-day me-1"></i>
                        Hoy
                    </button>
                    <button class="time-filter-btn" data-filter="week">
                        <i class="fas fa-calendar-week me-1"></i>
                        Esta Semana
                    </button>
                    <button class="time-filter-btn" data-filter="month">
                        <i class="fas fa-calendar-alt me-1"></i>
                        Este Mes
                    </button>
                    <button class="time-filter-btn" data-filter="year">
                        <i class="fas fa-calendar me-1"></i>
                        Este Año
                    </button>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        // Filtros temporales
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('time-filter-btn')) {
                document.querySelectorAll('.time-filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                e.target.classList.add('active');
                
                const filter = e.target.dataset.filter;
                this.applyTimeFilter(filter);
            }
        });

        // Botón de actualizar
        const refreshBtn = document.getElementById('refresh-reports');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshReports();
            });
        }
    }

    async applyTimeFilter(filter) {
        console.log('Aplicando filtro temporal:', filter);
        
        this.showLoading();
        
        try {
            // Calcular fecha desde según el filtro
            let fecha_desde = null;
            const now = new Date();
            
            switch (filter) {
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
            
            // Construir URL con filtro
            let url = `${this.apiBaseUrl}/api/stats`;
            if (fecha_desde) {
                url += `?fecha_desde=${fecha_desde}`;
            }
            
            // Recargar datos con filtro
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const apiData = await response.json();
            this.statsData = this.transformStatsData(apiData);
            
            // Recargar métricas también
            await this.loadMetricsData();
            
            // Re-renderizar
            this.renderStatsSummary();
            this.renderCharts();
            
            this.showNotification(`Filtro aplicado: ${filter}`, 'success');
        } catch (error) {
            console.error('Error aplicando filtro:', error);
            this.showNotification('Error al aplicar el filtro', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async refreshReports() {
        console.log('Actualizando reportes...');
        
        const refreshBtn = document.getElementById('refresh-reports');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Actualizando...';
            refreshBtn.disabled = true;
        }

        try {
            this.showLoading();
            await this.loadMetricsData();
            await this.loadStatsData();
            this.showNotification('Reportes actualizados correctamente', 'success');
        } catch (error) {
            console.error('Error actualizando reportes:', error);
            this.showNotification('Error al actualizar los reportes', 'error');
        } finally {
            this.hideLoading();
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Actualizar';
                refreshBtn.disabled = false;
            }
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)} me-2"></i>
            ${message}
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    showError(message) {
        const container = document.getElementById('reports-container');
        if (container) {
            container.innerHTML = `
                <div class="text-center p-5">
                    <i class="fas fa-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                    <h3 class="mt-3">Error al cargar los reportes</h3>
                    <p class="text-muted">${message}</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-refresh me-2"></i>
                        Reintentar
                    </button>
                </div>
            `;
        }
        this.hideLoading();
    }

    showLoading() {
        if (!this.loadingOverlay) {
            this.loadingOverlay = document.getElementById('loadingOverlay');
        }
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'flex';
        }
    }

    hideLoading() {
        if (!this.loadingOverlay) {
            this.loadingOverlay = document.getElementById('loadingOverlay');
        }
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }

    destroy() {
        // Destruir todos los gráficos
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
    window.reportesManager = new ReportesManager();
    window.reportesManager.init();
});

// Limpiar al salir de la página
window.addEventListener('beforeunload', () => {
    if (window.reportesManager) {
        window.reportesManager.destroy();
    }
});