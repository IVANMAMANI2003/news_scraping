/**
 * BizNews Public Authentication
 * Sistema de autenticación para páginas públicas
 */

class PublicAuthManager {
    constructor() {
        this.apiBaseUrl = 'http://127.0.0.1:8000';
        this.sessionKey = 'biznews_session';
        this.sessionTimeout = 24 * 60 * 60 * 1000; // 24 horas
    }

    // Verificar si el usuario está autenticado
    isAuthenticated() {
        const session = this.getSession();
        if (!session) return false;
        
        // Verificar si la sesión expiró
        const now = new Date().getTime();
        if (now > session.expiresAt) {
            this.logout();
            return false;
        }
        
        return true;
    }

    // Obtener sesión actual
    getSession() {
        try {
            const sessionData = localStorage.getItem(this.sessionKey);
            if (!sessionData) return null;
            return JSON.parse(sessionData);
        } catch (error) {
            console.error('Error obteniendo sesión:', error);
            return null;
        }
    }

    // Obtener token de acceso
    getAccessToken() {
        const session = this.getSession();
        return session ? session.access_token : null;
    }

    // Obtener usuario actual
    getCurrentUser() {
        const session = this.getSession();
        return session ? session.user : null;
    }

    // Login
    async login(email, password, rememberMe = false) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Error de autenticación' }));
                throw new Error(errorData.detail || 'Credenciales inválidas');
            }

            const data = await response.json();

            // Guardar tokens y datos del usuario
            const session = {
                access_token: data.access_token,
                refresh_token: data.refresh_token,
                user: data.user,
                loginTime: new Date().getTime(),
                expiresAt: new Date().getTime() + (data.expires_in * 1000),
                rememberMe: rememberMe
            };

            localStorage.setItem(this.sessionKey, JSON.stringify(session));
            
            return { 
                success: true, 
                message: 'Login exitoso',
                user: data.user
            };
        } catch (error) {
            console.error('Error en login:', error);
            return { 
                success: false, 
                message: error.message || 'Error de conexión. Verifica que el servidor esté corriendo.' 
            };
        }
    }

    // Logout
    async logout() {
        try {
            // Intentar cerrar sesión en el servidor
            const token = this.getAccessToken();
            if (token) {
                await fetch(`${this.apiBaseUrl}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }).catch(() => {
                    // Ignorar errores si el servidor no responde
                });
            }
        } catch (error) {
            console.error('Error en logout:', error);
        } finally {
            localStorage.removeItem(this.sessionKey);
        }
    }

    // Hacer request autenticado
    async authenticatedFetch(url, options = {}) {
        const token = this.getAccessToken();
        if (!token) {
            throw new Error('No hay token de acceso. Por favor, inicia sesión.');
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include'
            });

            // Si el token expiró, intentar refrescar
            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
                    return fetch(url, {
                        ...options,
                        headers,
                        credentials: 'include'
                    });
                } else {
                    this.logout();
                    throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
                }
            }

            return response;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                throw new Error(`No se pudo conectar con el servidor. Verifica que el servidor API esté corriendo.`);
            }
            throw error;
        }
    }

    // Refrescar token
    async refreshToken() {
        const session = this.getSession();
        if (!session || !session.refresh_token) {
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: session.refresh_token
                })
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();
            
            // Actualizar sesión
            session.access_token = data.access_token;
            session.expiresAt = new Date().getTime() + (data.expires_in * 1000);
            localStorage.setItem(this.sessionKey, JSON.stringify(session));
            
            return true;
        } catch (error) {
            console.error('Error refrescando token:', error);
            return false;
        }
    }

    // Mostrar alerta
    showAlert(message, type = 'danger') {
        const alertContainer = document.getElementById('alertContainer');
        if (!alertContainer) return;

        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${type === 'danger' ? 'exclamation-circle' : 'check-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        alertContainer.innerHTML = alertHTML;
        
        // Auto-dismiss después de 5 segundos
        setTimeout(() => {
            const alert = alertContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Inicializar PublicAuthManager
window.publicAuthManager = new PublicAuthManager();

// Si estamos en la página de login, manejar el formulario
if (window.location.pathname.includes('login.html')) {
    document.addEventListener('DOMContentLoaded', () => {
        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.getElementById('loginBtn');
        const postLoginOptions = document.getElementById('postLoginOptions');
        const optionDashboard = document.getElementById('optionDashboard');
        const optionPublic = document.getElementById('optionPublic');
        
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const rememberMe = document.getElementById('rememberMe').checked;
                
                // Deshabilitar botón y mostrar loading
                loginBtn.disabled = true;
                const originalHTML = loginBtn.innerHTML;
                loginBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Iniciando sesión...';
                
                try {
                    const result = await window.publicAuthManager.login(email, password, rememberMe);
                    
                    if (result.success) {
                        window.publicAuthManager.showAlert('¡Login exitoso!', 'success');
                        
                        // Ocultar formulario y mostrar opciones
                        loginForm.style.display = 'none';
                        postLoginOptions.classList.add('show');
                        
                        // Configurar opciones
                        const user = result.user;
                        const userRole = (user.rol || 'user').toLowerCase();
                        
                        // Si es admin, siempre mostrar opción de dashboard
                        if (userRole === 'admin') {
                            optionDashboard.onclick = () => {
                                // Obtener la sesión actual de publicAuthManager
                                const publicSession = window.publicAuthManager.getSession();
                                if (publicSession) {
                                    // Guardar también en authManager para admin con los datos correctos
                                    const adminSession = {
                                        access_token: publicSession.access_token,
                                        refresh_token: publicSession.refresh_token,
                                        user: publicSession.user,
                                        loginTime: publicSession.loginTime,
                                        expiresAt: publicSession.expiresAt,
                                        rememberMe: publicSession.rememberMe
                                    };
                                    localStorage.setItem('biznews_admin_session', JSON.stringify(adminSession));
                                }
                                window.location.href = '../admin/dashboard.html';
                            };
                            optionPublic.onclick = () => {
                                window.location.href = '../index.html';
                            };
                        } else {
                            // Para usuarios normales, solo opción de página pública
                            optionDashboard.style.display = 'none';
                            optionPublic.onclick = () => {
                                window.location.href = '../index.html';
                            };
                        }
                    } else {
                        window.publicAuthManager.showAlert(result.message, 'danger');
                        loginBtn.disabled = false;
                        loginBtn.innerHTML = originalHTML;
                    }
                } catch (error) {
                    window.publicAuthManager.showAlert('Error de conexión. Verifica que el servidor esté corriendo.', 'danger');
                    loginBtn.disabled = false;
                    loginBtn.innerHTML = originalHTML;
                }
            });
        }
    });
}

