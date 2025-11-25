/**
 * Gestión de API Keys - CRUD Completo
 * BizNews Admin
 */

const API_BASE_URL = "http://127.0.0.1:8000";
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;
let deleteKeyId = null;
let editingKeyId = null;
let usersCache = {};

/**
 * Inicializar página
 */
document.addEventListener('DOMContentLoaded', () => {
    loadUsersCache();
    loadAPIKeys();
    
    // Búsqueda en tiempo real
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadAPIKeys();
            }, 500);
        });
    }
    
    // Filtros
    ['filterPlan', 'filterActivo', 'filterUsuario'].forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.addEventListener('change', () => {
                currentPage = 1;
                loadAPIKeys();
            });
        }
    });
    
    // Actualizar límites cuando cambia el plan
    const planSelect = document.getElementById('apiKeyPlan');
    if (planSelect) {
        planSelect.addEventListener('change', updatePlanLimits);
    }
});

/**
 * Cargar cache de usuarios
 */
async function loadUsersCache() {
    try {
        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/users?limit=1000`
        );
        
        if (response.ok) {
            const data = await response.json();
            data.items.forEach(user => {
                usersCache[user.id] = user;
            });
        }
    } catch (error) {
        console.error('Error cargando usuarios:', error);
    }
}

/**
 * Cargar API keys
 */
async function loadAPIKeys() {
    try {
        // Verificar autenticación
        if (!window.authManager || !window.authManager.isAuthenticated()) {
            console.error('Usuario no autenticado');
            window.location.href = 'login.html';
            return;
        }

        const search = document.getElementById('searchInput')?.value || '';
        const plan = document.getElementById('filterPlan')?.value || '';
        const activo = document.getElementById('filterActivo')?.value || '';
        const usuarioId = document.getElementById('filterUsuario')?.value || '';
        
        const params = new URLSearchParams({
            skip: (currentPage - 1) * pageSize,
            limit: pageSize
        });
        
        if (plan) params.append('plan', plan);
        if (activo) params.append('activo', activo === 'true');
        if (usuarioId) params.append('usuario_id', usuarioId);
        
        const url = `${API_BASE_URL}/api-keys?${params.toString()}`;
        console.log('Cargando API keys desde:', url);
        
        const response = await window.authManager.authenticatedFetch(url);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error en respuesta:', response.status, errorText);
            throw new Error(`Error al cargar API keys: ${response.status} ${errorText}`);
        }
        
        const data = await response.json();
        
        // Filtrar por búsqueda si existe
        let filteredItems = data.items;
        if (search) {
            const searchLower = search.toLowerCase();
            filteredItems = data.items.filter(key => 
                key.nombre.toLowerCase().includes(searchLower) ||
                key.key.toLowerCase().includes(searchLower)
            );
        }
        
        renderAPIKeys(filteredItems);
        updatePagination(data.total); // Usar el total real de la respuesta, no el filtrado
        
    } catch (error) {
        console.error('Error cargando API keys:', error);
        const errorMessage = error.message || 'Error desconocido';
        const tableBody = document.getElementById('apiKeysTableBody');
        if (tableBody) {
            tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-5">
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        <strong>Error al cargar API keys:</strong><br>
                        ${errorMessage}
                        <br><br>
                        <small class="text-muted">
                            Verifica que:<br>
                            • El servidor API esté corriendo en ${API_BASE_URL}<br>
                            • Estés autenticado correctamente<br>
                            • No haya problemas de CORS
                        </small>
                    </div>
                </td>
            </tr>
        `;
        }
    }
}

/**
 * Renderizar API keys en la tabla
 */
function renderAPIKeys(keys) {
    const tbody = document.getElementById('apiKeysTableBody');
    
    if (!keys || keys.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-5 text-muted">
                    <i class="fas fa-key me-2"></i>
                    No se encontraron API keys
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = keys.map(key => {
        const user = usersCache[key.usuario_id];
        const userName = user ? `${user.nombre} (${user.email})` : `Usuario #${key.usuario_id}`;
        const usagePercent = key.limite_diario > 0 
            ? (key.requests_today / key.limite_diario * 100) 
            : 0;
        const usageClass = usagePercent >= 90 ? 'danger' : usagePercent >= 70 ? 'warning' : '';
        
        return `
            <tr>
                <td>${key.id}</td>
                <td><strong>${key.nombre}</strong></td>
                <td>
                    <div class="api-key-value">
                        ${key.key.substring(0, 20)}...
                        <button class="btn btn-sm btn-link p-0 ms-2" onclick="copyToClipboard('${key.key}')" title="Copiar">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </td>
                <td>${userName}</td>
                <td>
                    <span class="badge badge-plan ${key.plan}">${key.plan.toUpperCase()}</span>
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="flex-grow-1">
                            <div class="usage-bar">
                                <div class="usage-fill ${usageClass}" style="width: ${Math.min(usagePercent, 100)}%"></div>
                            </div>
                        </div>
                        <small class="text-muted">${key.requests_today}/${key.limite_diario}</small>
                    </div>
                </td>
                <td>
                    ${key.activo 
                        ? '<span class="badge bg-success">Activa</span>' 
                        : '<span class="badge bg-secondary">Inactiva</span>'}
                </td>
                <td>
                    ${key.last_used 
                        ? new Date(key.last_used).toLocaleString('es-ES') 
                        : '<span class="text-muted">Nunca</span>'}
                </td>
                <td>
                    <div class="table-actions">
                        <button class="btn btn-sm btn-info btn-action" onclick="viewStats(${key.id})" title="Estadísticas">
                            <i class="fas fa-chart-bar"></i>
                        </button>
                        <button class="btn btn-sm btn-primary btn-action" onclick="editAPIKey(${key.id})" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger btn-action" onclick="deleteAPIKey(${key.id})" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Copiar al portapapeles
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        window.authManager.showAlert('API key copiada al portapapeles', 'success');
    }).catch(err => {
        console.error('Error copiando:', err);
    });
}

/**
 * Actualizar paginación
 */
function updatePagination(total) {
    totalPages = Math.ceil(total / pageSize);
    const from = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
    const to = Math.min(currentPage * pageSize, total);
    
    // Actualizar total (los elementos showingFrom y showingTo ya no existen en el nuevo diseño)
    const totalAPIKeysEl = document.getElementById('totalAPIKeys');
    if (totalAPIKeysEl) {
        totalAPIKeysEl.textContent = total;
    }
    
    const pagination = document.getElementById('pagination');
    if (!pagination) {
        console.warn('Elemento pagination no encontrado');
        return;
    }
    
    pagination.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // Botón anterior
    pagination.innerHTML += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Páginas
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            pagination.innerHTML += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            pagination.innerHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Botón siguiente
    pagination.innerHTML += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
}

/**
 * Cambiar página
 */
function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadAPIKeys();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Actualizar límites según el plan
 */
function updatePlanLimits() {
    const plan = document.getElementById('apiKeyPlan').value;
    const limits = {
        free: { limite: 50, sources: 1, historial: 0 },
        pro: { limite: 2000, sources: 5, historial: 7 },
        business: { limite: 20000, sources: 999, historial: 365 },
        enterprise: { limite: 999999, sources: 999, historial: 9999 }
    };
    
    const limit = limits[plan] || limits.free;
    document.getElementById('apiKeyLimiteDiario').value = limit.limite;
    document.getElementById('apiKeyMaxSources').value = limit.sources;
    document.getElementById('apiKeyHistorialDias').value = limit.historial;
}

/**
 * Abrir modal para nueva API key
 */
function openAPIKeyModal(keyId = null) {
    editingKeyId = keyId;
    const modal = new bootstrap.Modal(document.getElementById('apiKeyModal'));
    const form = document.getElementById('apiKeyForm');
    form.reset();
    
    document.getElementById('apiKeyModalTitle').textContent = keyId ? 'Editar API Key' : 'Nueva API Key';
    document.getElementById('apiKeyId').value = keyId || '';
    
    updatePlanLimits();
    
    if (keyId) {
        loadAPIKeyData(keyId);
    }
    
    modal.show();
}

/**
 * Cargar datos de la API key para editar
 */
async function loadAPIKeyData(keyId) {
    try {
        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/api-keys/${keyId}`
        );
        
        if (!response.ok) {
            throw new Error('Error al cargar API key');
        }
        
        const key = await response.json();
        
        document.getElementById('apiKeyUsuarioId').value = key.usuario_id;
        document.getElementById('apiKeyNombre').value = key.nombre;
        document.getElementById('apiKeyPlan').value = key.plan;
        document.getElementById('apiKeyLimiteDiario').value = key.limite_diario;
        document.getElementById('apiKeyFuentePermitida').value = key.fuente_permitida || '';
        document.getElementById('apiKeyMaxSources').value = key.max_sources;
        document.getElementById('apiKeyHistorialDias').value = key.historial_dias;
        document.getElementById('apiKeyWebhookUrl').value = key.webhook_url || '';
        document.getElementById('apiKeyActivo').checked = key.activo;
        
        updatePlanLimits();
        
    } catch (error) {
        console.error('Error cargando API key:', error);
        window.authManager.showAlert('Error al cargar datos de la API key', 'danger');
    }
}

/**
 * Guardar API key
 */
async function saveAPIKey() {
    const form = document.getElementById('apiKeyForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const keyId = document.getElementById('apiKeyId').value;
    const keyData = {
        usuario_id: parseInt(document.getElementById('apiKeyUsuarioId').value),
        nombre: document.getElementById('apiKeyNombre').value.trim(),
        plan: document.getElementById('apiKeyPlan').value,
        limite_diario: parseInt(document.getElementById('apiKeyLimiteDiario').value) || null,
        fuente_permitida: document.getElementById('apiKeyFuentePermitida').value.trim() || null,
        max_sources: parseInt(document.getElementById('apiKeyMaxSources').value) || null,
        historial_dias: parseInt(document.getElementById('apiKeyHistorialDias').value) || null,
        webhook_url: document.getElementById('apiKeyWebhookUrl').value.trim() || null,
        activo: document.getElementById('apiKeyActivo').checked
    };
    
    try {
        let response;
        if (keyId) {
            // Actualizar
            response = await window.authManager.authenticatedFetch(
                `${API_BASE_URL}/api-keys/${keyId}`,
                {
                    method: 'PUT',
                    body: JSON.stringify(keyData)
                }
            );
        } else {
            // Crear
            response = await window.authManager.authenticatedFetch(
                `${API_BASE_URL}/api-keys`,
                {
                    method: 'POST',
                    body: JSON.stringify(keyData)
                }
            );
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar API key');
        }
        
        const savedKey = await response.json();
        
        bootstrap.Modal.getInstance(document.getElementById('apiKeyModal')).hide();
        window.authManager.showAlert(
            keyId ? 'API key actualizada exitosamente' : 'API key creada exitosamente',
            'success'
        );
        
        // Si es nueva, mostrar la key completa
        if (!keyId) {
            alert(`API Key creada:\n\n${savedKey.key}\n\n¡Guarda esta key de forma segura!`);
        }
        
        loadAPIKeys();
        
    } catch (error) {
        console.error('Error guardando API key:', error);
        window.authManager.showAlert(error.message || 'Error al guardar API key', 'danger');
    }
}

/**
 * Ver estadísticas
 */
async function viewStats(keyId) {
    try {
        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/api-keys/${keyId}/stats`
        );
        
        if (!response.ok) {
            throw new Error('Error al cargar estadísticas');
        }
        
        const stats = await response.json();
        const usagePercent = stats.porcentaje_uso;
        const usageClass = usagePercent >= 90 ? 'danger' : usagePercent >= 70 ? 'warning' : '';
        
        document.getElementById('statsModalBody').innerHTML = `
            <div class="row g-3">
                <div class="col-6">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="text-muted mb-2">Requests Hoy</h6>
                            <h3 class="mb-0">${stats.requests_today}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="text-muted mb-2">Límite Diario</h6>
                            <h3 class="mb-0">${stats.limite_diario}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-12">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="text-muted mb-2">Requests Totales</h6>
                            <h3 class="mb-0">${stats.requests_total.toLocaleString()}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-12">
                    <h6 class="mb-2">Uso Diario</h6>
                    <div class="usage-bar mb-2">
                        <div class="usage-fill ${usageClass}" style="width: ${Math.min(usagePercent, 100)}%"></div>
                    </div>
                    <div class="d-flex justify-content-between">
                        <small class="text-muted">${usagePercent.toFixed(1)}% usado</small>
                        <small class="text-muted">${stats.limite_diario - stats.requests_today} restantes</small>
                    </div>
                </div>
                ${stats.last_used ? `
                    <div class="col-12">
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>
                            Último uso: ${new Date(stats.last_used).toLocaleString('es-ES')}
                        </small>
                    </div>
                ` : ''}
            </div>
        `;
        
        const modal = new bootstrap.Modal(document.getElementById('statsModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
        window.authManager.showAlert('Error al cargar estadísticas', 'danger');
    }
}

/**
 * Editar API key
 */
function editAPIKey(keyId) {
    openAPIKeyModal(keyId);
}

/**
 * Eliminar API key
 */
function deleteAPIKey(keyId) {
    deleteKeyId = keyId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

/**
 * Confirmar eliminación
 */
async function confirmDelete() {
    if (!deleteKeyId) return;
    
    try {
        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/api-keys/${deleteKeyId}`,
            {
                method: 'DELETE'
            }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar API key');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
        window.authManager.showAlert('API key eliminada exitosamente', 'success');
        loadAPIKeys();
        deleteKeyId = null;
        
    } catch (error) {
        console.error('Error eliminando API key:', error);
        window.authManager.showAlert(error.message || 'Error al eliminar API key', 'danger');
    }
}

/**
 * Limpiar filtros
 */
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filterPlan').value = '';
    document.getElementById('filterActivo').value = '';
    document.getElementById('filterUsuario').value = '';
    currentPage = 1;
    loadAPIKeys();
}

// Exponer funciones globalmente
window.clearFilters = clearFilters;

