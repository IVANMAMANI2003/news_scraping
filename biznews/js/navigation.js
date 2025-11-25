/**
 * BizNews Navigation Component
 * Componente de navegación único y reutilizable
 */

class Navigation {
    constructor() {
        this.currentPage = this.getCurrentPage();
        this.isInPageFolder = this.checkIfInPageFolder();
        console.log('🔍 Navigation - currentPage:', this.currentPage);
        console.log('🔍 Navigation - isInPageFolder:', this.isInPageFolder);
        
        this.navItems = [
            {
                href: this.isInPageFolder ? '../index.html' : 'index.html',
                icon: 'fa-home',
                text: 'Inicio',
                id: 'nav-inicio'
            },
            {
                href: this.isInPageFolder ? 'fuentes.html' : 'page/fuentes.html',
                icon: 'fa-rss',
                text: 'Fuentes',
                id: 'nav-fuentes'
            },
            {
                href: this.isInPageFolder ? 'categorias.html' : 'page/categorias.html',
                icon: 'fa-tags',
                text: 'Categorías',
                id: 'nav-categorias'
            },
            {
                href: this.isInPageFolder ? 'servicios.html' : 'page/servicios.html',
                icon: 'fa-box',
                text: 'Servicios',
                id: 'nav-servicios'
            },
            {
                href: this.isInPageFolder ? 'busqueda.html' : 'page/busqueda.html',
                icon: 'fa-search',
                text: 'Búsqueda Avanzada',
                id: 'nav-busqueda',
                requiresAuth: true
            },
            {
                href: this.isInPageFolder ? 'noticias-ia.html' : 'page/noticias-ia.html',
                icon: 'fa-robot',
                text: 'Noticias con IA',
                id: 'nav-noticias-ia',
                badge: 'IA',
                requiresAuth: true,
                requiredPlan: ['enterprise', 'premium']
            },
            {
                href: this.isInPageFolder ? 'contact.html' : 'page/contact.html',
                icon: 'fa-envelope',
                text: 'Contacto',
                id: 'nav-contacto'
            }
        ];
    }

    checkIfInPageFolder() {
        const path = window.location.pathname;
        return path.includes('/page/');
    }

    getCurrentPage() {
        const path = window.location.pathname;
        // Si estamos en /page/ o en la raíz, obtener el nombre del archivo
        let filename = path.split('/').pop() || 'index.html';
        // Si el path incluye 'page/', el filename ya es correcto
        // Si estamos en la raíz y el path es '/', usar index.html
        if (path === '/' || path === '') {
            filename = 'index.html';
        }
        return filename;
    }

    isActive(href) {
        const current = this.currentPage;
        // Comparar solo el nombre del archivo, sin la ruta
        const currentFile = current.split('/').pop();
        const hrefFile = href.split('/').pop();
        return currentFile === hrefFile || 
               (current === '' && hrefFile === 'index.html') ||
               (current === '/' && hrefFile === 'index.html');
    }

    async checkUserAccess() {
        // Verificar si el usuario tiene acceso a noticias con IA
        try {
            // Verificar si hay token en localStorage (puede ser de publicAuthManager o authManager)
            const publicToken = localStorage.getItem('biznews_session');
            const adminToken = localStorage.getItem('biznews_admin_session');
            
            let token = null;
            if (publicToken) {
                try {
                    const session = JSON.parse(publicToken);
                    token = session.access_token;
                } catch (e) {
                    // Ignorar error de parseo
                }
            }
            if (!token && adminToken) {
                try {
                    const session = JSON.parse(adminToken);
                    token = session.access_token;
                } catch (e) {
                    // Ignorar error de parseo
                }
            }
            
            if (!token) {
                return { hasAccess: false, reason: 'not_authenticated', user: null };
            }
            
            // Verificar plan del usuario
            const response = await fetch('http://127.0.0.1:8000/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                return { hasAccess: false, reason: 'not_authenticated', user: null };
            }
            
            const user = await response.json();
            const userPlan = (user.plan || 'free').toLowerCase();
            const userRole = (user.rol || 'user').toLowerCase();
            
            // Solo admin, enterprise y premium tienen acceso
            if (userRole === 'admin' || userPlan === 'enterprise' || userPlan === 'premium') {
                return { hasAccess: true, user };
            }
            
            return { hasAccess: false, reason: 'insufficient_plan', userPlan, user };
        } catch (error) {
            console.error('Error verificando acceso:', error);
            return { hasAccess: false, reason: 'error', user: null };
        }
    }

    async checkAuthentication() {
        // Verificar si el usuario está autenticado
        try {
            const publicToken = localStorage.getItem('biznews_session');
            const adminToken = localStorage.getItem('biznews_admin_session');
            
            let token = null;
            if (publicToken) {
                try {
                    const session = JSON.parse(publicToken);
                    token = session.access_token;
                } catch (e) {
                    // Ignorar error de parseo
                }
            }
            if (!token && adminToken) {
                try {
                    const session = JSON.parse(adminToken);
                    token = session.access_token;
                } catch (e) {
                    // Ignorar error de parseo
                }
            }
            
            if (!token) {
                return { isAuthenticated: false, user: null };
            }
            
            const response = await fetch('http://127.0.0.1:8000/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                return { isAuthenticated: false, user: null };
            }
            
            const user = await response.json();
            return { isAuthenticated: true, user };
        } catch (error) {
            console.error('Error verificando autenticación:', error);
            return { isAuthenticated: false, user: null };
        }
    }

    async render() {
        const homeHref = this.isInPageFolder ? '../index.html' : 'index.html';
        
        // Verificar autenticación y acceso
        const authStatus = await this.checkAuthentication();
        const iaAccess = await this.checkUserAccess();
        
        // Filtrar items de navegación según acceso
        const visibleNavItems = this.navItems.filter(item => {
            if (item.requiresAuth) {
                if (item.id === 'nav-noticias-ia') {
                    return iaAccess.hasAccess;
                } else if (item.id === 'nav-busqueda') {
                    // Búsqueda avanzada requiere solo autenticación (no plan específico)
                    return authStatus.isAuthenticated;
                }
            }
            return true;
        });
        
        // Agregar opciones de login/logout según autenticación
        let authNavItem = '';
        if (authStatus.isAuthenticated) {
            const user = authStatus.user;
            const userRole = (user.rol || 'user').toLowerCase();
            const userName = user.nombre || user.email || 'Usuario';
            
            // Si es admin, mostrar opción de dashboard
            if (userRole === 'admin') {
                authNavItem = `
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user-circle"></i>
                            ${userName}
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="../admin/dashboard.html">
                                <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                            </a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="#" id="logoutBtn">
                                <i class="fas fa-sign-out-alt me-2"></i>Cerrar Sesión
                            </a></li>
                        </ul>
                    </li>
                `;
            } else {
                // Usuario normal
                authNavItem = `
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user-circle"></i>
                            ${userName}
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="#" id="logoutBtn">
                                <i class="fas fa-sign-out-alt me-2"></i>Cerrar Sesión
                            </a></li>
                        </ul>
                    </li>
                `;
            }
        } else {
            // No autenticado, mostrar login
            authNavItem = `
                <li class="nav-item">
                    <a class="nav-link ${this.isActive('login.html') ? 'active' : ''}" 
                       href="${this.isInPageFolder ? 'login.html' : 'page/login.html'}" 
                       id="nav-login">
                        <i class="fas fa-sign-in-alt"></i>
                        Iniciar Sesión
                    </a>
                </li>
            `;
        }
        
        const navHTML = `
            <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
                <div class="container">
                    <a class="navbar-brand" href="${homeHref}">
                        <i class="fas fa-newspaper"></i>
                        BizNews
                    </a>
                    
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav ms-auto">
                            ${visibleNavItems.map(item => `
                                <li class="nav-item">
                                    <a class="nav-link ${this.isActive(item.href) ? 'active' : ''}" 
                                       href="${item.href}" 
                                       id="${item.id}">
                                        <i class="fas ${item.icon}"></i>
                                        ${item.text}
                                        ${item.badge ? `<span class="badge bg-warning text-dark ms-2">${item.badge}</span>` : ''}
                                    </a>
                                </li>
                            `).join('')}
                            ${authNavItem}
                        </ul>
                    </div>
                </div>
            </nav>
        `;
        return navHTML;
    }

    async init() {
        const navContainer = document.getElementById('navigation-container');
        if (navContainer) {
            const renderedHTML = await this.render();
            console.log('🔍 Navigation - Renderizando con', this.navItems.length, 'items');
            console.log('🔍 Navigation - Items:', this.navItems.map(i => i.text));
            navContainer.innerHTML = renderedHTML;
            
            // Configurar logout si existe
            const logoutBtn = document.getElementById('logoutBtn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    // Intentar logout desde ambos managers
                    if (window.publicAuthManager) {
                        await window.publicAuthManager.logout();
                    }
                    if (window.authManager) {
                        await window.authManager.logout();
                    }
                    // Limpiar ambos tokens
                    localStorage.removeItem('biznews_session');
                    localStorage.removeItem('biznews_admin_session');
                    // Redirigir a página principal
                    window.location.href = this.isInPageFolder ? '../index.html' : 'index.html';
                });
            }
            
            console.log('✅ Navigation - HTML renderizado correctamente');
        } else {
            console.warn('❌ No se encontró el contenedor #navigation-container');
        }
    }
}

// Inicializar navegación cuando el DOM esté listo
// Esperar a que publicAuthManager esté disponible si existe
function initializeNavigation() {
    // Si publicAuthManager aún no está disponible, esperar un poco más
    if (typeof window.publicAuthManager === 'undefined') {
        setTimeout(initializeNavigation, 100);
        return;
    }
    
    const nav = new Navigation();
    nav.init().catch(error => {
        console.error('Error inicializando navegación:', error);
    });
}

document.addEventListener('DOMContentLoaded', initializeNavigation);

