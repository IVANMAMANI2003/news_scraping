(function() {
    "use strict";

    const API_BASE_URL = "http://127.0.0.1:8000";
    const NEWS_ENDPOINT = API_BASE_URL + "/news";

    async function fetchNews() {
        const res = await fetch(NEWS_ENDPOINT, { headers: { "Accept": "application/json" } });
        if (!res.ok) throw new Error("Error fetching news: " + res.status);
        const data = await res.json();
        const allNews = Array.isArray(data) ? data : (data.items || []);
        
        // Aplicar los mismos filtros que en news-api.js
        const filteredNews = allNews.filter(news => {
            // Excluir noticias con título "Login/Register"
            if (news.titulo && news.titulo.toLowerCase().includes('login/register')) {
                return false;
            }
            
            // Excluir noticias con título "Pachamama Radio" que contienen código HTML
            if (news.titulo && news.titulo.toLowerCase().includes('pachamama radio') && 
                news.resumen && news.resumen.includes('[tdc_zone')) {
                return false;
            }
            
            // Excluir noticias con contenido HTML problemático
            if (news.resumen && news.resumen.includes('[tdc_zone type="tdc_content"]')) {
                return false;
            }
            
            // Excluir noticias con contenido que contiene mucho código HTML
            if (news.resumen && news.resumen.length > 500 && news.resumen.includes('[')) {
                return false;
            }
            
            // Excluir noticias sin título válido
            if (!news.titulo || news.titulo.trim() === '' || news.titulo === 'null' || news.titulo === 'undefined') {
                return false;
            }
            
            return true;
        });
        
        console.log(`Categorías: Filtradas ${allNews.length - filteredNews.length} noticias problemáticas`);
        console.log(`Categorías: Noticias válidas: ${filteredNews.length}`);
        
        return filteredNews;
    }

    async function fetchNewsByCategoria(categoriaName, timeFilter = 'all') {
        // Construir parámetros de fecha
        let dateParams = '';
        if (timeFilter !== 'all') {
            const now = new Date();
            let startDate;
            
            switch (timeFilter) {
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
                const isoDate = startDate.toISOString().split('T')[0];
                dateParams = `&fecha_desde=${isoDate}`;
            }
        }
        
        // Primero obtener solo el conteo total
        const countRes = await fetch(`${API_BASE_URL}/news/categorias/${encodeURIComponent(categoriaName)}?limit=1${dateParams}`, { 
            headers: { "Accept": "application/json" } 
        });
        if (!countRes.ok) throw new Error(`Error fetching count for categoria ${categoriaName}: ${countRes.status}`);
        const countData = await countRes.json();
        const totalCount = countData.total || 0;
        
        console.log(`${categoriaName} (${timeFilter}): Total de noticias en API: ${totalCount}`);
        
        // Si hay noticias, obtener una muestra para aplicar filtros
        if (totalCount > 0) {
            const sampleRes = await fetch(`${API_BASE_URL}/news/categorias/${encodeURIComponent(categoriaName)}${dateParams ? `?${dateParams.slice(1)}` : ''}`, { 
                headers: { "Accept": "application/json" } 
            });
            if (!sampleRes.ok) throw new Error(`Error fetching sample for categoria ${categoriaName}: ${sampleRes.status}`);
            const sampleData = await sampleRes.json();
            const sampleNews = Array.isArray(sampleData) ? sampleData : (sampleData.items || []);
            
            // Aplicar los mismos filtros
            const filteredNews = sampleNews.filter(news => {
                if (news.titulo && news.titulo.toLowerCase().includes('login/register')) return false;
                if (news.titulo && news.titulo.toLowerCase().includes('pachamama radio') && 
                    news.resumen && news.resumen.includes('[tdc_zone')) return false;
                if (news.resumen && news.resumen.includes('[tdc_zone type="tdc_content"]')) return false;
                if (news.resumen && news.resumen.length > 500 && news.resumen.includes('[')) return false;
                if (!news.titulo || news.titulo.trim() === '' || news.titulo === 'null' || news.titulo === 'undefined') return false;
                return true;
            });
            
            // Calcular el porcentaje de noticias válidas y estimar el total filtrado
            const validPercentage = sampleNews.length > 0 ? filteredNews.length / sampleNews.length : 1;
            const estimatedValidCount = Math.round(totalCount * validPercentage);
            
            console.log(`${categoriaName} (${timeFilter}): ${filteredNews.length} válidas de ${sampleNews.length} muestra, estimado total: ${estimatedValidCount}`);
            return { count: estimatedValidCount, news: filteredNews };
        }
        
        return { count: 0, news: [] };
    }

    async function fetchCategorias() {
        try {
            // Usar el endpoint específico de categorías
            const res = await fetch(`${API_BASE_URL}/news/categorias/listar`, { 
                headers: { "Accept": "application/json" } 
            });
            if (!res.ok) throw new Error(`Error fetching categorias: ${res.status}`);
            const data = await res.json();
            const categorias = Array.isArray(data) ? data : (data.categorias || []);
            console.log('Categorías obtenidas del API:', categorias);
            return categorias;
        } catch (error) {
            console.error('Error fetching categorias from API:', error);
            // Fallback: extraer de noticias generales
            const res = await fetch(`${API_BASE_URL}/news`, { 
                headers: { "Accept": "application/json" } 
            });
            if (!res.ok) throw new Error(`Error fetching news: ${res.status}`);
            const data = await res.json();
            const news = Array.isArray(data) ? data : (data.items || []);
            const categorias = [...new Set(news.map(n => n.categoria).filter(Boolean))];
            console.log('Categorías extraídas de noticias (fallback):', categorias);
            return categorias.map(categoria => ({ nombre: categoria }));
        }
    }

    function formatDate(dateStr) {
        if (!dateStr) return "";
        try {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) return String(dateStr);
            return d.toLocaleDateString();
        } catch (e) {
            return String(dateStr);
        }
    }

    function parseFirstImage(imagenes) {
        if (!imagenes) return null;
        if (Array.isArray(imagenes)) return imagenes[0] || null;
        const parts = String(imagenes).split(/[|,;\n]/).map(s => s.trim()).filter(Boolean);
        return parts[0] || null;
    }

    async function renderCategoriasCards(categorias, newsByCategoria, timeFilter = 'all') {
        const container = document.getElementById('categories-container');
        if (!container) return;

        // Agregar clase row para el sistema de grid de Bootstrap
        container.className = 'row';

        const cards = await Promise.all(categorias.map(async (categoria) => {
            const categoriaName = categoria.nombre || categoria;
            const news = newsByCategoria[categoriaName] || [];
            const latestNews = news[0];
            
            // Obtener conteo real del API con filtro de tiempo
            let realCount = news.length;
            try {
                const result = await fetchNewsByCategoria(categoriaName, timeFilter);
                realCount = result.count;
            } catch (error) {
                console.warn(`Error fetching real count for ${categoriaName}:`, error);
            }
            
            const img = latestNews ? parseFirstImage(latestNews.imagenes) : 'img/news-800x500-1.jpg';
            const date = latestNews ? formatDate(latestNews.fecha || latestNews.created_at) : '';

            return `
                <div class="col-xl-3 col-lg-4 col-md-6 col-sm-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="position-relative">
                            <img class="card-img-top" src="${img}" alt="${categoriaName}" style="height: 220px; object-fit: cover;">
                            <div class="position-absolute top-0 right-0 m-2">
                                <span class="badge bg-primary fs-6 px-3 py-2">${realCount} noticias</span>
                            </div>
                        </div>
                        <div class="card-body d-flex flex-column p-4">
                            <h5 class="card-title text-uppercase fw-bold mb-3" style="font-size: 1.1rem; min-height: 2.5rem;">${categoriaName}</h5>
                            ${latestNews ? `
                                <p class="card-text text-muted mb-2" style="font-size: 0.85rem;">
                                    <i class="fas fa-calendar-alt me-1"></i>
                                    Última: ${date}
                                </p>
                                <p class="card-text mb-3" style="font-size: 0.9rem; line-height: 1.5; min-height: 3rem;">
                                    ${(latestNews.titulo || '').substring(0, 120)}${(latestNews.titulo || '').length > 120 ? '...' : ''}
                                </p>
                            ` : '<p class="card-text text-muted mb-3">No hay noticias disponibles</p>'}
                            <div class="mt-auto">
                                <a href="category.html?categoria=${encodeURIComponent(categoriaName)}" class="btn btn-primary w-100 py-2" style="font-size: 0.9rem; font-weight: 600;">
                                    <i class="fas fa-eye me-2"></i>
                                    Ver Noticias
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }));

        container.innerHTML = cards.join('');
        
        // Agregar animación de entrada
        const allCards = container.querySelectorAll('.col-xl-3, .col-lg-4, .col-md-6, .col-sm-6');
        allCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            setTimeout(() => {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }

    function renderBreakingNews(news) {
        const tickers = document.querySelectorAll('.tranding-carousel');
        if (!tickers.length) return;
        
        const items = news.slice(0, 10).map(n => `
            <div class="text-truncate"><a class="text-secondary text-uppercase font-weight-semi-bold" href="detalle_noticias.html?id=${encodeURIComponent(n.id)}">${(n.titulo || '').toString()}</a></div>
        `).join('');
        
        tickers.forEach(ticker => {
            ticker.innerHTML = items;
            if (window.jQuery && window.jQuery.fn && window.jQuery(ticker).owlCarousel) {
                window.jQuery(ticker).owlCarousel({
                    autoplay: true,
                    smartSpeed: 2000,
                    items: 1,
                    dots: false,
                    loop: true,
                    nav: true,
                    navText: [
                        '<i class="fa fa-angle-left"></i>',
                        '<i class="fa fa-angle-right"></i>'
                    ]
                });
            }
        });
    }

    function groupNewsByCategoria(news) {
        const groups = {};
        news.forEach(article => {
            const categoria = article.categoria || 'General';
            if (!groups[categoria]) {
                groups[categoria] = [];
            }
            groups[categoria].push(article);
        });
        
        // Sort news by date within each group
        Object.keys(groups).forEach(categoria => {
            groups[categoria].sort((a, b) => new Date(b.fecha || b.created_at) - new Date(a.fecha || a.created_at));
        });
        
        // Log para debug
        console.log('Categorías encontradas:', Object.keys(groups));
        Object.keys(groups).forEach(categoria => {
            console.log(`${categoria}: ${groups[categoria].length} noticias`);
        });
        
        return groups;
    }

    async function init() {
        try {
            const news = await fetchNews();
            const categorias = await fetchCategorias();
            const newsByCategoria = groupNewsByCategoria(news);
            
            renderBreakingNews(news);
            renderCategoriasCards(categorias, newsByCategoria);
        } catch (err) {
            console.error('Error initializing categorias page:', err);
            const container = document.getElementById('categories-container');
            if (container) {
                container.className = 'row';
                container.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-danger">
                            <h5>Error al cargar las categorías</h5>
                            <p>No se pudieron cargar las categorías de noticias. Por favor, verifica que la API esté funcionando.</p>
                        </div>
                    </div>
                `;
            }
        }
    }

    // Función para manejar filtros de tiempo
    function setupTimeFilters() {
        const filterButtons = document.querySelectorAll('[data-filter]');
        filterButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                // Remover clase active de todos los botones
                filterButtons.forEach(btn => btn.classList.remove('active'));
                // Agregar clase active al botón clickeado
                e.target.classList.add('active');
                
                const timeFilter = e.target.getAttribute('data-filter');
                console.log('Filtro de tiempo seleccionado:', timeFilter);
                
                // Recargar las categorías con el nuevo filtro
                try {
                    const news = await fetchNews();
                    const categorias = await fetchCategorias();
                    const newsByCategoria = groupNewsByCategoria(news);
                    await renderCategoriasCards(categorias, newsByCategoria, timeFilter);
                } catch (error) {
                    console.error('Error applying time filter:', error);
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            init();
            setupTimeFilters();
        });
    } else {
        init();
        setupTimeFilters();
    }
})();
