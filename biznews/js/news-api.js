(function() {
	"use strict";

	const API_BASE_URL = "http://127.0.0.1:8000";
	const NEWS_ENDPOINT = API_BASE_URL + "/news";

	function getQueryParam(name) {
		const params = new URLSearchParams(window.location.search);
		return params.get(name);
	}

	function parseFirstImage(imagenes) {
		if (!imagenes) return null;
		if (Array.isArray(imagenes)) return imagenes[0] || null;
		// assume comma or pipe separated
		const parts = String(imagenes).split(/[|,;\n]/).map(s => s.trim()).filter(Boolean);
		return parts[0] || null;
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
		const res = await fetch(NEWS_ENDPOINT, { headers: { "Accept": "application/json" } });
		if (!res.ok) throw new Error("Error fetching news: " + res.status);
		const data = await res.json();
		return Array.isArray(data) ? data : (data.items || []);
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
			<div class="text-truncate"><a class="text-white text-uppercase font-weight-semi-bold" href="single.html?id=${encodeURIComponent(n.id)}">${(n.titulo || '').toString()}</a></div>
		`).join('');
		tickers.forEach(ticker => {
			// If ticker is inside white bg (single/category), use darker text
			const isWhite = ticker.classList.contains('bg-white') || (ticker.parentElement && ticker.parentElement.classList.contains('bg-white'));
			const html = news.slice(0, 10).map(n => `
				<div class="text-truncate"><a class="${isWhite ? 'text-secondary' : 'text-white'} text-uppercase font-weight-semi-bold" href="single.html?id=${encodeURIComponent(n.id)}">${(n.titulo || '').toString()}</a></div>
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
					<a class="h2 m-0 text-white text-uppercase font-weight-bold" href="single.html?id=${encodeURIComponent(n.id)}">${n.titulo || 'Sin título'}</a>
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
		const resumen = (n.resumen || n.contenido || '').toString();
		return `
			<div class="col-lg-6">
				<div class="position-relative mb-3">
					<img class="img-fluid w-100" src="${img}" style="object-fit: cover;">
					<div class="bg-white border border-top-0 p-4">
						<div class="mb-2">
							<a class="badge badge-primary text-uppercase font-weight-semi-bold p-2 mr-2" href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}&categoria=${encodeURIComponent(n.categoria||'General')}">${n.categoria || 'General'}</a>
							<a class="text-body" href=""><small>${date}</small></a>
						</div>
						<a class="h4 d-block mb-3 text-secondary text-uppercase font-weight-bold" href="single.html?id=${encodeURIComponent(n.id)}">${n.titulo || 'Sin título'}</a>
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
						<a class="h6 m-0 text-white text-uppercase font-weight-semi-bold" href="single.html?id=${encodeURIComponent(n.id)}">${n.titulo || 'Sin título'}</a>
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
		return `
			<div class="d-flex align-items-center bg-white mb-3" style="height: 110px;">
				<img class="img-fluid" src="${img}" alt="">
				<div class="w-100 h-100 px-3 d-flex flex-column justify-content-center border border-left-0">
					<div class="mb-2">
						<a class="badge badge-primary text-uppercase font-weight-semi-bold p-1 mr-2" href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}&categoria=${encodeURIComponent(n.categoria||'General')}">${n.categoria || 'General'}</a>
						<a class="text-body" href=""><small>${date}</small></a>
					</div>
					<a class="h6 m-0 text-secondary text-uppercase font-weight-bold" href="single.html?id=${encodeURIComponent(n.id)}">${n.titulo || 'Sin título'}</a>
				</div>
			</div>
		`;
	}

	function renderSidebarTrending(news) {
		const sections = Array.from(document.querySelectorAll('.section-title h4')).filter(h => /tranding news/i.test(h.textContent || ''));
		sections.forEach(h => {
			const box = h.closest('.mb-3');
			if (!box) return;
			const content = box.querySelector('.bg-white.border.border-top-0.p-3');
			if (!content) return;
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
		if (!/single\.html$/i.test(location.pathname)) return;
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
			const html = (n.contenido || n.resumen || '').toString()
				.replace(/\n\n+/g, '</p><p>')
				.replace(/\n/g, '<br/>');
			contentBox.innerHTML = `
				<div class="mb-3">
					<a class="badge badge-primary text-uppercase font-weight-semi-bold p-2 mr-2" href="category.html?fuente=${encodeURIComponent(n.fuente||'Otros')}">${n.fuente || 'Otros'}</a>
					<a class="text-body" href=""><small>${date}</small></a>
				</div>
				<h1 class="mb-3 text-secondary text-uppercase font-weight-bold">${n.titulo || 'Sin título'}</h1>
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
				renderFeaturedCarousel(allNews);
				renderLatestNews(allNews);
			}
			renderSidebarTrending(allNews);
			renderCategoryPage(allNews);
			renderSinglePage(allNews);
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


