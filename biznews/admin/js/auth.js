/**
 * BizNews Admin Authentication
 * Sistema de autenticación para el panel de administración
 */

class AuthManager {
    constructor() {
        this.apiBaseUrl = 'http://127.0.0.1:8000';
        this.sessionKey = 'biznews_admin_session';
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
                credentials: 'include' // Incluir cookies si es necesario
            });

            // Si el token expiró, intentar refrescar
            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Reintentar la petición con el nuevo token
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
            // Mejorar mensajes de error
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                throw new Error(`No se pudo conectar con el servidor. Verifica que el servidor API esté corriendo en ${url.split('/')[0] + '//' + url.split('/')[2]}`);
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
                    'Authorization': `Bearer ${session.refresh_token}`
                }
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();
            
            // Actualizar sesión
            session.access_token = data.access_token;
            session.refresh_token = data.refresh_token;
            session.expiresAt = new Date().getTime() + (data.expires_in * 1000);
            localStorage.setItem(this.sessionKey, JSON.stringify(session));
            
            return true;
        } catch (error) {
            console.error('Error al refrescar token:', error);
            return false;
        }
    }

    // Login
    async login(email, password, rememberMe = false) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                return { 
                    success: false, 
                    message: data.detail || 'Error al iniciar sesión' 
                };
            }

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
                message: 'Error de conexión. Verifica que el servidor esté corriendo.' 
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
            window.location.href = 'login.html';
        }
    }

    // Obtener usuario actual
    getCurrentUser() {
        const session = this.getSession();
        return session ? session.user : null;
    }

    // Verificar y redirigir si no está autenticado
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = 'login.html';
            return false;
        }
        return true;
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

// Inicializar AuthManager
window.authManager = new AuthManager();

// Si estamos en la página de login, manejar el formulario
if (window.location.pathname.includes('login.html')) {
    document.addEventListener('DOMContentLoaded', () => {
        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.getElementById('loginBtn');
        
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const emailInput = document.getElementById('email') || document.getElementById('username');
                const email = emailInput ? emailInput.value.trim() : '';
                const password = document.getElementById('password').value;
                const rememberMe = document.getElementById('rememberMe') ? document.getElementById('rememberMe').checked : false;
                
                // Validar campos
                if (!email || !password) {
                    window.authManager.showAlert('Por favor, completa todos los campos', 'warning');
                    return;
                }
                
                // Validar formato de email
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    window.authManager.showAlert('Por favor, ingresa un email válido', 'warning');
                    return;
                }
                
                // Deshabilitar botón y mostrar loading
                loginBtn.disabled = true;
                loginBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Iniciando sesión...';
                
                // Intentar login
                const result = await window.authManager.login(email, password, rememberMe);
                
                if (result.success) {
                    window.authManager.showAlert('Login exitoso. Redirigiendo...', 'success');
                    setTimeout(() => {
                        window.location.href = 'dashboard.html';
                    }, 1000);
                } else {
                    window.authManager.showAlert(result.message, 'danger');
                    loginBtn.disabled = false;
                    loginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Iniciar Sesión';
                    document.getElementById('password').value = '';
                    document.getElementById('password').focus();
                }
            });
        }
        
        // Si ya está autenticado, redirigir al dashboard
        if (window.authManager.isAuthenticated()) {
            window.location.href = 'dashboard.html';
        }
    });
}

// Si estamos en páginas protegidas, verificar autenticación
if (window.location.pathname.includes('admin/') && 
    !window.location.pathname.includes('login.html')) {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.authManager.requireAuth()) {
            return;
        }
        
        // Mostrar usuario actual en el menú si existe
        const userMenu = document.getElementById('userMenu');
        if (userMenu) {
            const currentUser = window.authManager.getCurrentUser();
            if (currentUser) {
                const userName = currentUser.nombre || currentUser.email || 'Usuario';
                userMenu.innerHTML = `
                    <i class="fas fa-user-circle"></i>
                    ${userName}
                `;
            }
        }
    });
}

