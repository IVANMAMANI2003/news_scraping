/**
 * Gestión de Usuarios - CRUD Completo
 * BizNews Admin
 */

const API_BASE_URL = "http://127.0.0.1:8000";
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;
let deleteUserId = null;
let editingUserId = null;

/**
 * Inicializar página
 */
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    
    // Búsqueda en tiempo real
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadUsers();
            }, 500);
        });
    }
    
    // Filtros
    ['filterRol', 'filterPlan', 'filterActivo'].forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.addEventListener('change', () => {
                currentPage = 1;
                loadUsers();
            });
        }
    });
});

/**
 * Cargar usuarios
 */
async function loadUsers() {
    try {
        const search = document.getElementById('searchInput')?.value || '';
        const rol = document.getElementById('filterRol')?.value || '';
        const plan = document.getElementById('filterPlan')?.value || '';
        const activo = document.getElementById('filterActivo')?.value || '';
        
        const params = new URLSearchParams({
            skip: (currentPage - 1) * pageSize,
            limit: pageSize
        });
        
        if (rol) params.append('rol', rol);
        if (plan) params.append('plan', plan);
        if (activo) params.append('activo', activo === 'true');
        
        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/users?${params.toString()}`
        );
        
        if (!response.ok) {
            throw new Error('Error al cargar usuarios');
        }
        
        const data = await response.json();
        renderUsers(data.items);
        updatePagination(data.total);
        
    } catch (error) {
        console.error('Error cargando usuarios:', error);
        document.getElementById('usersTableBody').innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5 text-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error al cargar usuarios: ${error.message}
                </td>
            </tr>
        `;
    }
}

/**
 * Renderizar usuarios en la tabla
 */
function renderUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5 text-muted">
                    <i class="fas fa-users me-2"></i>
                    No se encontraron usuarios
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>
                <strong>${user.email}</strong>
                ${user.email_verificado ? '<i class="fas fa-check-circle text-success ms-2" title="Email verificado"></i>' : ''}
            </td>
            <td>${user.nombre} ${user.apellido || ''}</td>
            <td>
                <span class="badge badge-rol ${user.rol}">${user.rol}</span>
            </td>
            <td>
                <span class="badge badge-plan ${user.plan}">${user.plan.toUpperCase()}</span>
            </td>
            <td>
                ${user.activo 
                    ? '<span class="badge bg-success">Activo</span>' 
                    : '<span class="badge bg-secondary">Inactivo</span>'}
            </td>
            <td>
                ${user.last_login 
                    ? new Date(user.last_login).toLocaleString('es-ES') 
                    : '<span class="text-muted">Nunca</span>'}
            </td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-sm btn-primary btn-action" onclick="editUser(${user.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger btn-action" onclick="deleteUser(${user.id})" title="Eliminar">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Actualizar paginación
 */
function updatePagination(total) {
    totalPages = Math.ceil(total / pageSize);
    const from = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
    const to = Math.min(currentPage * pageSize, total);
    
    // Actualizar total (los elementos showingFrom y showingTo ya no existen en el nuevo diseño)
    const totalUsersEl = document.getElementById('totalUsers');
    if (totalUsersEl) {
        totalUsersEl.textContent = total;
    }
    
    const pagination = document.getElementById('pagination');
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
    loadUsers();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Abrir modal para nuevo usuario
 */
function openUserModal(userId = null) {
    editingUserId = userId;
    const modal = new bootstrap.Modal(document.getElementById('userModal'));
    const form = document.getElementById('userForm');
    form.reset();
    
    document.getElementById('userModalTitle').textContent = userId ? 'Editar Usuario' : 'Nuevo Usuario';
    document.getElementById('userId').value = userId || '';
    document.getElementById('passwordRequired').style.display = userId ? 'none' : 'inline';
    document.getElementById('passwordHelp').style.display = userId ? 'block' : 'none';
    document.getElementById('userPassword').required = !userId;
    
    if (userId) {
        loadUserData(userId);
    }
    
    modal.show();
}

/**
 * Cargar datos del usuario para editar
 */
async function loadUserData(userId) {
    try {
        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/users/${userId}`
        );
        
        if (!response.ok) {
            throw new Error('Error al cargar usuario');
        }
        
        const user = await response.json();
        
        console.log('📥 Usuario cargado para editar:', user);
        
        document.getElementById('userEmail').value = user.email;
        document.getElementById('userNombre').value = user.nombre;
        document.getElementById('userApellido').value = user.apellido || '';
        document.getElementById('userRol').value = user.rol;
        document.getElementById('userPlan').value = user.plan || 'free';
        document.getElementById('userActivo').checked = user.activo;
        
        console.log('✅ Campos del formulario actualizados. Plan seleccionado:', document.getElementById('userPlan').value);
        
    } catch (error) {
        console.error('Error cargando usuario:', error);
        window.authManager.showAlert('Error al cargar datos del usuario', 'danger');
    }
}

/**
 * Guardar usuario
 */
async function saveUser() {
    const form = document.getElementById('userForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const userId = document.getElementById('userId').value;
    const userData = {
        email: document.getElementById('userEmail').value.trim(),
        nombre: document.getElementById('userNombre').value.trim(),
        apellido: document.getElementById('userApellido').value.trim() || null,
        rol: document.getElementById('userRol').value,
        plan: document.getElementById('userPlan').value,
        activo: document.getElementById('userActivo').checked
    };
    
    const password = document.getElementById('userPassword').value;
    if (password) {
        userData.password = password;
    }
    
    console.log('💾 Guardando usuario:', { userId, userData });
    
    try {
        let response;
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (userId) {
            // Actualizar
            console.log('🔄 Actualizando usuario:', userId, userData);
            response = await window.authManager.authenticatedFetch(
                `${API_BASE_URL}/users/${userId}`,
                {
                    method: 'PUT',
                    headers: headers,
                    body: JSON.stringify(userData)
                }
            );
        } else {
            // Crear
            console.log('➕ Creando nuevo usuario:', userData);
            response = await window.authManager.authenticatedFetch(
                `${API_BASE_URL}/users`,
                {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify(userData)
                }
            );
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar usuario');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
        window.authManager.showAlert(
            userId ? 'Usuario actualizado exitosamente' : 'Usuario creado exitosamente',
            'success'
        );
        loadUsers();
        
    } catch (error) {
        console.error('Error guardando usuario:', error);
        window.authManager.showAlert(error.message || 'Error al guardar usuario', 'danger');
    }
}

/**
 * Eliminar usuario
 */
function deleteUser(userId) {
    deleteUserId = userId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

/**
 * Confirmar eliminación
 */
async function confirmDelete() {
    if (!deleteUserId) return;
    
    try {
        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/users/${deleteUserId}`,
            {
                method: 'DELETE'
            }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar usuario');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
        window.authManager.showAlert('Usuario eliminado exitosamente', 'success');
        loadUsers();
        deleteUserId = null;
        
    } catch (error) {
        console.error('Error eliminando usuario:', error);
        window.authManager.showAlert(error.message || 'Error al eliminar usuario', 'danger');
    }
}

/**
 * Limpiar filtros
 */
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filterRol').value = '';
    document.getElementById('filterPlan').value = '';
    document.getElementById('filterActivo').value = '';
    currentPage = 1;
    loadUsers();
}

// Exponer funciones globalmente
window.clearFilters = clearFilters;
window.editUser = openUserModal;
window.deleteUser = deleteUser;
window.saveUser = saveUser;
window.confirmDelete = confirmDelete;
window.changePage = changePage;

