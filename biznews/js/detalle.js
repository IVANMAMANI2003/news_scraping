(function() {
    "use strict";

    const API_BASE_URL = "http://127.0.0.1:8000";
    const NEWS_ENDPOINT = API_BASE_URL + "/news";

    // Obtener ID de la URL
    function getNewsIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get('id');
        if (!id) {
            // Intentar obtener de hash
            const hash = window.location.hash;
            if (hash) {
                return hash.replace('#', '');
            }
        }
        return id;
    }

    // Formatear fecha
    function formatDate(dateStr) {
        if (!dateStr) return "";
        try {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) return String(dateStr);
            return d.toLocaleDateString('es-PE', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch (e) {
            return String(dateStr);
        }
    }

    // Parsear primera imagen
    function parseFirstImage(imagenes) {
        if (!imagenes) return null;
        if (Array.isArray(imagenes)) return imagenes[0] || null;
        const parts = String(imagenes).split(/[|,;\n]/).map(s => s.trim()).filter(Boolean);
        return parts[0] || null;
    }

    // Parsear tags/keywords
    function parseTags(keywords) {
        if (!keywords) return [];
        if (Array.isArray(keywords)) return keywords;
        const parts = String(keywords).split(/[|,;\n]/).map(s => s.trim()).filter(Boolean);
        return parts;
    }

    // Limpiar contenido HTML
    function cleanHTML(html) {
        if (!html) return '';
        // Remover scripts y estilos
        let cleaned = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
        cleaned = cleaned.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
        // Remover atributos problemáticos pero mantener estructura básica
        cleaned = cleaned.replace(/on\w+="[^"]*"/gi, '');
        return cleaned;
    }

    // Cargar noticia por ID
    async function fetchNewsById(id) {
        try {
            const res = await fetch(`${NEWS_ENDPOINT}/${id}`, {
                headers: { "Accept": "application/json" }
            });
            if (!res.ok) {
                if (res.status === 404) {
                    throw new Error("Noticia no encontrada");
                }
                throw new Error(`Error: ${res.status}`);
            }
            return await res.json();
        } catch (error) {
            console.error('Error fetching news:', error);
            throw error;
        }
    }

    // Cargar noticias relacionadas
    async function fetchRelatedNews(categoria, fuente, excludeId, limit = 5) {
        try {
            let url = `${NEWS_ENDPOINT}?limit=${limit}`;
            if (categoria) {
                url += `&categoria=${encodeURIComponent(categoria)}`;
            } else if (fuente) {
                url += `&fuente=${encodeURIComponent(fuente)}`;
            }
            
            const res = await fetch(url, {
                headers: { "Accept": "application/json" }
            });
            if (!res.ok) throw new Error(`Error: ${res.status}`);
            
            const data = await res.json();
            const news = Array.isArray(data) ? data : (data.items || []);
            
            // Filtrar la noticia actual y noticias problemáticas
            return news.filter(article => {
                if (article.id === excludeId) return false;
                if (article.titulo && article.titulo.toLowerCase().includes('login/register')) return false;
                if (article.titulo && article.titulo.toLowerCase().includes('pachamama radio') && 
                    article.resumen && article.resumen.includes('[tdc_zone')) return false;
                if (article.resumen && article.resumen.includes('[tdc_zone type="tdc_content"]')) return false;
                if (!article.titulo || article.titulo.trim() === '' || article.titulo === 'null') return false;
                return true;
            }).slice(0, limit);
        } catch (error) {
            console.error('Error fetching related news:', error);
            return [];
        }
    }

    // Cargar categorías populares
    async function fetchPopularCategories(limit = 8) {
        try {
            const res = await fetch(`${NEWS_ENDPOINT}/categorias/listar`, {
                headers: { "Accept": "application/json" }
            });
            if (!res.ok) throw new Error(`Error: ${res.status}`);
            const categorias = await res.json();
            return Array.isArray(categorias) ? categorias.slice(0, limit) : [];
        } catch (error) {
            console.error('Error fetching categories:', error);
            return [];
        }
    }

    // Renderizar noticia
    function renderNews(news) {
        const container = document.getElementById('article-container');
        if (!container) return;

        const img = parseFirstImage(news.imagenes || news.imagen_principal);
        const tags = parseTags(news.tags || news.keywords);
        const fecha = formatDate(news.fecha || news.created_at);
        const contenido = cleanHTML(news.contenido || news.resumen || '');

        container.innerHTML = `
            <div class="article-header fade-in">
                ${news.categoria ? `<span class="article-category">${news.categoria}</span>` : ''}
                <h1 class="article-title">${news.titulo || 'Sin título'}</h1>
                <div class="article-meta">
                    ${news.fuente ? `
                        <div class="meta-item">
                            <i class="fas fa-newspaper"></i>
                            <span>${news.fuente}</span>
                        </div>
                    ` : ''}
                    ${fecha ? `
                        <div class="meta-item">
                            <i class="fas fa-calendar-alt"></i>
                            <span>${fecha}</span>
                        </div>
                    ` : ''}
                    ${news.autor ? `
                        <div class="meta-item">
                            <i class="fas fa-user"></i>
                            <span>${news.autor}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            ${img ? `
                <div class="article-content">
                    <img src="${img}" alt="${news.titulo || ''}" class="article-image" onerror="this.style.display='none'">
                </div>
            ` : ''}
            
            <div class="article-content">
                ${news.resumen && news.resumen !== contenido ? `
                    <div class="article-summary">
                        ${news.resumen}
                    </div>
                ` : ''}
                
                ${contenido ? `
                    <div class="article-text">
                        ${contenido}
                    </div>
                ` : news.resumen ? `
                    <div class="article-text">
                        ${news.resumen}
                    </div>
                ` : ''}
                
                ${news.url ? `
                    <div class="mt-4">
                        <a href="${news.url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-action">
                            <i class="fas fa-external-link-alt"></i>
                            Ver noticia original
                        </a>
                    </div>
                ` : ''}
            </div>
            
            <div class="article-footer">
                ${tags.length > 0 ? `
                    <div class="article-tags">
                        <div class="tags-label">
                            <i class="fas fa-tags"></i>
                            Etiquetas:
                        </div>
                        <div class="tag-list">
                            ${tags.map(tag => `
                                <a href="categorias.html?categoria=${encodeURIComponent(tag)}" class="tag">
                                    ${tag}
                                </a>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="article-actions">
                    <a href="index.html" class="btn btn-secondary btn-action">
                        <i class="fas fa-arrow-left"></i>
                        Volver al inicio
                    </a>
                    ${news.categoria ? `
                        <a href="categorias.html?categoria=${encodeURIComponent(news.categoria)}" class="btn btn-primary btn-action">
                            <i class="fas fa-tag"></i>
                            Ver más de ${news.categoria}
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Renderizar noticias relacionadas
    function renderRelatedNews(news) {
        const container = document.getElementById('related-news');
        if (!container) return;

        if (news.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay noticias relacionadas disponibles.</p>';
            return;
        }

        container.innerHTML = news.map(article => {
            const img = parseFirstImage(article.imagenes || article.imagen_principal) || 'img/news-110x110-1.jpg';
            const fecha = formatDate(article.fecha || article.created_at);
            const titulo = (article.titulo || '').substring(0, 80);
            
            return `
                <div class="related-item">
                    <img src="${img}" alt="${titulo}" class="related-image" onerror="this.src='img/news-110x110-1.jpg'">
                    <div class="related-content">
                        <h4 class="related-title">
                            <a href="detalle_noticias.html?id=${article.id}">${titulo}${article.titulo && article.titulo.length > 80 ? '...' : ''}</a>
                        </h4>
                        <div class="related-meta">
                            ${fecha ? `<i class="fas fa-calendar-alt"></i> ${fecha}` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Renderizar categorías populares
    function renderPopularCategories(categorias) {
        const container = document.getElementById('popular-categories');
        if (!container) return;

        if (categorias.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay categorías disponibles.</p>';
            return;
        }

        container.innerHTML = categorias.map(categoria => `
            <a href="categorias.html?categoria=${encodeURIComponent(categoria)}" class="tag mb-2 d-inline-block">
                ${categoria}
            </a>
        `).join('');
    }

    // Inicializar página
    async function init() {
        const newsId = getNewsIdFromURL();
        
        if (!newsId) {
            const container = document.getElementById('article-container');
            if (container) {
                container.innerHTML = `
                    <div class="error-state">
                        <div class="error-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h2 class="error-title">ID de noticia no especificado</h2>
                        <p class="error-description">
                            No se encontró un ID de noticia en la URL. Por favor, selecciona una noticia desde la página principal.
                        </p>
                        <a href="index.html" class="btn btn-primary btn-action">
                            <i class="fas fa-arrow-left"></i>
                            Volver al inicio
                        </a>
                    </div>
                `;
            }
            return;
        }

        try {
            // Cargar noticia principal
            const news = await fetchNewsById(newsId);
            renderNews(news);

            // Cargar noticias relacionadas
            const relatedNews = await fetchRelatedNews(news.categoria, news.fuente, news.id);
            renderRelatedNews(relatedNews);

            // Cargar categorías populares
            const categories = await fetchPopularCategories();
            renderPopularCategories(categories);

            // Actualizar título de la página
            document.title = `${news.titulo || 'Noticia'} - BizNews`;

        } catch (error) {
            console.error('Error initializing detail page:', error);
            const container = document.getElementById('article-container');
            if (container) {
                container.innerHTML = `
                    <div class="error-state">
                        <div class="error-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h2 class="error-title">Error al cargar la noticia</h2>
                        <p class="error-description">
                            ${error.message || 'No se pudo cargar la noticia. Por favor, verifica que la API esté funcionando.'}
                        </p>
                        <a href="index.html" class="btn btn-primary btn-action">
                            <i class="fas fa-arrow-left"></i>
                            Volver al inicio
                        </a>
                    </div>
                `;
            }
        }
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

