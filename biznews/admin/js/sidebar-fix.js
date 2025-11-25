/**
 * Sidebar Fix - DESACTIVADO
 * Este script ha sido desactivado. Solo se usa sidebar.js ahora.
 */

(function() {
    'use strict';
    
    // Script desactivado - no hacer nada
    return;
    
    console.log('🔧 sidebar-fix.js cargado');
    
    function generarSidebarCorrecto() {
        console.log('🔧 Generando sidebar correcto...');
        const sidebar = document.getElementById('adminSidebar');
        if (!sidebar) {
            console.log('⏳ Esperando elemento #adminSidebar...');
            setTimeout(generarSidebarCorrecto, 200);
            return;
        }
        
        const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
        const menuItems = [
            {
                section: 'main',
                items: [
                    { href: 'dashboard.html', icon: 'fa-tachometer-alt', text: 'Dashboard', tooltip: 'Dashboard' }
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
            },
            {
                section: 'footer',
                items: [
                    { href: '../index.html', icon: 'fa-home', text: 'Página Pública', tooltip: 'Página Pública' },
                    { href: '#', icon: 'fa-sign-out-alt', text: 'Cerrar Sesión', tooltip: 'Cerrar Sesión', id: 'logoutBtn' }
                ]
            }
        ];
        
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
                const itemHref = item.href.replace('#', '');
                const isActive = itemHref === currentPage ? 'active' : '';
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
        
        sidebar.innerHTML = html;
        console.log('✅ Sidebar regenerado correctamente');
        console.log('🔍 Verificación:');
        console.log('  - Contiene "GESTIÓN DE NOTICIAS CON IA":', html.includes('GESTIÓN DE NOTICIAS CON IA'));
        console.log('  - Contiene "GESTIÓN":', html.includes('GESTIÓN'));
        console.log('  - Contiene "SCRAPERS":', html.includes('SCRAPERS'));
        console.log('  - Contiene "Reportes":', html.includes('Reportes'));
        
        // Configurar event listeners básicos
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (window.authManager) {
                    if (confirm('¿Estás seguro de que deseas cerrar sesión?')) {
                        window.authManager.logout();
                    }
                }
            });
        }
        
        const collapseBtn = document.getElementById('sidebarCollapseBtn');
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => {
                document.body.classList.toggle('sidebar-collapsed');
            });
        }
    }
    
    function verificarYCorregirSidebar() {
        const sidebar = document.getElementById('adminSidebar');
        if (!sidebar) {
            setTimeout(verificarYCorregirSidebar, 200);
            return;
        }
        
        const html = sidebar.innerHTML;
        
        // Si el sidebar está vacío, esperar
        if (html.length < 100) {
            setTimeout(verificarYCorregirSidebar, 200);
            return;
        }
        
        const tieneReportes = html.includes('Reportes') || (html.includes('fa-chart-bar') && html.includes('reportes.html'));
        const tieneGestionIA = html.includes('GESTIÓN DE NOTICIAS CON IA');
        const tieneGestionMinusculas = html.includes('sidebar-section-title">Gestión') && !html.includes('sidebar-section-title">GESTIÓN');
        const tieneScrapersMinusculas = html.includes('sidebar-section-title">Scrapers') && !html.includes('sidebar-section-title">SCRAPERS');
        
        if (tieneReportes || !tieneGestionIA || tieneGestionMinusculas || tieneScrapersMinusculas) {
            console.warn('🚨 DETECTADO: Sidebar tiene versión antigua, corrigiendo...');
            console.warn('  - Tiene Reportes:', tieneReportes);
            console.warn('  - NO tiene GESTIÓN DE NOTICIAS CON IA:', !tieneGestionIA);
            console.warn('  - Tiene "Gestión" en minúsculas:', tieneGestionMinusculas);
            console.warn('  - Tiene "Scrapers" en minúsculas:', tieneScrapersMinusculas);
            generarSidebarCorrecto();
        } else {
            console.log('✅ Sidebar está correcto');
        }
    }
    
    // Iniciar verificación después de que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(verificarYCorregirSidebar, 500);
        });
    } else {
        setTimeout(verificarYCorregirSidebar, 500);
    }
    
    // Verificar también después de un tiempo adicional (por si sidebar.js se carga tarde)
    setTimeout(verificarYCorregirSidebar, 2000);
    setTimeout(verificarYCorregirSidebar, 4000);
})();

