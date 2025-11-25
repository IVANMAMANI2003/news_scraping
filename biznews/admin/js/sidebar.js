/**
 * Sidebar Component - Componente centralizado para el menú lateral del admin
 * BizNews Admin
 * VERSIÓN 2.0.2 - Con logs agresivos
 */

// Log INMEDIATO - debe ejecutarse SIEMPRE, incluso si hay errores después
(function() {
    'use strict';
    try {
        console.log('═══════════════════════════════════════');
        console.log('📦📦📦 SIDEBAR.JS CARGADO - VERSIÓN 2.0.2 📦📦📦');
        console.log('📦 Timestamp:', new Date().toISOString());
        console.log('📦 Document readyState:', document.readyState);
        console.log('📦 window.authManager:', typeof window.authManager !== 'undefined' ? '✅ Disponible' : '❌ No disponible');
        console.log('📦 window.location.href:', window.location.href);
        console.log('═══════════════════════════════════════');
    } catch (e) {
        console.error('❌ ERROR en logs iniciales:', e);
    }
})();

class SidebarManager {
    constructor() {
        this.currentPage = this.getCurrentPage();
    }

    /**
     * Obtener la página actual basada en la URL
     */
    getCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop() || 'dashboard.html';
        // También verificar hash si existe
        const hash = window.location.hash.replace('#', '');
        return hash || filename;
    }

    /**
     * Verificar si el usuario tiene acceso a funciones de IA
     */
    hasIAAccess() {
        if (!window.authManager) {
            console.log('❌ authManager no disponible');
            return false;
        }
        
        const currentUser = window.authManager.getCurrentUser();
        if (!currentUser) {
            console.log('❌ No hay usuario en sesión');
            return false;
        }
        
        console.log('👤 Usuario actual:', currentUser);
        
        const userRole = (currentUser.rol || '').toLowerCase();
        const userPlan = (currentUser.plan || '').toLowerCase();
        
        console.log('🔍 Verificando acceso - Rol:', userRole, 'Plan:', userPlan);
        
        // Solo admin y enterprise tienen acceso
        const hasAccess = userRole === 'admin' || userPlan === 'enterprise';
        console.log('✅ Acceso a IA:', hasAccess);
        
        return hasAccess;
    }

    /**
     * Generar el HTML del sidebar
     */
    generateSidebarHTML() {
        console.log('🔨 generateSidebarHTML() llamado');
        const menuItems = [
            {
                section: 'main',
                items: [
                    { href: 'dashboard.html', icon: 'fa-tachometer-alt', text: 'Dashboard', tooltip: 'Dashboard' }
                    // Reportes comentado - NO debe aparecer
                    // { href: '#reportes.html', icon: 'fa-chart-bar', text: 'Reportes', tooltip: 'Reportes' }
                ]
            },
            {
                section: 'gestión',
                title: 'GESTIÓN',
                items: [
                    { href: 'noticias.html', icon: 'fa-newspaper', text: 'Noticias', tooltip: 'Noticias' },
                    { href: 'fuentes.html', icon: 'fa-rss', text: 'Fuentes', tooltip: 'Fuentes' },
                    { href: 'categorias.html', icon: 'fa-tags', text: 'Categorías', tooltip: 'Categorías' },
                    { href: 'usuarios.html', icon: 'fa-users', text: 'Usuarios', tooltip: 'Usuarios' },
                    { href: 'api-keys.html', icon: 'fa-key', text: 'API Keys', tooltip: 'API Keys' }
                    
                ]
            },
            {
                section: 'scrapers',
                title: 'SCRAPERS',
                items: [
                    { href: 'scrapers.html', icon: 'fa-spider', text: 'Gestión Scrapers', tooltip: 'Gestión Scrapers' }
                ]
            },
            {
                section: 'gestion-con-ia',
                title: 'GESTIÓN DE NOTICIAS CON IA',
                items: [
                    { href: 'limpieza.html', icon: 'fa-magic', text: 'Limpieza con IA', tooltip: 'Limpieza de Noticias con IA' }
                ]
            }
        ];
        
        console.log('📋 Total de secciones en menuItems:', menuItems.length);
        console.log('📋 Secciones:', menuItems.map(m => m.section || m.title || 'sin título'));
        
        // Footer siempre visible
        menuItems.push({
            section: 'footer',
            items: [
                { href: '../index.html', icon: 'fa-home', text: 'Página Pública', tooltip: 'Página Pública' },
                { href: '#', icon: 'fa-sign-out-alt', text: 'Cerrar Sesión', tooltip: 'Cerrar Sesión', id: 'logoutBtn' }
            ]
        });

        let html = `
            <div class="sidebar-header">
                <h2 class="sidebar-title" style="color: white !important; white-space: nowrap; overflow: visible;">
                    <i class="fas fa-bars sidebar-collapse-btn" id="sidebarCollapseBtn" style="color: white !important; cursor: pointer;" title="Colapsar/Expandir menú"></i>
                    <span class="sidebar-title-text" style="color: white !important;">Menú Admin</span>
                </h2>
            </div>
        `;

        menuItems.forEach((section, sectionIndex) => {
            if (section.title) {
                if (sectionIndex > 0) {
                    html += '<div class="sidebar-divider"></div>';
                }
                html += `<div class="sidebar-section-title">${section.title}</div>`;
            } else if (sectionIndex > 0 && !section.title) {
                html += '<div class="sidebar-divider"></div>';
            }

            html += '<ul class="sidebar-menu">';
            section.items.forEach(item => {
                // Comparar sin el # si existe
                const itemHref = item.href.replace('#', '');
                const currentPageClean = this.currentPage.replace('#', '');
                const isActive = itemHref === currentPageClean ? 'active' : '';
                const idAttr = item.id ? `id="${item.id}"` : '';
                html += `
                    <li class="sidebar-menu-item">
                        <a href="${item.href}" class="sidebar-menu-link ${isActive}" data-tooltip="${item.tooltip}" ${idAttr}>
                            <i class="fas ${item.icon}"></i>
                            <span class="menu-text">${item.text}</span>
                        </a>
                    </li>
                `;
            });
            html += '</ul>';
        });

        console.log('✅ HTML generado exitosamente');
        console.log('🔍 Verificando contenido del HTML:');
        console.log('  - Contiene "GESTIÓN":', html.includes('GESTIÓN'));
        console.log('  - Contiene "SCRAPERS":', html.includes('SCRAPERS'));
        console.log('  - Contiene "GESTIÓN DE NOTICIAS CON IA":', html.includes('GESTIÓN DE NOTICIAS CON IA'));
        console.log('  - Contiene "Limpieza con IA":', html.includes('Limpieza con IA'));
        
        return html;
    }

    /**
     * Inicializar el sidebar
     */
    init() {
        console.log('🔧 Inicializando SidebarManager...');
        const sidebar = document.getElementById('adminSidebar');
        if (sidebar) {
            console.log('✅ Elemento #adminSidebar encontrado');
            // Esperar a que authManager esté disponible
            if (!window.authManager) {
                console.log('⏳ Esperando authManager...');
                setTimeout(() => this.init(), 200);
                return;
            }
            
            console.log('📝 Generando HTML del sidebar...');
            const html = this.generateSidebarHTML();
            console.log('📊 HTML generado, longitud:', html.length);
            console.log('🔍 Verificando si contiene "GESTIÓN DE NOTICIAS CON IA":', html.includes('GESTIÓN DE NOTICIAS CON IA'));
            console.log('🔍 Verificando si contiene "Reportes":', html.includes('Reportes'));
            
            // Verificar que el HTML no esté vacío
            if (!html || html.length < 100) {
                console.error('❌ ERROR: HTML generado está vacío o es muy corto');
                return;
            }
            
            // Limpiar el sidebar antes de insertar el nuevo HTML
            sidebar.innerHTML = '';
            
            // Insertar el nuevo HTML
            sidebar.innerHTML = html;
            
            // Verificar que se insertó correctamente
            const insertedHTML = sidebar.innerHTML;
            console.log('✅ HTML insertado en el sidebar');
            console.log('🔍 Verificando contenido insertado:');
            console.log('  - Contiene "GESTIÓN DE NOTICIAS CON IA":', insertedHTML.includes('GESTIÓN DE NOTICIAS CON IA'));
            console.log('  - Contiene "Reportes":', insertedHTML.includes('Reportes'));
            console.log('  - Contiene "fa-chart-bar" (icono de Reportes):', insertedHTML.includes('fa-chart-bar'));
            
            // Verificar si el HTML insertado es la versión antigua (tiene "Reportes" o no tiene "GESTIÓN DE NOTICIAS CON IA")
            const tieneReportes = insertedHTML.includes('Reportes') || (insertedHTML.includes('fa-chart-bar') && insertedHTML.includes('reportes.html'));
            const tieneGestionIA = insertedHTML.includes('GESTIÓN DE NOTICIAS CON IA');
            const tieneGestionMinusculas = insertedHTML.includes('sidebar-section-title">Gestión') && !insertedHTML.includes('sidebar-section-title">GESTIÓN');
            const tieneScrapersMinusculas = insertedHTML.includes('sidebar-section-title">Scrapers') && !insertedHTML.includes('sidebar-section-title">SCRAPERS');
            
            if (tieneReportes || !tieneGestionIA || tieneGestionMinusculas || tieneScrapersMinusculas) {
                console.warn('⚠️ ADVERTENCIA: El sidebar contiene versión antigua en caché. Forzando regeneración...');
                console.warn('  - Tiene Reportes:', tieneReportes);
                console.warn('  - NO tiene GESTIÓN DE NOTICIAS CON IA:', !tieneGestionIA);
                console.warn('  - Tiene "Gestión" en minúsculas:', tieneGestionMinusculas);
                console.warn('  - Tiene "Scrapers" en minúsculas:', tieneScrapersMinusculas);
                
                // Limpiar completamente
                sidebar.innerHTML = '';
                
                // Esperar un momento y regenerar
                setTimeout(() => {
                    console.log('🔄 Regenerando sidebar...');
                    const newHTML = this.generateSidebarHTML();
                    sidebar.innerHTML = newHTML;
                    this.setupEventListeners();
                    
                    // Verificar nuevamente
                    const finalHTML = sidebar.innerHTML;
                    console.log('✅ Sidebar regenerado forzadamente');
                    console.log('🔍 Verificación final:');
                    console.log('  - Contiene "Reportes":', finalHTML.includes('Reportes'));
                    console.log('  - Contiene "GESTIÓN DE NOTICIAS CON IA":', finalHTML.includes('GESTIÓN DE NOTICIAS CON IA'));
                    console.log('  - Contiene "GESTIÓN" (mayúsculas):', finalHTML.includes('sidebar-section-title">GESTIÓN'));
                    console.log('  - Contiene "SCRAPERS" (mayúsculas):', finalHTML.includes('sidebar-section-title">SCRAPERS'));
                }, 200);
            }
            
            this.setupEventListeners();
            
            const hasAccess = this.hasIAAccess();
            console.log('✅ Sidebar inicializado correctamente');
            console.log('📄 Página actual:', this.currentPage);
            console.log('🤖 Acceso a IA:', hasAccess ? '✅ Sí' : '❌ No');
        } else {
            console.error('❌ No se encontró el elemento #adminSidebar');
        }
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Botón de colapsar/expandir
        const collapseBtn = document.getElementById('sidebarCollapseBtn');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => {
                document.body.classList.toggle('sidebar-collapsed');
            });
        }

        // Botón de logout
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (window.authManager) {
                    window.authManager.logout();
                }
            });
        }

        // Toggle sidebar en móvil
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                document.body.classList.toggle('sidebar-open');
            });
        }

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', () => {
                document.body.classList.remove('sidebar-open');
            });
        }
    }
}

// Función para inicializar el sidebar
function initializeSidebar() {
    console.log('🚀 initializeSidebar() llamado');
    try {
        if (window.sidebarManager) {
            console.log('⚠️ SidebarManager ya existe, reinicializando...');
        }
        window.sidebarManager = new SidebarManager();
        window.sidebarManager.init();
    } catch (error) {
        console.error('❌ Error inicializando sidebar:', error);
        console.error('Stack trace:', error.stack);
    }
}

// Inicializar cuando el DOM esté listo
console.log('⏳ Esperando DOMContentLoaded...');
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ DOMContentLoaded disparado');
    // Esperar un poco para asegurar que todos los scripts estén cargados
    setTimeout(initializeSidebar, 100);
});

// También intentar inicializar inmediatamente si el DOM ya está listo
if (document.readyState === 'loading') {
    console.log('📄 DOM aún cargando, esperando DOMContentLoaded...');
} else {
    console.log('✅ DOM ya está listo, inicializando inmediatamente');
    setTimeout(initializeSidebar, 100);
}

// Verificación agresiva: ejecutar cada 500ms hasta que el sidebar esté correcto
function verificarYCorregirSidebar() {
    const sidebar = document.getElementById('adminSidebar');
    if (!sidebar) {
        console.log('⏳ Esperando elemento #adminSidebar...');
        setTimeout(verificarYCorregirSidebar, 500);
        return;
    }
    
    const html = sidebar.innerHTML;
    console.log('🔍 Verificando sidebar - Longitud HTML:', html.length);
    
    // Si el sidebar está vacío o tiene muy poco contenido, esperar
    if (html.length < 100) {
        console.log('⏳ Sidebar aún vacío, esperando...');
        setTimeout(verificarYCorregirSidebar, 500);
        return;
    }
    
    const tieneReportes = html.includes('Reportes') || (html.includes('fa-chart-bar') && html.includes('reportes.html'));
    const tieneGestionIA = html.includes('GESTIÓN DE NOTICIAS CON IA');
    const tieneGestionMinusculas = html.includes('sidebar-section-title">Gestión') && !html.includes('sidebar-section-title">GESTIÓN');
    const tieneScrapersMinusculas = html.includes('sidebar-section-title">Scrapers') && !html.includes('sidebar-section-title">SCRAPERS');
    
    console.log('🔍 Verificación:');
    console.log('  - Tiene Reportes:', tieneReportes);
    console.log('  - Tiene GESTIÓN DE NOTICIAS CON IA:', tieneGestionIA);
    console.log('  - Tiene "Gestión" en minúsculas:', tieneGestionMinusculas);
    console.log('  - Tiene "Scrapers" en minúsculas:', tieneScrapersMinusculas);
    
    if (tieneReportes || !tieneGestionIA || tieneGestionMinusculas || tieneScrapersMinusculas) {
        console.warn('🚨 VERIFICACIÓN AGRESIVA: Sidebar tiene versión antigua, corrigiendo...');
        
        // Forzar regeneración
        if (window.sidebarManager && typeof window.sidebarManager.generateSidebarHTML === 'function') {
            console.log('✅ Usando sidebarManager existente para regenerar...');
            const newHTML = window.sidebarManager.generateSidebarHTML();
            sidebar.innerHTML = newHTML;
            window.sidebarManager.setupEventListeners();
            console.log('✅ Sidebar corregido por verificación agresiva');
        } else {
            // Si no existe sidebarManager, crearlo
            console.log('⚠️ sidebarManager no existe o no tiene generateSidebarHTML, creándolo...');
            if (typeof initializeSidebar === 'function') {
                initializeSidebar();
            } else {
                // Crear SidebarManager directamente
                console.log('⚠️ initializeSidebar no existe, creando SidebarManager directamente...');
                try {
                    window.sidebarManager = new SidebarManager();
                    window.sidebarManager.init();
                } catch (e) {
                    console.error('❌ Error creando SidebarManager:', e);
                }
            }
        }
    } else {
        console.log('✅ Sidebar está correcto, no necesita corrección');
    }
}

// Iniciar verificación agresiva después de 1 segundo
setTimeout(() => {
    console.log('🔍 Iniciando verificación agresiva del sidebar...');
    verificarYCorregirSidebar();
    // Verificar cada 2 segundos durante los primeros 10 segundos
    let intentos = 0;
    const intervalo = setInterval(() => {
        intentos++;
        verificarYCorregirSidebar();
        if (intentos >= 5) {
            clearInterval(intervalo);
            console.log('✅ Verificación agresiva completada');
        }
    }, 2000);
}, 1000);

// Log al final del script para confirmar que se cargó completamente
console.log('📦 sidebar.js cargado - FIN DEL SCRIPT');
console.log('📦 window.sidebarManager disponible:', typeof window.sidebarManager !== 'undefined');

