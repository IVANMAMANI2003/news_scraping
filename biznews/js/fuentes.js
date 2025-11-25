(function() {
    "use strict";

    const API_BASE_URL = "http://127.0.0.1:8000";
    const NEWS_ENDPOINT = API_BASE_URL + "/news";
    const ADVANCED_ENDPOINT = API_BASE_URL + "/api";

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
        
        console.log(`Fuentes: Filtradas ${allNews.length - filteredNews.length} noticias problemáticas`);
        console.log(`Fuentes: Noticias válidas: ${filteredNews.length}`);
        
        return filteredNews;
    }

    async function fetchNewsByFuente(fuenteName, timeFilter = 'all') {
        try {
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
            
            console.log(`Buscando noticias de ${fuenteName} con filtro ${timeFilter}`);
            
            // Usar el endpoint específico de fuentes
            const res = await fetch(`${API_BASE_URL}/news/fuentes/${encodeURIComponent(fuenteName)}${dateParams ? `?${dateParams.slice(1)}` : ''}`, { 
                headers: { "Accept": "application/json" } 
            });
            
            if (!res.ok) {
                throw new Error(`Error fetching news for fuente ${fuenteName}: ${res.status}`);
            }
            
            const data = await res.json();
            const news = Array.isArray(data) ? data : (data.items || []);
            const totalCount = data.total || news.length;
            
            console.log(`${fuenteName} (${timeFilter}): Total de noticias en API: ${totalCount}, obtenidas: ${news.length}`);
            
            // Aplicar filtros de limpieza
            const filteredNews = news.filter(article => {
                if (article.titulo && article.titulo.toLowerCase().includes('login/register')) return false;
                if (article.titulo && article.titulo.toLowerCase().includes('pachamama radio') && 
                    article.resumen && article.resumen.includes('[tdc_zone')) return false;
                if (article.resumen && article.resumen.includes('[tdc_zone type="tdc_content"]')) return false;
                if (article.resumen && article.resumen.length > 500 && article.resumen.includes('[')) return false;
                if (!article.titulo || article.titulo.trim() === '' || article.titulo === 'null' || article.titulo === 'undefined') return false;
                return true;
            });
            
            console.log(`${fuenteName} (${timeFilter}): ${filteredNews.length} noticias válidas después del filtrado`);
            
            return { count: totalCount, news: filteredNews };
        } catch (error) {
            console.error(`Error fetching news for fuente ${fuenteName}:`, error);
            return { count: 0, news: [] };
        }
    }

    async function fetchFuentes() {
        try {
            // Usar el endpoint específico de fuentes
            const res = await fetch(`${API_BASE_URL}/news/fuentes/listar`, { 
                headers: { "Accept": "application/json" } 
            });
            if (!res.ok) throw new Error(`Error fetching fuentes: ${res.status}`);
            const data = await res.json();
            const fuentes = Array.isArray(data) ? data : (data.fuentes || []);
            console.log('Fuentes obtenidas del API:', fuentes);
            return fuentes;
        } catch (error) {
            console.error('Error fetching fuentes from API:', error);
            // Fallback: extraer de noticias generales
            const res = await fetch(`${API_BASE_URL}/news`, { 
                headers: { "Accept": "application/json" } 
            });
            if (!res.ok) throw new Error(`Error fetching news: ${res.status}`);
            const data = await res.json();
            const news = Array.isArray(data) ? data : (data.items || []);
            const fuentes = [...new Set(news.map(n => n.fuente).filter(Boolean))];
            console.log('Fuentes extraídas de noticias (fallback):', fuentes);
            return fuentes.map(fuente => ({ nombre: fuente }));
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

    async function renderFuentesCards(fuentes, newsByFuente, timeFilter = 'all') {
        const container = document.getElementById('sources-container');
        if (!container) return;

        // Agregar clase row para el sistema de grid de Bootstrap
        container.className = 'row';

        const cards = await Promise.all(fuentes.map(async (fuente) => {
            const fuenteName = fuente.nombre || fuente;
            const news = newsByFuente[fuenteName] || [];
            const latestNews = news[0];
            
            // Obtener conteo real del API con filtro de tiempo
            let realCount = news.length;
            try {
                const result = await fetchNewsByFuente(fuenteName, timeFilter);
                realCount = result.count;
            } catch (error) {
                console.warn(`Error fetching real count for ${fuenteName}:`, error);
            }
            
            const img = latestNews ? parseFirstImage(latestNews.imagenes) : 'img/news-800x500-1.jpg';
            const date = latestNews ? formatDate(latestNews.fecha || latestNews.created_at) : '';

            return `
                <div class="col-xl-2 col-lg-3 col-md-4 col-sm-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="position-relative">
                            <img class="card-img-top" src="${img}" alt="${fuenteName}" style="height: 180px; object-fit: cover;">
                            <div class="position-absolute top-0 right-0 m-2">
                                <span class="badge bg-primary">${realCount} noticias</span>
                            </div>
                        </div>
                        <div class="card-body d-flex flex-column p-3">
                            <h5 class="card-title text-uppercase fw-bold mb-2" style="font-size: 0.95rem;">${fuenteName}</h5>
                            ${latestNews ? `
                                <p class="card-text text-muted small mb-2" style="font-size: 0.75rem;">Última: ${date}</p>
                                <p class="card-text small mb-2" style="font-size: 0.85rem; line-height: 1.4;">${(latestNews.titulo || '').substring(0, 80)}${(latestNews.titulo || '').length > 80 ? '...' : ''}</p>
                            ` : '<p class="card-text text-muted small">No hay noticias disponibles</p>'}
                            <div class="mt-auto">
                                <a href="category.html?fuente=${encodeURIComponent(fuenteName)}" class="btn btn-primary btn-sm w-100" style="font-size: 0.8rem;">
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
        const allCards = container.querySelectorAll('.col-xl-2, .col-lg-3, .col-md-4, .col-sm-6');
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

    function groupNewsByFuente(news) {
        const groups = {};
        news.forEach(article => {
            const fuente = article.fuente || 'Otros';
            if (!groups[fuente]) {
                groups[fuente] = [];
            }
            groups[fuente].push(article);
        });
        
        // Sort news by date within each group
        Object.keys(groups).forEach(fuente => {
            groups[fuente].sort((a, b) => new Date(b.fecha || b.created_at) - new Date(a.fecha || a.created_at));
        });
        
        // Log para debug
        console.log('Fuentes encontradas:', Object.keys(groups));
        Object.keys(groups).forEach(fuente => {
            console.log(`${fuente}: ${groups[fuente].length} noticias`);
        });
        
        return groups;
    }

    async function init() {
        try {
            const news = await fetchNews();
            const fuentes = await fetchFuentes();
            const newsByFuente = groupNewsByFuente(news);
            
            renderBreakingNews(news);
            renderFuentesCards(fuentes, newsByFuente);
        } catch (err) {
            console.error('Error initializing fuentes page:', err);
            const container = document.getElementById('sources-container');
            if (container) {
                container.className = 'row';
                container.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-danger">
                            <h5>Error al cargar las fuentes</h5>
                            <p>No se pudieron cargar las fuentes de noticias. Por favor, verifica que la API esté funcionando.</p>
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
                
                // Recargar las fuentes con el nuevo filtro
                try {
                    const news = await fetchNews();
                    const fuentes = await fetchFuentes();
                    const newsByFuente = groupNewsByFuente(news);
                    await renderFuentesCards(fuentes, newsByFuente, timeFilter);
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
