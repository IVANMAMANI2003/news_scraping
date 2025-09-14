(function() {
    'use strict';

    const API_BASE_URL = 'http://127.0.0.1:8000';

    // Variables para las gráficas
    let fuentesChart, categoriasChart, mensualChart, diasChart, topNewsChart;
    let chartsLoaded = false;

    // Función para obtener datos de la API
    async function fetchData() {
        try {
            const [newsRes, fuentesRes, categoriasRes] = await Promise.all([
                fetch(`${API_BASE_URL}/news`, { headers: { "Accept": "application/json" } }),
                fetch(`${API_BASE_URL}/news/fuentes/listar`, { headers: { "Accept": "application/json" } }),
                fetch(`${API_BASE_URL}/news/categorias/listar`, { headers: { "Accept": "application/json" } })
            ]);

            if (!newsRes.ok || !fuentesRes.ok || !categoriasRes.ok) {
                throw new Error('Error fetching data from API');
            }

            const news = await newsRes.json();
            const fuentes = await fuentesRes.json();
            const categorias = await categoriasRes.json();

            const newsData = Array.isArray(news) ? news : (news.items || []);
            const fuentesData = Array.isArray(fuentes) ? fuentes : (fuentes.fuentes || []);
            const categoriasData = Array.isArray(categorias) ? categorias : (categorias.categorias || []);

            return { newsData, fuentesData, categoriasData };
        } catch (error) {
            console.error('Error fetching data:', error);
            return { newsData: [], fuentesData: [], categoriasData: [] };
        }
    }

    // Función para procesar datos de noticias por fuente
    function processFuentesData(newsData, fuentesData) {
        const fuentesCount = {};
        fuentesData.forEach(fuente => {
            fuentesCount[fuente] = 0;
        });

        newsData.forEach(news => {
            if (news.fuente && fuentesCount.hasOwnProperty(news.fuente)) {
                fuentesCount[news.fuente]++;
            }
        });

        return Object.entries(fuentesCount)
            .filter(([_, count]) => count > 0)
            .sort((a, b) => b[1] - a[1]);
    }

    // Función para procesar datos de noticias por categoría
    function processCategoriasData(newsData, categoriasData) {
        const categoriasCount = {};
        categoriasData.forEach(categoria => {
            categoriasCount[categoria] = 0;
        });

        newsData.forEach(news => {
            if (news.categoria && categoriasCount.hasOwnProperty(news.categoria)) {
                categoriasCount[news.categoria]++;
            }
        });

        return Object.entries(categoriasCount)
            .filter(([_, count]) => count > 0)
            .sort((a, b) => b[1] - a[1]);
    }

    // Función para procesar datos mensuales
    function processMensualData(newsData) {
        const mensualCount = {};
        
        newsData.forEach(news => {
            if (news.fecha) {
                const date = new Date(news.fecha);
                const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                const monthName = date.toLocaleDateString('es-ES', { year: 'numeric', month: 'short' });
                
                if (!mensualCount[monthKey]) {
                    mensualCount[monthKey] = { name: monthName, count: 0 };
                }
                mensualCount[monthKey].count++;
            }
        });

        return Object.values(mensualCount).sort((a, b) => a.name.localeCompare(b.name));
    }

    // Función para procesar datos por día de la semana
    function processDiasData(newsData) {
        const diasCount = {
            'Lunes': 0, 'Martes': 0, 'Miércoles': 0, 'Jueves': 0,
            'Viernes': 0, 'Sábado': 0, 'Domingo': 0
        };
        
        newsData.forEach(news => {
            if (news.fecha) {
                const date = new Date(news.fecha);
                const dayName = date.toLocaleDateString('es-ES', { weekday: 'long' });
                if (diasCount.hasOwnProperty(dayName)) {
                    diasCount[dayName]++;
                }
            }
        });

        return Object.entries(diasCount);
    }

    // Función para procesar top noticias (simulado por fecha de creación)
    function processTopNewsData(newsData) {
        return newsData
            .filter(news => news.titulo && news.titulo.trim() !== '')
            .sort((a, b) => new Date(b.created_at || b.fecha_extraccion) - new Date(a.created_at || a.fecha_extraccion))
            .slice(0, 10)
            .map((news, index) => ({
                title: news.titulo.length > 50 ? news.titulo.substring(0, 50) + '...' : news.titulo,
                count: Math.floor(Math.random() * 1000) + 100, // Simulado
                index: index + 1
            }));
    }

    // Función para crear gráfica de fuentes
    function createFuentesChart(data) {
        const ctx = document.getElementById('fuentesChart').getContext('2d');
        
        // Destruir gráfica anterior si existe
        if (fuentesChart) {
            fuentesChart.destroy();
            fuentesChart = null;
        }

        fuentesChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(([fuente, _]) => fuente),
                datasets: [{
                    data: data.map(([_, count]) => count),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF',
                        '#FF9F40'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    // Función para crear gráfica de categorías
    function createCategoriasChart(data) {
        const ctx = document.getElementById('categoriasChart').getContext('2d');
        
        // Destruir gráfica anterior si existe
        if (categoriasChart) {
            categoriasChart.destroy();
            categoriasChart = null;
        }

        categoriasChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(([categoria, _]) => categoria),
                datasets: [{
                    label: 'Noticias',
                    data: data.map(([_, count]) => count),
                    backgroundColor: '#36A2EB',
                    borderColor: '#36A2EB',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Función para crear gráfica mensual
    function createMensualChart(data) {
        const ctx = document.getElementById('mensualChart').getContext('2d');
        
        // Destruir gráfica anterior si existe
        if (mensualChart) {
            mensualChart.destroy();
            mensualChart = null;
        }

        mensualChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(item => item.name),
                datasets: [{
                    label: 'Noticias por Mes',
                    data: data.map(item => item.count),
                    borderColor: '#4BC0C0',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Función para crear gráfica de días
    function createDiasChart(data) {
        const ctx = document.getElementById('diasChart').getContext('2d');
        
        // Destruir gráfica anterior si existe
        if (diasChart) {
            diasChart.destroy();
            diasChart = null;
        }

        diasChart = new Chart(ctx, {
            type: 'polarArea',
            data: {
                labels: data.map(([dia, _]) => dia),
                datasets: [{
                    data: data.map(([_, count]) => count),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF',
                        '#FF9F40',
                        '#FF6384'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    // Función para crear gráfica de top noticias
    function createTopNewsChart(data) {
        const ctx = document.getElementById('topNewsChart').getContext('2d');
        
        // Destruir gráfica anterior si existe
        if (topNewsChart) {
            topNewsChart.destroy();
            topNewsChart = null;
        }

        topNewsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.title),
                datasets: [{
                    label: 'Lecturas',
                    data: data.map(item => item.count),
                    backgroundColor: '#9966FF',
                    borderColor: '#9966FF',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2.0,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 100
                        }
                    },
                    y: {
                        ticks: {
                            maxRotation: 0,
                            minRotation: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Función para actualizar resumen estadístico
    function updateStatsSummary(newsData, fuentesData, categoriasData) {
        const totalNews = newsData.length;
        const totalFuentes = fuentesData.length;
        const totalCategorias = categoriasData.length;
        
        // Calcular promedio por día (últimos 30 días)
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        
        const recentNews = newsData.filter(news => {
            const newsDate = new Date(news.fecha || news.created_at);
            return newsDate >= thirtyDaysAgo;
        });
        
        const avgPerDay = Math.round(recentNews.length / 30 * 10) / 10;

        document.getElementById('total-news').textContent = totalNews.toLocaleString();
        document.getElementById('total-fuentes').textContent = totalFuentes;
        document.getElementById('total-categorias').textContent = totalCategorias;
        document.getElementById('avg-per-day').textContent = avgPerDay;
    }

    // Función para actualizar fecha de última actualización
    function updateLastUpdate() {
        const now = new Date();
        const formattedDate = now.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        document.getElementById('last-update').textContent = formattedDate;
    }

    // Función para limpiar todas las gráficas
    function clearAllCharts() {
        if (fuentesChart) {
            fuentesChart.destroy();
            fuentesChart = null;
        }
        if (categoriasChart) {
            categoriasChart.destroy();
            categoriasChart = null;
        }
        if (mensualChart) {
            mensualChart.destroy();
            mensualChart = null;
        }
        if (diasChart) {
            diasChart.destroy();
            diasChart = null;
        }
        if (topNewsChart) {
            topNewsChart.destroy();
            topNewsChart = null;
        }
        chartsLoaded = false;
    }

    // Función principal para cargar todos los datos y gráficas
    async function loadReportes() {
        try {
            // Evitar cargar múltiples veces
            if (chartsLoaded) {
                console.log('Las gráficas ya están cargadas');
                return;
            }

            console.log('Cargando datos para reportes...');
            
            const { newsData, fuentesData, categoriasData } = await fetchData();
            
            if (newsData.length === 0) {
                console.warn('No hay datos disponibles para mostrar');
                return;
            }

            console.log(`Datos cargados: ${newsData.length} noticias, ${fuentesData.length} fuentes, ${categoriasData.length} categorías`);

            // Procesar datos
            const fuentesProcessed = processFuentesData(newsData, fuentesData);
            const categoriasProcessed = processCategoriasData(newsData, categoriasData);
            const mensualProcessed = processMensualData(newsData);
            const diasProcessed = processDiasData(newsData);
            const topNewsProcessed = processTopNewsData(newsData);

            // Crear gráficas solo una vez
            createFuentesChart(fuentesProcessed);
            createCategoriasChart(categoriasProcessed);
            createMensualChart(mensualProcessed);
            createDiasChart(diasProcessed);
            createTopNewsChart(topNewsProcessed);

            // Actualizar resumen
            updateStatsSummary(newsData, fuentesData, categoriasData);
            updateLastUpdate();

            // Marcar como cargado
            chartsLoaded = true;

            console.log('Reportes cargados exitosamente');
        } catch (error) {
            console.error('Error loading reportes:', error);
        }
    }

    // Función para refrescar reportes (disponible globalmente)
    window.refreshReportes = function() {
        console.log('Refrescando reportes...');
        clearAllCharts();
        loadReportes();
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadReportes);
    } else {
        loadReportes();
    }
})();
