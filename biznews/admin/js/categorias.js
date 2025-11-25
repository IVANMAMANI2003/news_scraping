/**
 * Gestión de Categorías - CRUD Completo
 * BizNews Admin
 */

const API_BASE_URL = "http://127.0.0.1:8000";
let deleteCategoryName = null;

/**
 * Inicializar página
 */
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
});

/**
 * Cargar categorías
 */
async function loadCategories() {
    const categoriesList = document.getElementById('categoriesList');
    if (!categoriesList) return;
    
    categoriesList.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/categories`);
        if (!response.ok) throw new Error('Error al cargar categorías');
        
        const categories = await response.json();
        
        if (categories.length === 0) {
            categoriesList.innerHTML = '<div class="text-center text-muted">No hay categorías registradas</div>';
            return;
        }
        
        categoriesList.innerHTML = categories.map(category => `
            <div class="category-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h5 class="mb-2">
                            <i class="fas fa-tag text-primary me-2"></i>
                            ${escapeHtml(category.nombre)}
                        </h5>
                        <p class="text-muted mb-0">
                            <i class="fas fa-newspaper me-2"></i>
                            ${category.total_noticias} noticia(s)
                        </p>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-primary" onclick="editCategory('${escapeHtml(category.nombre)}')" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteCategory('${escapeHtml(category.nombre)}')" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error cargando categorías:', error);
        categoriesList.innerHTML = '<div class="text-center text-danger">Error al cargar las categorías</div>';
        showNotification('Error al cargar las categorías', 'error');
    }
}

/**
 * Abrir modal para crear categoría
 */
function openCreateModal() {
    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    document.getElementById('modalTitle').textContent = 'Nueva Categoría';
    document.getElementById('categoryForm').reset();
    document.getElementById('categoryOldName').value = '';
    modal.show();
}

/**
 * Editar categoría
 */
function editCategory(nombre) {
    document.getElementById('categoryOldName').value = nombre;
    document.getElementById('categoryNombre').value = nombre;
    document.getElementById('categoryDescripcion').value = '';
    document.getElementById('modalTitle').textContent = 'Editar Categoría';
    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    modal.show();
}

/**
 * Guardar categoría
 */
async function saveCategory() {
    const form = document.getElementById('categoryForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const oldName = document.getElementById('categoryOldName').value;
    const isEdit = !!oldName;
    const nombre = document.getElementById('categoryNombre').value.trim();
    
    if (!nombre) {
        showNotification('El nombre de la categoría es requerido', 'error');
        return;
    }
    
    try {
        let response;
        if (isEdit) {
            // Actualizar
            const updateData = {
                nombre: nombre
            };
            
            const descripcion = document.getElementById('categoryDescripcion').value.trim();
            if (descripcion) updateData.descripcion = descripcion;
            
            response = await fetch(`${API_BASE_URL}/api/admin/categories/${encodeURIComponent(oldName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });
        } else {
            // Crear
            const createData = {
                nombre: nombre
            };
            
            const descripcion = document.getElementById('categoryDescripcion').value.trim();
            if (descripcion) createData.descripcion = descripcion;
            
            response = await fetch(`${API_BASE_URL}/api/admin/categories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(createData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar categoría');
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('categoryModal'));
        modal.hide();
        
        showNotification(isEdit ? 'Categoría actualizada exitosamente' : 'Categoría creada exitosamente', 'success');
        loadCategories();
        
    } catch (error) {
        console.error('Error guardando categoría:', error);
        showNotification(error.message || 'Error al guardar la categoría', 'error');
    }
}

/**
 * Eliminar categoría
 */
function deleteCategory(nombre) {
    deleteCategoryName = nombre;
    document.getElementById('deleteCategoryName').textContent = nombre;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

/**
 * Confirmar eliminación
 */
async function confirmDelete() {
    if (!deleteCategoryName) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/categories/${encodeURIComponent(deleteCategoryName)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar categoría');
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        modal.hide();
        
        showNotification('Categoría eliminada exitosamente', 'success');
        loadCategories();
        deleteCategoryName = null;
        
    } catch (error) {
        console.error('Error eliminando categoría:', error);
        showNotification(error.message || 'Error al eliminar la categoría', 'error');
    }
}

/**
 * Utilidades
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    const toast = document.getElementById('notificationToast');
    const toastMessage = document.getElementById('toastMessage');
    if (toast && toastMessage) {
        toastMessage.textContent = message;
        const toastInstance = new bootstrap.Toast(toast);
        toastInstance.show();
    }
}

// Hacer funciones disponibles globalmente
window.loadCategories = loadCategories;
window.openCreateModal = openCreateModal;
window.editCategory = editCategory;
window.saveCategory = saveCategory;
window.deleteCategory = deleteCategory;
window.confirmDelete = confirmDelete;

