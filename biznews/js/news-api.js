/**
 * BizNews News API JavaScript - Versión Simplificada y Robusta
 * Versión 2.2.0
 */

(function() {
	"use strict";

	const API_BASE_URL = "http://127.0.0.1:8000";
	const NEWS_ENDPOINT = API_BASE_URL + "/news";
	const SOCIAL_ENDPOINT = API_BASE_URL + "/social/news";

    console.log('🚀 Iniciando BizNews JavaScript...');

    // Helper function to get correct path for public pages
    function getPagePath(filename) {
        const path = window.location.pathname;
        const isInPageFolder = path.includes('/page/');
        const isRoot = path === '/' || path === '' || path === '/index.html' || 
                      (!path.includes('/page/') && !path.includes('/admin/'));
        
        // If we're in root or index.html, use page/ prefix
        if (isRoot && !isInPageFolder) {
            return `page/${filename}`;
        }
        // If we're already in page/, use relative path
        return filename;
    }

    // Make it globally available
    window.getPagePath = getPagePath;

    function cleanContent(content) {
        if (!content) return '';
        return content.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
    }

    function formatDate(dateString) {
        if (!dateString) return 'Fecha no disponible';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
		} catch (e) {
            return 'Fecha no disponible';
        }
    }

    function getImageUrl(imagenes) {
        if (!imagenes || imagenes === 'null' || imagenes === 'undefined' || imagenes === '') {
            return 'img/news-700x435-1.jpg';
        }
        
        let firstImg = null;
        if (Array.isArray(imagenes)) {
            firstImg = imagenes[0];
        } else {
            const parts = String(imagenes).split(/[|,;\n]/).map(s => s.trim()).filter(Boolean);
            firstImg = parts[0];
        }
        
        if (!firstImg || firstImg === 'null' || firstImg === 'undefined') {
            return 'img/news-700x435-1.jpg';
        }
        
        // Si es URL externa, usar proxy
        if (firstImg.startsWith('http') && !firstImg.includes('localhost')) {
            return `https://images.weserv.nl/?url=${encodeURIComponent(firstImg)}`;
        }
        
        return firstImg;
    }

    async function fetchNews() {
        try {
            console.log('📡 Obteniendo noticias de la API...');
            // Solicitar noticias ordenadas por fecha descendente (más recientes primero)
            const response = await fetch(`${NEWS_ENDPOINT}?order=desc&limit=100`);
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('✅ Noticias obtenidas:', data.total);
            
            // Filtrar noticias problemáticas y excluir noticias de Reddit
            const allNews = data.items || [];
            console.log('📊 Total noticias recibidas:', allNews.length);
            
            // Debug: Mostrar todas las fuentes únicas
            const uniqueSources = [...new Set(allNews.map(n => n.fuente).filter(Boolean))];
            console.log('📋 Fuentes encontradas:', uniqueSources);
            
            // Contar noticias de Reddit antes de filtrar (múltiples variantes)
            const redditVariants = ['reddit', 'Reddit', 'REDDIT'];
            const redditNews = allNews.filter(n => {
                if (!n.fuente) return false;
                const fuenteLower = n.fuente.toLowerCase();
                return redditVariants.some(variant => fuenteLower.includes(variant.toLowerCase()));
            });
            console.log('📱 Noticias de Reddit detectadas:', redditNews.length);
            if (redditNews.length > 0) {
                console.log('📱 Ejemplos de fuentes Reddit:', redditNews.slice(0, 3).map(n => ({id: n.id, fuente: n.fuente, titulo: n.titulo?.substring(0, 40)})));
            }
            
            const filteredNews = allNews.filter(news => {
                if (!news.titulo || news.titulo.trim() === '') return false;
                if (news.titulo.toLowerCase().includes('login/register')) return false;
                if (news.resumen && news.resumen.includes('[tdc_zone')) return false;
                
                // Excluir noticias de Reddit (múltiples variantes)
                if (news.fuente) {
                    const fuenteLower = news.fuente.toLowerCase();
                    if (fuenteLower.includes('reddit')) {
                        console.log('🚫 Excluyendo noticia de Reddit:', {
                            id: news.id,
                            fuente: news.fuente,
                            titulo: news.titulo?.substring(0, 50)
                        });
                        return false;
                    }
                }
                
                return true;
            });
            
            console.log('📰 Noticias válidas (excluyendo Reddit):', filteredNews.length);
            console.log('📰 Noticias filtradas:', allNews.length - filteredNews.length);
            return filteredNews;
        } catch (error) {
            console.error('❌ Error obteniendo noticias:', error);
            return [];
        }
    }

    function buildNewsCard(news) {
        const img = getImageUrl(news.imagenes);
        const date = formatDate(news.fecha || news.created_at);
        
		return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="news-card">
                    <img class="news-image" src="${img}" alt="${cleanContent(news.titulo)}" 
                         onerror="this.src='img/news-700x435-1.jpg'">
                    <div class="news-content">
                        <div class="news-category">${news.categoria || 'General'}</div>
                        <h3 class="news-title">
                            <a href="${getPagePath('detalle_noticias.html')}?id=${news.id}">${cleanContent(news.titulo)}</a>
                        </h3>
                        <p class="news-summary">${cleanContent(news.resumen || news.contenido || '').substring(0, 150)}...</p>
                        <div class="news-meta">
                            <div class="news-author">
                                <img src="img/user.jpg" alt="Autor">
                                <span>${news.fuente || 'BizNews'}</span>
                            </div>
                            <div class="news-date">
                                <i class="fas fa-calendar"></i>
                                <span>${date}</span>
                            </div>
                        </div>
					</div>
				</div>
			</div>
		`;
	}

    function buildSmallCard(news) {
        const img = getImageUrl(news.imagenes);
        const date = formatDate(news.fecha || news.created_at);
        
		return `
            <div class="small-news-card">
                <img class="small-news-image" src="${img}" alt="${cleanContent(news.titulo)}" 
                     onerror="this.src='img/news-700x435-1.jpg'">
                <div class="small-news-content">
                    <h4 class="small-news-title">
                        <a href="${getPagePath('detalle_noticias.html')}?id=${news.id}">${cleanContent(news.titulo)}</a>
                    </h4>
                    <div class="small-news-meta">
                        <i class="fas fa-calendar"></i>
                        <span>${date}</span>
                        <span class="badge badge-primary">${news.categoria || 'General'}</span>
					</div>
				</div>
			</div>
		`;
	}

    function buildSocialCard(item) {
        const img = item.imagen ? (item.imagen.startsWith('http') ? `https://images.weserv.nl/?url=${encodeURIComponent(item.imagen)}` : item.imagen) : 'img/news-700x435-1.jpg';
        const date = formatDate(item.fecha || item.created_at);
        const title = cleanContent(item.titulo || 'Publicación social');
        const resumen = cleanContent(item.resumen || '').substring(0, 140);
        return `
            <div class="small-news-card">
                <img class="small-news-image" src="${img}" alt="${title}" onerror="this.src='img/news-700x435-1.jpg'">
                <div class="small-news-content">
                    <h4 class="small-news-title">
                        <a href="${item.url}" target="_blank" rel="noopener noreferrer">${title}</a>
                    </h4>
                    <div class="small-news-meta">
                        <i class="fas fa-calendar"></i>
                        <span>${date}</span>
                        <span class="badge badge-primary">${item.fuente || 'Social'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    async function fetchSocialNews() {
        try {
            const res = await fetch(SOCIAL_ENDPOINT + '?limit=8');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();
            return data.items || [];
        } catch (e) {
            console.error('Error obteniendo social news:', e);
            return [];
        }
    }

    async function renderSocialNews() {
        const container = document.getElementById('social-news');
        if (!container) return;
        container.innerHTML = '';
        const items = await fetchSocialNews();
        if (items.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No hay publicaciones sociales</p>';
            return;
        }
        container.innerHTML = items.map(buildSocialCard).join('');
    }

    function renderFeaturedNews(news) {
        console.log('🎯 Renderizando noticia destacada...');
        const container = document.getElementById('featured-news');
        if (!container) {
            console.log('❌ No se encontró #featured-news');
            return;
        }
        
        // Limpiar contenido de carga
        container.innerHTML = '';
        
        // Filtrar noticias de Reddit
        const filteredNews = news.filter(n => {
            if (!n.fuente) return true;
            const fuenteLower = n.fuente.toLowerCase();
            const isReddit = fuenteLower.includes('reddit');
            if (isReddit) {
                console.log('🚫 Excluyendo Reddit de destacada:', n.id, n.fuente, n.titulo?.substring(0, 40));
            }
            return !isReddit;
        });
        
        console.log('📊 Noticias para destacada - Total:', news.length, 'Filtradas:', filteredNews.length);
        
        const featured = filteredNews[0];
        if (!featured) {
            container.innerHTML = '<p class="text-center text-muted">No hay noticias disponibles</p>';
            return;
        }
        
        // Verificar que la noticia destacada no sea de Reddit
        if (featured.fuente && featured.fuente.toLowerCase().includes('reddit')) {
            console.error('❌ ERROR: Noticia destacada es de Reddit!', featured);
        }
        
        const img = getImageUrl(featured.imagenes);
        const date = formatDate(featured.fecha || featured.created_at);
        
        container.innerHTML = `
            <div class="news-card">
                <img class="news-image" src="${img}" alt="${cleanContent(featured.titulo)}" 
                     onerror="this.src='img/news-700x435-1.jpg'">
                <div class="news-content">
                    <div class="news-category">${featured.categoria || 'General'}</div>
                    <h2 class="news-title">
                        <a href="detalle_noticias.html?id=${featured.id}">${cleanContent(featured.titulo)}</a>
                    </h2>
                    <p class="news-summary">${cleanContent(featured.resumen || featured.contenido || '')}</p>
                    <div class="news-meta">
                        <div class="news-author">
                            <img src="img/user.jpg" alt="Autor">
                            <span>${featured.fuente || 'BizNews'}</span>
                        </div>
                        <div class="news-date">
                            <i class="fas fa-calendar"></i>
                            <span>${date}</span>
                        </div>
						</div>
					</div>
				</div>
			`;
        console.log('✅ Noticia destacada renderizada');
    }

    function renderLatestNews(news) {
        console.log('📰 Renderizando últimas noticias...');
        const container = document.getElementById('latest-news');
        if (!container) {
            console.log('❌ No se encontró #latest-news');
            return;
        }
        
        // Limpiar contenido de carga
        container.innerHTML = '';
        
        // Filtrar noticias de Reddit
        const filteredNews = news.filter(n => {
            if (!n.fuente) return true;
            const fuenteLower = n.fuente.toLowerCase();
            const isReddit = fuenteLower.includes('reddit');
            if (isReddit) {
                console.log('🚫 Excluyendo Reddit de últimas:', n.id, n.fuente, n.titulo?.substring(0, 40));
            }
            return !isReddit;
        });
        const latestNews = filteredNews.slice(0, 6);
        
        // Verificar que no haya Reddit en últimas noticias
        const redditInLatest = latestNews.filter(n => 
            n.fuente && n.fuente.toLowerCase().includes('reddit')
        );
        if (redditInLatest.length > 0) {
            console.error('❌ ERROR: Hay Reddit en últimas noticias!', redditInLatest);
        }
        
        const cards = latestNews.map(buildNewsCard).join('');
        
        container.innerHTML = `
            <div class="row">
                ${cards}
			</div>
		`;
        console.log('✅ Últimas noticias renderizadas:', latestNews.length, '(Total filtradas:', filteredNews.length, ')');
    }

    function renderSmallNewsCards(news) {
        console.log('🏷️ Renderizando noticias de Puno...');
        const container = document.getElementById('small-news-container');
        if (!container) {
            console.log('❌ No se encontró #small-news-container');
            return;
        }
        
        // Limpiar contenido de carga
        container.innerHTML = '';
        
        // Filtrar noticias de Reddit
        const filteredNews = news.filter(n => {
            return !n.fuente || !n.fuente.toLowerCase().includes('reddit');
        });
        
        const punoNews = filteredNews.filter(n => 
            n.categoria === 'Puno' || 
            (n.titulo && n.titulo.toLowerCase().includes('puno')) ||
            (n.resumen && n.resumen.toLowerCase().includes('puno'))
        );
        
        const selectedNews = punoNews.length > 0 ? punoNews.slice(0, 4) : filteredNews.slice(0, 4);
        const cards = selectedNews.map(buildSmallCard).join('');
        
        container.innerHTML = cards;
        console.log('✅ Noticias de Puno renderizadas:', selectedNews.length);
    }

    function renderTrendingNews(news) {
        console.log('🔥 Renderizando noticias trending...');
        const container = document.getElementById('trending-news');
        if (!container) {
            console.log('❌ No se encontró #trending-news');
            return;
        }
        
        // Limpiar contenido de carga
        container.innerHTML = '';
        
        // Filtrar noticias de Reddit
        const filteredNews = news.filter(n => {
            return !n.fuente || !n.fuente.toLowerCase().includes('reddit');
        });
        const trendingNews = filteredNews.slice(0, 5);
        const cards = trendingNews.map(buildSmallCard).join('');
        
        container.innerHTML = cards;
        console.log('✅ Noticias trending renderizadas:', trendingNews.length);
    }

    function renderPopularCategories(news) {
        console.log('📊 Renderizando categorías populares...');
        const container = document.getElementById('popular-categories');
        if (!container) {
            console.log('❌ No se encontró #popular-categories');
            return;
        }
        
        // Limpiar contenido de carga
        container.innerHTML = '';
        
        // Filtrar noticias de Reddit
        const filteredNews = news.filter(n => {
            return !n.fuente || !n.fuente.toLowerCase().includes('reddit');
        });
        
        const categories = {};
        filteredNews.forEach(n => {
            const cat = n.categoria || 'General';
            categories[cat] = (categories[cat] || 0) + 1;
        });
        
        const sortedCategories = Object.entries(categories)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 6);
        
        const categoryCards = sortedCategories.map(([category, count]) => `
            <a href="categorias.html?categoria=${encodeURIComponent(category)}" class="category-card">
                <div class="category-name">${category}</div>
                <div class="category-count">${count} noticias</div>
            </a>
        `).join('');
        
        container.innerHTML = categoryCards;
        console.log('✅ Categorías populares renderizadas:', sortedCategories.length);
    }

    function updateStats(news) {
        console.log('📊 Actualizando estadísticas...');
        const totalNews = document.getElementById('total-news');
        const totalSources = document.getElementById('total-sources');
        const totalCategories = document.getElementById('total-categories');
        
        // Filtrar noticias de Reddit
        const filteredNews = news.filter(n => {
            return !n.fuente || !n.fuente.toLowerCase().includes('reddit');
        });
        
        if (totalNews) {
            totalNews.textContent = filteredNews.length.toLocaleString();
        }
        
        if (totalSources) {
            const sources = new Set(filteredNews.map(n => n.fuente)).size;
            totalSources.textContent = sources;
        }
        
        if (totalCategories) {
            const categories = new Set(filteredNews.map(n => n.categoria)).size;
            totalCategories.textContent = categories;
        }
        
        console.log('✅ Estadísticas actualizadas');
	}

	async function init() {
		try {
            console.log('🎬 Iniciando aplicación BizNews...');
            
            // Renderizar redes sociales SIEMPRE, independientemente de otras cargas
            renderSocialNews();

            const news = await fetchNews();
            if (news.length === 0) {
                console.log('⚠️ No hay noticias disponibles');
            } else {
                console.log('🎯 Procesando noticias para página principal...');
                
                // Verificar que no haya noticias de Reddit después del filtro
                const redditInFiltered = news.filter(n => 
                    n.fuente && n.fuente.toLowerCase().includes('reddit')
                );
                if (redditInFiltered.length > 0) {
                    console.warn('⚠️ ADVERTENCIA: Hay noticias de Reddit después del filtro:', redditInFiltered.length);
                    console.warn('⚠️ Ejemplos:', redditInFiltered.slice(0, 3).map(n => ({
                        id: n.id,
                        fuente: n.fuente,
                        titulo: n.titulo?.substring(0, 40)
                    })));
                }
                
                // Renderizar secciones principales
                renderFeaturedNews(news);
                renderLatestNews(news);
                renderSmallNewsCards(news);
                renderTrendingNews(news);
                renderPopularCategories(news);
                updateStats(news);
            }
            
            console.log('🎉 ¡Página principal cargada completamente!');
            
        } catch (error) {
            console.error('❌ Error en init:', error);
        }
    }

    // Ejecutar cuando el DOM esté listo
	if (document.readyState === 'loading') {
        console.log('⏳ Esperando DOM...');
		document.addEventListener('DOMContentLoaded', init);
	} else {
        console.log('🚀 DOM ya listo, ejecutando init...');
		init();
	}

    console.log('📜 Script news-api.js cargado');
})();