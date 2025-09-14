(function() {
	"use strict";

	const API_BASE_URL = "http://127.0.0.1:8000";
	const NEWS_ENDPOINT = API_BASE_URL + "/news";

	function getQueryParam(name) {
		const params = new URLSearchParams(window.location.search);
		return params.get(name);
	}

	function parseFirstImage(imagenes) {
		console.log('parseFirstImage recibió:', imagenes);
		
		// Verificar si imagenes es null, undefined, NaN, o string vacío
		if (!imagenes || imagenes === 'null' || imagenes === 'undefined' || imagenes === 'NaN' || 
			imagenes === '' || imagenes === 'null' || imagenes === 'undefined') {
			console.log('No hay imágenes válidas, usando imagen por defecto');
			return 'img/news-700x435-1.jpg';
		}
		
		let firstImg = null;
		
		if (Array.isArray(imagenes)) {
			firstImg = imagenes[0];
		} else {
			// Convertir a string y limpiar
			const cleanImagenes = String(imagenes).trim();
			if (cleanImagenes === 'null' || cleanImagenes === 'undefined' || cleanImagenes === 'NaN' || 
				cleanImagenes === '' || cleanImagenes === 'null' || cleanImagenes === 'undefined') {
				console.log('Imágenes limpias están vacías, usando imagen por defecto');
				return 'img/news-700x435-1.jpg';
			}
			
			// assume comma or pipe separated
			const parts = cleanImagenes.split(/[|,;\n]/).map(s => s.trim()).filter(Boolean);
			firstImg = parts[0];
		}
		
		console.log('Primera imagen encontrada:', firstImg);
		
		// Verificar si firstImg es válido
		if (!firstImg || firstImg === 'null' || firstImg === 'undefined' || firstImg === 'NaN' || 
			firstImg === '' || firstImg === 'null' || firstImg === 'undefined') {
			console.log('Primera imagen no válida, usando imagen por defecto');
			return 'img/news-700x435-1.jpg';
		}
		
		// Verificar si es una URL válida (http o https)
		if (firstImg.startsWith('http://') || firstImg.startsWith('https://')) {
			console.log('URL válida encontrada:', firstImg);
			// Probar si la imagen se puede cargar
			testImageLoad(firstImg);
			
			// Si es una URL externa, usar proxy para evitar problemas de CORS
			if (firstImg.includes('pachamamaradio.org') || firstImg.includes('punonoticias.com') || 
				firstImg.includes('losandes.com.pe') || firstImg.includes('sinfronteras.pe')) {
				const proxyUrl = `https://images.weserv.nl/?url=${encodeURIComponent(firstImg)}`;
				console.log('Usando proxy para imagen externa:', proxyUrl);
				return proxyUrl;
			}
			
			return firstImg;
		}
		
		// Verificar si es una imagen base64
		if (firstImg.startsWith('data:image/')) {
			console.log('Imagen base64 encontrada');
			return firstImg;
		}
		
		// Verificar si es una ruta relativa válida
		if (firstImg.startsWith('/') || firstImg.startsWith('./') || firstImg.includes('.')) {
			console.log('Ruta relativa encontrada:', firstImg);
			return firstImg;
		}
		
		console.log('Imagen no válida, usando imagen por defecto');
		return 'img/news-700x435-1.jpg';
	}

	function testImageLoad(url) {
		const img = new Image();
		img.onload = function() {
			console.log('✅ Imagen cargada exitosamente:', url);
		};
		img.onerror = function() {
			console.log('❌ Error al cargar imagen:', url);
			// Intentar con proxy de imágenes
			const proxyUrl = `https://images.weserv.nl/?url=${encodeURIComponent(url)}`;
			console.log('Intentando con proxy:', proxyUrl);
			const proxyImg = new Image();
			proxyImg.onload = function() {
				console.log('✅ Imagen cargada con proxy:', proxyUrl);
			};
			proxyImg.onerror = function() {
				console.log('❌ Error incluso con proxy:', proxyUrl);
			};
			proxyImg.src = proxyUrl;
		};
		img.src = url;
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

	function cleanContent(content) {
		if (!content) return '';
		
		// Convertir a string
		let clean = String(content);
		
		// Remover código HTML problemático específico
		clean = clean.replace(/\[tdc_zone[^\]]*\]/g, '');
		clean = clean.replace(/\[vc_row[^\]]*\]/g, '');
		clean = clean.replace(/\[vc_column[^\]]*\]/g, '');
		clean = clean.replace(/\[vc_[^\]]*\]/g, '');
		clean = clean.replace(/\[[^\]]*\]/g, '');
		
		// Remover HTML tags
		clean = clean.replace(/<[^>]*>/g, '');
		
		// Remover códigos CSS específicos problemáticos
		clean = clean.replace(/eyJhbGwiOnsibWFyZ2luLXRvcCI6IjQ4IiwibWFyZ2luLWI[^"]*"/g, '');
		clean = clean.replace(/eyJhbGwiOnsibWFyZ2luLXRvcCI6IjAiLCJtYXJna[^"]*"/g, '');
		
		// Limpiar espacios extra
		clean = clean.replace(/\s+/g, ' ').trim();
		
		// Si el contenido está muy corto, es solo código, o contiene patrones problemáticos
		if (clean.length < 10 || 
			clean.includes('eyJhbGwiOnsibWFyZ2luLXRvcCI6IjQ4IiwibWFyZ2luLWI') ||
			clean.includes('eyJhbGwiOnsibWFyZ2luLXRvcCI6IjAiLCJtYXJna') ||
			clean.match(/^[A-Za-z0-9+/=]+$/) || // Solo base64
			clean.includes('tdc_css=')) {
			return 'Contenido no disponible';
		}
		
		return clean;
	}

	function groupByFuenteAndCategoria(items) {
		const map = new Map();
		for (const n of items) {
			const fuente = (n.fuente || "Otros").trim();
			const categoria = (n.categoria || "General").trim();
			if (!map.has(fuente)) map.set(fuente, new Map());
			const catMap = map.get(fuente);
			if (!catMap.has(categoria)) catMap.set(categoria, []);
			catMap.get(categoria).push(n);
		}
		return map; // Map<fuente, Map<categoria, News[]>>
	}

	async function fetchNews() {
		try {
			console.log('Fetching news from:', NEWS_ENDPOINT);
			const res = await fetch(NEWS_ENDPOINT, { 
				headers: { 
					"Accept": "application/json",
					"Content-Type": "application/json"
				} 
			});
			console.log('Response status:', res.status);
			console.log('Response ok:', res.ok);
			
			if (!res.ok) {
				throw new Error("Error fetching news: " + res.status + " " + res.statusText);
			}
			
			const data = await res.json();
			console.log('Response data:', data);
			const allNews = Array.isArray(data) ? data : (data.items || []);
			
			// Filtrar noticias problemáticas
			const filteredNews = allNews.filter(news => {
				// Excluir noticias con título "Login/Register"
				if (news.titulo && news.titulo.toLowerCase().includes('login/register')) {
					console.log('Excluyendo noticia Login/Register:', news.id);
					return false;
				}
				
				// Excluir noticias con título "Pachamama Radio" que contienen código HTML
				if (news.titulo && news.titulo.toLowerCase().includes('pachamama radio') && 
					news.resumen && news.resumen.includes('[tdc_zone')) {
					console.log('Excluyendo noticia Pachamama Radio con código HTML:', news.id);
					return false;
				}
				
				// Excluir noticias con contenido HTML problemático
				if (news.resumen && news.resumen.includes('[tdc_zone type="tdc_content"]')) {
					console.log('Excluyendo noticia con contenido HTML problemático:', news.id);
					return false;
				}
				
				// Excluir noticias con contenido que contiene mucho código HTML
				if (news.resumen && news.resumen.length > 500 && news.resumen.includes('[')) {
					console.log('Excluyendo noticia con mucho código HTML:', news.id);
					return false;
				}
				
				// Excluir noticias sin título válido
				if (!news.titulo || news.titulo.trim() === '' || news.titulo === 'null' || news.titulo === 'undefined') {
					console.log('Excluyendo noticia sin título válido:', news.id);
					return false;
				}
				
				return true;
			});
			
			console.log(`Filtradas ${allNews.length - filteredNews.length} noticias problemáticas`);
			console.log(`Noticias válidas: ${filteredNews.length}`);
			
			return filteredNews;
		} catch (error) {
			console.error('Error in fetchNews:', error);
			throw error;
		}
	}

	function ensureOwlRefresh(selector) {
		try {
			const $el = window.jQuery && window.jQuery(selector);
			if ($el && $el.data && $el.data('owl.carousel')) {
				$el.trigger('destroy.owl.carousel');
				$el.find('.owl-stage-outer').children().unwrap();
				$el.removeClass("owl-center owl-loaded owl-text-select-on");
			}
		} catch (_) {}
	}

	function renderBreakingNews(news) {
		const tickers = document.querySelectorAll('.tranding-carousel');
		if (!tickers.length) return;
		const items = news.slice(0, 10).map(n => `
			<div class="text-truncate"><a class="text-white text-uppercase font-weight-semi-bold" href="detalle_noticias.html?id=${encodeURIComponent(n.id)}">${(n.titulo || '').toString()}</a></div>
		`).join('');
		tickers.forEach(ticker => {
			// If ticker is inside white bg (single/category), use darker text
			const isWhite = ticker.classList.contains('bg-white') || (ticker.parentElement && ticker.parentElement.classList.contains('bg-white'));
			const html = news.slice(0, 10).map(n => `
				<div class="text-truncate"><a class="${isWhite ? 'text-secondary' : 'text-white'} text-uppercase font-weight-semi-bold" href="detalle_noticias.html?id=${encodeURIComponent(n.id)}">${(n.titulo || '').toString()}</a></div>
			`).join('');
			ensureOwlRefresh('.tranding-carousel');
			ticker.innerHTML = html || items;
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

	function renderNavbar(groups) {
		const container = document.querySelector('.navbar .navbar-nav.mr-auto.py-0');
		if (!container) return;

		// Remove previously injected dropdowns
		container.querySelectorAll('[data-dynamic="true"]').forEach(n => n.remove());

		groups.forEach(([fuente, catMap]) => {
			const li = document.createElement('div');
			li.className = 'nav-item dropdown';
			li.setAttribute('data-dynamic', 'true');
			li.innerHTML = `
				<a href="category.html?fuente=${encodeURIComponent(fuente)}" class="nav-link dropdown-toggle" data-toggle="dropdown">${fuente}</a>
				<div class="dropdown-menu rounded-0 m-0"></div>
			`;
			const menu = li.querySelector('.dropdown-menu');
			Array.from(catMap.keys()).sort().forEach(cat => {
				const a = document.createElement('a');
				a.className = 'dropdown-item';
				a.href = `category.html?fuente=${encodeURIComponent(fuente)}&categoria=${encodeURIComponent(cat)}`;
				a.textContent = cat;
				menu.appendChild(a);
			});
			container.appendChild(li);
		});
	}

	function buildSlide(n) {
		const img = parseFirstImage(n.imagenes) || 'img/news-800x500-1.jpg';
		const date = formatDate(n.fecha || n.created_at);
		return `
			<div class="position-relative overflow-hidden" style="height: 500px;">
				<img class="img-fluid h-100" src="${img}" style="object-fit: cover;">
				<div class="overlay">
					<div class="mb-2">
						<a class="badge badge-primary text-uppercase font-weight-semi-bold p-2 mr-2" href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}">${n.fuente || 'Otros'}</a>
						<a class="text-white" href=""><small>${date}</small></a>
					</div>
					<a class="h2 m-0 text-white text-uppercase font-weight-bold" href="detalle_noticias.html?id=${encodeURIComponent(n.id)}">${n.titulo || 'Sin título'}</a>
				</div>
			</div>
		`;
	}

	function renderMainCarousel(news) {
		const el = document.querySelector('.main-carousel');
		if (!el) return;
		ensureOwlRefresh('.main-carousel');
		el.innerHTML = news.slice(0, 5).map(buildSlide).join('');
		if (window.jQuery && window.jQuery.fn && window.jQuery(el).owlCarousel) {
			window.jQuery(el).owlCarousel({
				autoplay: true,
				smartSpeed: 1500,
				items: 1,
				dots: true,
				loop: true,
				center: true,
			});
		}
	}

	function buildCard(n) {
		const img = parseFirstImage(n.imagenes) || 'img/news-700x435-1.jpg';
		const date = formatDate(n.fecha || n.created_at);
		const resumen = cleanContent(n.resumen || n.contenido || '');
		return `
			<div class="col-lg-6">
				<div class="position-relative mb-3">
					<img class="img-fluid w-100" src="${img}" style="object-fit: cover;">
					<div class="bg-white border border-top-0 p-4">
						<div class="mb-2">
							<a class="badge badge-primary text-uppercase font-weight-semi-bold p-2 mr-2" href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}&categoria=${encodeURIComponent(n.categoria||'General')}">${n.categoria || 'General'}</a>
							<a class="text-body" href=""><small>${date}</small></a>
						</div>
						<a class="h4 d-block mb-3 text-secondary text-uppercase font-weight-bold" href="detalle_noticias.html?id=${encodeURIComponent(n.id)}">${n.titulo || 'Sin título'}</a>
						<p class="m-0">${resumen.length > 140 ? resumen.slice(0, 140) + '…' : resumen}</p>
					</div>
					<div class="d-flex justify-content-between bg-white border border-top-0 p-4">
						<div class="d-flex align-items-center">
							<img class="rounded-circle mr-2" src="img/user.jpg" width="25" height="25" alt="">
							<small>${n.autor || 'Autor desconocido'}</small>
						</div>
					</div>
				</div>
			</div>
		`;
	}

	function buildSmallCard(n) {
		const img = parseFirstImage(n.imagenes) || 'img/news-700x435-1.jpg';
		const date = formatDate(n.fecha || n.created_at);
		const titulo = cleanContent(n.titulo || 'Sin título');
		return `
			<div class="col-md-6 px-0">
				<div class="position-relative overflow-hidden" style="height: 250px;">
					<img class="img-fluid w-100 h-100" src="${img}" style="object-fit: cover;">
					<div class="overlay">
						<div class="mb-2">
							<a class="badge badge-primary text-uppercase font-weight-semi-bold p-2 mr-2"
								href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}&categoria=${encodeURIComponent(n.categoria||'General')}">${n.categoria || 'General'}</a>
							<a class="text-white" href=""><small>${date}</small></a>
						</div>
						<a class="h6 m-0 text-white text-uppercase font-weight-semi-bold" href="detalle_noticias.html?id=${encodeURIComponent(n.id)}">${titulo}</a>
					</div>
				</div>
			</div>
		`;
	}

	function renderSmallNewsCards(news) {
		console.log('=== INICIANDO renderSmallNewsCards ===');
		console.log('Noticias recibidas:', news.length);
		
		// Filtrar noticias que tengan "Puno" como categoría exacta o contengan "Puno" en el título
		const punoNews = news.filter(n => 
			(n.categoria && n.categoria === 'Puno') || 
			(n.titulo && n.titulo.toLowerCase().includes('puno'))
		);
		
		console.log('Total noticias:', news.length);
		console.log('Noticias de Puno:', punoNews.length);
		console.log('Categorías disponibles:', [...new Set(news.map(n => n.categoria))]);
		console.log('Primeras 5 noticias con categoría:', news.slice(0, 5).map(n => ({id: n.id, titulo: n.titulo, categoria: n.categoria})));
		console.log('Noticias de Puno encontradas:', punoNews.map(n => ({id: n.id, titulo: n.titulo, categoria: n.categoria})));
		
		// Buscar el contenedor de las 4 imágenes pequeñas en la columna derecha
		const container = document.getElementById('small-news-container');
		if (!container) {
			console.log('No se encontró el contenedor #small-news-container');
			return;
		}
		
		console.log('Contenedor encontrado:', container);
		
		// Limpiar el contenido existente
		container.innerHTML = '';
		
		// TEMPORAL: Siempre usar las primeras 4 noticias para debug
		let selectedNews = news.slice(0, 4);
		console.log('USANDO PRIMERAS 4 NOTICIAS PARA DEBUG');
		
		console.log('Noticias seleccionadas para mostrar:', selectedNews.length);
		console.log('Detalles de noticias seleccionadas:', selectedNews.map(n => ({id: n.id, titulo: n.titulo})));
		
		// Renderizar las primeras 4 noticias
		const cards = selectedNews.slice(0, 4).map(buildSmallCard).join('');
		console.log('HTML generado:', cards.substring(0, 200) + '...');
		
		container.innerHTML = cards;
		
		console.log('Cards renderizadas:', cards.length > 0 ? 'Sí' : 'No');
		console.log('Noticias mostradas:', selectedNews.length);
		console.log('Contenedor después de insertar:', container.innerHTML.substring(0, 200) + '...');
	}

	function renderLatestNews(news) {
		const container = document.querySelector('.col-lg-8 > .row');
		if (!container) return;
		// Find section title "Latest News" and clear following grid cards, then insert ours at top
		const sectionIndex = Array.from(container.children).findIndex(ch => ch.querySelector && ch.querySelector('.section-title h4'));
		if (sectionIndex >= 0) {
			// Remove all after the title for a simpler integration
			while (container.children.length > sectionIndex + 1) container.removeChild(container.lastElementChild);
			const wrap = document.createElement('div');
			wrap.className = 'row';
			wrap.innerHTML = news.slice(0, 8).map(buildCard).join('');
			container.appendChild(wrap);
		}
	}

	function renderFeaturedCarousel(news) {
		const el = document.querySelector('.news-carousel');
		if (!el) return;
		ensureOwlRefresh('.news-carousel');
		el.innerHTML = news.slice(0, 8).map(n => {
			const img = parseFirstImage(n.imagenes) || 'img/news-700x435-1.jpg';
			const date = formatDate(n.fecha || n.created_at);
			return `
				<div class="position-relative overflow-hidden" style="height: 300px;">
					<img class="img-fluid h-100" src="${img}" style="object-fit: cover;">
					<div class="overlay">
						<div class="mb-2">
							<a class="badge badge-primary text-uppercase font-weight-semi-bold p-2 mr-2" href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}">${n.fuente || 'Otros'}</a>
							<a class="text-white" href=""><small>${date}</small></a>
						</div>
						<a class="h6 m-0 text-white text-uppercase font-weight-semi-bold" href="detalle_noticias.html?id=${encodeURIComponent(n.id)}">${n.titulo || 'Sin título'}</a>
					</div>
				</div>
			`;
		}).join('');
		if (window.jQuery && window.jQuery.fn && window.jQuery(el).owlCarousel) {
			window.jQuery(el).owlCarousel({
				autoplay: true,
				smartSpeed: 1000,
				margin: 30,
				dots: false,
				loop: true,
				nav: true,
				navText: [
					'<i class="fa fa-angle-left" aria-hidden="true"></i>',
					'<i class="fa fa-angle-right" aria-hidden="true"></i>'
				],
				responsive: { 0: { items: 1 }, 576: { items: 1 }, 768: { items: 2 }, 992: { items: 3 }, 1200: { items: 4 } }
			});
		}
	}

	function buildTrendingItem(n) {
		const img = parseFirstImage(n.imagenes) || 'img/news-110x110-1.jpg';
		const date = formatDate(n.fecha || n.created_at);
		const titulo = cleanContent(n.titulo || 'Sin título');
		// Limitar el título a 50 caracteres para evitar desbordamiento
		const tituloCorto = titulo.length > 50 ? titulo.substring(0, 50) + '...' : titulo;
		
		return `
			<div class="d-flex align-items-center bg-white mb-3" style="height: 110px; overflow: hidden;">
				<img class="img-fluid" src="${img}" alt="" style="width: 110px; height: 110px; object-fit: cover; flex-shrink: 0;">
				<div class="w-100 h-100 px-3 d-flex flex-column justify-content-center border border-left-0" style="min-width: 0;">
					<div class="mb-2">
						<a class="badge badge-primary text-uppercase font-weight-semi-bold p-1 mr-2" href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}&categoria=${encodeURIComponent(n.categoria||'General')}">${n.categoria || 'General'}</a>
						<a class="text-body" href=""><small>${date}</small></a>
					</div>
					<a class="h6 m-0 text-secondary text-uppercase font-weight-bold" href="detalle_noticias.html?id=${encodeURIComponent(n.id)}" style="line-height: 1.2; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; word-wrap: break-word;">${tituloCorto}</a>
				</div>
			</div>
		`;
	}

	function renderSidebarTrending(news) {
		// Buscar el contenedor por ID primero
		const container = document.getElementById('trending-news-container');
		if (container) {
			console.log('Renderizando trending news en contenedor ID...');
			container.innerHTML = news.slice(0, 5).map(buildTrendingItem).join('');
			return;
		}
		
		// Fallback: buscar por texto del título
		const sections = Array.from(document.querySelectorAll('.section-title h4')).filter(h => /trending news/i.test(h.textContent || ''));
		sections.forEach(h => {
			const box = h.closest('.mb-3');
			if (!box) return;
			const content = box.querySelector('.bg-white.border.border-top-0.p-3');
			if (!content) return;
			console.log('Renderizando trending news en contenedor encontrado...');
			content.innerHTML = news.slice(0, 5).map(buildTrendingItem).join('');
		});
	}

	function renderCategoryPage(allNews) {
		const fuente = getQueryParam('fuente');
		const categoria = getQueryParam('categoria');
		if (!document.body || !/category\.html$/i.test(location.pathname)) return;
		let filtered = allNews;
		if (fuente) filtered = filtered.filter(n => (n.fuente || '').toLowerCase() === fuente.toLowerCase());
		if (categoria) filtered = filtered.filter(n => (n.categoria || '').toLowerCase() === categoria.toLowerCase());
		const title = document.querySelector('.section-title h4');
		if (title) {
			title.textContent = `Fuente: ${fuente || 'Todas'}${categoria ? ' - ' + categoria : ''}`;
		}
		const container = document.querySelector('.col-lg-8 > .row');
		if (!container) return;
		// Clear everything after the title block
		while (container.children.length > 1) container.removeChild(container.lastElementChild);
		const grid = document.createElement('div');
		grid.className = 'row';
		grid.innerHTML = filtered.map(buildCard).join('');
		container.appendChild(grid);
	}

	function renderSinglePage(allNews) {
		if (!/detalle_noticias\.html$/i.test(location.pathname)) return;
		const id = getQueryParam('id');
		if (!id) return;
		const n = allNews.find(x => String(x.id) === String(id));
		if (!n) return;
		const img = parseFirstImage(n.imagenes) || 'img/news-700x435-1.jpg';
		const date = formatDate(n.fecha || n.created_at);
		const container = document.querySelector('.col-lg-8 .position-relative.mb-3');
		if (!container) return;
		container.querySelector('img.img-fluid.w-100')?.setAttribute('src', img);
		const badge = container.querySelector('.badge');
		if (badge) {
			badge.textContent = n.categoria || 'General';
			badge.setAttribute('href', `category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}&categoria=${encodeURIComponent(n.categoria||'General')}`);
		}
		const dateEl = container.querySelector('.text-body');
		if (dateEl) dateEl.innerHTML = `<small>${date}</small>`;
		const h1 = container.querySelector('h1');
		if (h1) h1.textContent = n.titulo || 'Sin título';
		// Replace paragraphs with contenido
		const contentBox = container.querySelector('.bg-white.border.border-top-0.p-4');
		if (contentBox) {
			const cleanContenido = cleanContent(n.contenido || n.resumen || '');
			const html = cleanContenido
				.replace(/\n\n+/g, '</p><p>')
				.replace(/\n/g, '<br/>');
			contentBox.innerHTML = `
				<div class="mb-3">
					<a class="badge badge-primary text-uppercase font-weight-semi-bold p-2 mr-2" href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}">${n.fuente || 'Otros'}</a>
					<a class="text-body" href=""><small>${date}</small></a>
				</div>
				<h1 class="mb-3 text-secondary text-uppercase font-weight-bold">${cleanContent(n.titulo || 'Sin título')}</h1>
				<p>${html || ''}</p>
			`;
		}
	}

	async function init() {
		try {
			const allNews = await fetchNews();
			const groupsMap = groupByFuenteAndCategoria(allNews);
			const groups = Array.from(groupsMap.entries());
			renderNavbar(groups);
			renderBreakingNews(allNews);
			if (/index\.html$/i.test(location.pathname) || /\/biznews\/?$/i.test(location.pathname)) {
				renderMainCarousel(allNews);
				renderSmallNewsCards(allNews);
				renderFeaturedCarousel(allNews);
				renderLatestNews(allNews);
			}
			renderSidebarTrending(allNews);
			renderCategoryPage(allNews);
			renderSinglePage(allNews);
			
			// Prueba de la imagen específica
			testImageLoad('https://pachamamaradio.org/wp-content/uploads/2025/04/ninos-en-aula-rural-DF.webp');
		} catch (err) {
			// eslint-disable-next-line no-console
			console.error(err);
		}
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();


