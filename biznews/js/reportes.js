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
            await this.loadMetricsData();
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
            
            const data = await response.json();
            console.log('Datos de estadísticas cargados:', data);
            
            this.statsData = data;
            this.renderStatsSummary();
            this.renderCharts();
        } catch (error) {
            console.error('Error cargando estadísticas:', error);
            // Usar datos de ejemplo si falla la API
            this.statsData = this.getMockStatsData();
            this.renderStatsSummary();
            this.renderCharts();
        }
    }

    async loadMetricsData() {
        try {
            console.log('Cargando datos de métricas...');
            const response = await fetch(`${this.apiBaseUrl}/api/metrics`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Datos de métricas cargados:', data);
            
            this.metricsData = data;
        } catch (error) {
            console.error('Error cargando métricas:', error);
            // Usar datos de ejemplo si falla la API
            this.metricsData = this.getMockMetricsData();
        }
    }

    getMockStatsData() {
        return {
            total_news: 1250,
            total_sources: 4,
            total_categories: 8,
            news_by_source: [
                { source: 'Pachamama Radio', count: 450 },
                { source: 'Puno Noticias', count: 380 },
                { source: 'Los Andes', count: 250 },
                { source: 'Sin Fronteras', count: 170 }
            ],
            news_by_category: [
                { category: 'Política', count: 320 },
                { category: 'Economía', count: 280 },
                { category: 'Deportes', count: 250 },
                { category: 'Cultura', count: 200 },
                { category: 'Tecnología', count: 150 },
                { category: 'Salud', count: 120 },
                { category: 'Educación', count: 100 },
                { category: 'Internacional', count: 80 }
            ],
            news_by_month: [
                { month: 'Enero', count: 120 },
                { month: 'Febrero', count: 135 },
                { month: 'Marzo', count: 110 },
                { month: 'Abril', count: 145 },
                { month: 'Mayo', count: 160 },
                { month: 'Junio', count: 140 },
                { month: 'Julio', count: 155 },
                { month: 'Agosto', count: 130 },
                { month: 'Septiembre', count: 125 },
                { month: 'Octubre', count: 140 },
                { month: 'Noviembre', count: 135 },
                { month: 'Diciembre', count: 100 }
            ],
            news_by_day: [
                { day: 'Lunes', count: 180 },
                { day: 'Martes', count: 195 },
                { day: 'Miércoles', count: 185 },
                { day: 'Jueves', count: 200 },
                { day: 'Viernes', count: 175 },
                { day: 'Sábado', count: 160 },
                { day: 'Domingo', count: 155 }
            ],
            top_news: [
                { title: 'Gobierno anuncia nuevas medidas económicas', views: 15420, source: 'Pachamama Radio' },
                { title: 'Equipo local gana campeonato regional', views: 12850, source: 'Puno Noticias' },
                { title: 'Nueva tecnología revoluciona la agricultura', views: 11200, source: 'Los Andes' },
                { title: 'Crisis migratoria en la frontera', views: 9850, source: 'Sin Fronteras' },
                { title: 'Reforma educativa genera controversia', views: 9200, source: 'Pachamama Radio' },
                { title: 'Inversión extranjera aumenta en la región', views: 8750, source: 'Puno Noticias' },
                { title: 'Nuevo hospital mejora atención médica', views: 8200, source: 'Los Andes' },
                { title: 'Festival cultural atrae turistas', views: 7800, source: 'Sin Fronteras' },
                { title: 'Tecnología 5G llega a la ciudad', views: 7350, source: 'Pachamama Radio' },
                { title: 'Deportista local compite en olimpiadas', views: 6900, source: 'Puno Noticias' }
            ]
        };
    }

    getMockMetricsData() {
        return {
            average_news_per_day: 3.4,
            peak_hour: '14:00',
            most_active_source: 'Pachamama Radio',
            most_popular_category: 'Política',
            engagement_rate: 0.68,
            growth_rate: 0.15
        };
    }

    renderStatsSummary() {
        const container = document.getElementById('stats-summary');
        if (!container) return;

        const data = this.statsData;
        const metrics = this.metricsData;

        container.innerHTML = `
            <div class="col-lg-2 col-md-4 mb-4">
                <div class="stat-card primary h-100">
                    <div class="stat-icon">
                        <i class="fas fa-newspaper"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${data.total_news.toLocaleString()}</div>
                        <div class="stat-label">Total Noticias</div>
                    </div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 mb-4">
                <div class="stat-card success h-100">
                    <div class="stat-icon">
                        <i class="fas fa-rss"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${data.total_sources}</div>
                        <div class="stat-label">Fuentes</div>
                    </div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 mb-4">
                <div class="stat-card warning h-100">
                    <div class="stat-icon">
                        <i class="fas fa-tags"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${data.total_categories}</div>
                        <div class="stat-label">Categorías</div>
                    </div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 mb-4">
                <div class="stat-card info h-100">
                    <div class="stat-icon">
                        <i class="fas fa-calendar-day"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${metrics.average_news_per_day}</div>
                        <div class="stat-label">Noticias/Día</div>
                    </div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 mb-4">
                <div class="stat-card danger h-100">
                    <div class="stat-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${metrics.peak_hour}</div>
                        <div class="stat-label">Hora Pico</div>
                    </div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 mb-4">
                <div class="stat-card secondary h-100">
                    <div class="stat-icon">
                        <i class="fas fa-trending-up"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${(metrics.growth_rate * 100).toFixed(1)}%</div>
                        <div class="stat-label">Crecimiento</div>
                    </div>
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
        const data = this.statsData.news_by_source;

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
        const data = this.statsData.news_by_category;

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
        const data = this.statsData.news_by_month;

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
        const data = this.statsData.news_by_day;

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
        const data = this.statsData.top_news.slice(0, 10);

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

    applyTimeFilter(filter) {
        console.log('Aplicando filtro temporal:', filter);
        
        // Aquí iría la lógica para filtrar los datos según el tiempo
        // Por ahora solo mostramos un mensaje
        this.showNotification(`Filtro aplicado: ${filter}`, 'info');
        
        // En una implementación real, aquí se haría una nueva consulta a la API
        // con los parámetros de tiempo correspondientes
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