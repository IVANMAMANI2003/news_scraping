/**
 * Subscription CTA Component
 * Componente elegante para invitar a usuarios a suscribirse
 */

class SubscriptionCTA {
    constructor() {
        this.storageKey = 'biznews_cta_dismissed';
        this.dismissedUntil = null;
        this.checkDismissed();
    }

    checkDismissed() {
        try {
            const dismissed = localStorage.getItem(this.storageKey);
            if (dismissed) {
                const dismissedDate = new Date(dismissed);
                const now = new Date();
                // Si fue cerrado hace menos de 7 días, no mostrarlo
                const daysDiff = (now - dismissedDate) / (1000 * 60 * 60 * 24);
                if (daysDiff < 7) {
                    return; // No mostrar si fue cerrado recientemente
                }
            }
        } catch (e) {
            // Ignorar errores de localStorage
        }
        
        // Verificar si el usuario ya está autenticado
        this.checkAuthAndShow();
    }

    async checkAuthAndShow() {
        // Verificar si el usuario está autenticado
        const publicToken = localStorage.getItem('biznews_session');
        const adminToken = localStorage.getItem('biznews_admin_session');
        
        if (publicToken || adminToken) {
            // Usuario autenticado, no mostrar CTA
            return;
        }

        // Verificar si estamos en la página de servicios o login
        const currentPage = window.location.pathname;
        if (currentPage.includes('servicios.html') || currentPage.includes('login.html')) {
            return; // No mostrar en estas páginas
        }

        // Esperar un poco antes de mostrar para mejor UX
        setTimeout(() => {
            this.show();
        }, 2000);
    }

    show() {
        // Crear el elemento si no existe
        if (document.getElementById('subscription-cta')) {
            return;
        }

        const ctaHTML = `
            <div id="subscription-cta" class="subscription-cta">
                <div class="cta-container">
                    <button class="cta-close" id="cta-close" aria-label="Cerrar">
                        <i class="fas fa-times"></i>
                    </button>
                    <div class="cta-content">
                        <div class="cta-icon">
                            <i class="fas fa-rocket"></i>
                        </div>
                        <div class="cta-text">
                            <h4 class="cta-title">Desbloquea Funcionalidades Premium</h4>
                            <p class="cta-description">
                                Accede a <strong>búsqueda avanzada</strong>, <strong>noticias con IA</strong>, 
                                y mucho más. Suscríbete ahora y obtén acceso completo.
                            </p>
                            <div class="cta-features">
                                <span class="feature-badge">
                                    <i class="fas fa-search"></i> Búsqueda Avanzada
                                </span>
                                <span class="feature-badge">
                                    <i class="fas fa-robot"></i> Noticias con IA
                                </span>
                                <span class="feature-badge">
                                    <i class="fas fa-chart-line"></i> Análisis Avanzado
                                </span>
                            </div>
                        </div>
                        <div class="cta-actions">
                            <a href="${this.getServicesPath()}" class="btn-cta-primary">
                                <i class="fas fa-star me-2"></i>
                                Ver Planes
                            </a>
                            <a href="${this.getLoginPath()}" class="btn-cta-secondary">
                                Iniciar Sesión
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Insertar en el body
        document.body.insertAdjacentHTML('beforeend', ctaHTML);

        // Agregar animación de entrada
        setTimeout(() => {
            const cta = document.getElementById('subscription-cta');
            if (cta) {
                cta.classList.add('show');
            }
        }, 100);

        // Configurar event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        const closeBtn = document.getElementById('cta-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.dismiss();
            });
        }

        // Cerrar al hacer clic fuera del contenido
        const cta = document.getElementById('subscription-cta');
        if (cta) {
            cta.addEventListener('click', (e) => {
                if (e.target === cta) {
                    this.dismiss();
                }
            });
        }
    }

    dismiss() {
        const cta = document.getElementById('subscription-cta');
        if (cta) {
            cta.classList.add('hide');
            setTimeout(() => {
                cta.remove();
            }, 300);
        }

        // Guardar en localStorage
        try {
            localStorage.setItem(this.storageKey, new Date().toISOString());
        } catch (e) {
            // Ignorar errores
        }
    }

    getServicesPath() {
        const isInPageFolder = window.location.pathname.includes('/page/');
        return isInPageFolder ? 'servicios.html' : 'page/servicios.html';
    }

    getLoginPath() {
        const isInPageFolder = window.location.pathname.includes('/page/');
        return isInPageFolder ? 'login.html' : 'page/login.html';
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.subscriptionCTA = new SubscriptionCTA();
});

