/**
 * Gestión de Fuentes - CRUD Completo
 * BizNews Admin
 */

const API_BASE_URL = "http://127.0.0.1:8000";
let deleteSourceName = null;

/**
 * Inicializar página
 */
document.addEventListener('DOMContentLoaded', () => {
    loadSources();
});

/**
 * Cargar fuentes
 */
async function loadSources() {
    const sourcesList = document.getElementById('sourcesList');
    if (!sourcesList) return;
    
    sourcesList.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/sources`);
        if (!response.ok) throw new Error('Error al cargar fuentes');
        
        const sources = await response.json();
        
        if (sources.length === 0) {
            sourcesList.innerHTML = '<div class="text-center text-muted">No hay fuentes registradas</div>';
            return;
        }
        
        sourcesList.innerHTML = sources.map(source => `
            <div class="source-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h5 class="mb-2">
                            <i class="fas fa-rss text-primary me-2"></i>
                            ${escapeHtml(source.nombre)}
                        </h5>
                        <p class="text-muted mb-0">
                            <i class="fas fa-newspaper me-2"></i>
                            ${source.total_noticias} noticia(s)
                        </p>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-primary" onclick="editSource('${escapeHtml(source.nombre)}')" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteSource('${escapeHtml(source.nombre)}')" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error cargando fuentes:', error);
        sourcesList.innerHTML = '<div class="text-center text-danger">Error al cargar las fuentes</div>';
        showNotification('Error al cargar las fuentes', 'error');
    }
}

/**
 * Abrir modal para crear fuente
 */
function openCreateModal() {
    const modal = new bootstrap.Modal(document.getElementById('sourceModal'));
    document.getElementById('modalTitle').textContent = 'Nueva Fuente';
    document.getElementById('sourceForm').reset();
    document.getElementById('sourceOldName').value = '';
    modal.show();
}

/**
 * Editar fuente
 */
function editSource(nombre) {
    document.getElementById('sourceOldName').value = nombre;
    document.getElementById('sourceNombre').value = nombre;
    document.getElementById('sourceDescripcion').value = '';
    document.getElementById('sourceUrlBase').value = '';
    document.getElementById('modalTitle').textContent = 'Editar Fuente';
    const modal = new bootstrap.Modal(document.getElementById('sourceModal'));
    modal.show();
}

/**
 * Guardar fuente
 */
async function saveSource() {
    const form = document.getElementById('sourceForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const oldName = document.getElementById('sourceOldName').value;
    const isEdit = !!oldName;
    const nombre = document.getElementById('sourceNombre').value.trim();
    
    if (!nombre) {
        showNotification('El nombre de la fuente es requerido', 'error');
        return;
    }
    
    try {
        let response;
        if (isEdit) {
            // Actualizar
            const updateData = {
                nombre: nombre
            };
            
            const descripcion = document.getElementById('sourceDescripcion').value.trim();
            if (descripcion) updateData.descripcion = descripcion;
            
            const urlBase = document.getElementById('sourceUrlBase').value.trim();
            if (urlBase) updateData.url_base = urlBase;
            
            response = await fetch(`${API_BASE_URL}/api/admin/sources/${encodeURIComponent(oldName)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });
        } else {
            // Crear
            const createData = {
                nombre: nombre
            };
            
            const descripcion = document.getElementById('sourceDescripcion').value.trim();
            if (descripcion) createData.descripcion = descripcion;
            
            const urlBase = document.getElementById('sourceUrlBase').value.trim();
            if (urlBase) createData.url_base = urlBase;
            
            response = await fetch(`${API_BASE_URL}/api/admin/sources`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(createData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar fuente');
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('sourceModal'));
        modal.hide();
        
        showNotification(isEdit ? 'Fuente actualizada exitosamente' : 'Fuente creada exitosamente', 'success');
        loadSources();
        
    } catch (error) {
        console.error('Error guardando fuente:', error);
        showNotification(error.message || 'Error al guardar la fuente', 'error');
    }
}

/**
 * Eliminar fuente
 */
function deleteSource(nombre) {
    deleteSourceName = nombre;
    document.getElementById('deleteSourceName').textContent = nombre;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

/**
 * Confirmar eliminación
 */
async function confirmDelete() {
    if (!deleteSourceName) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/sources/${encodeURIComponent(deleteSourceName)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar fuente');
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        modal.hide();
        
        showNotification('Fuente eliminada exitosamente', 'success');
        loadSources();
        deleteSourceName = null;
        
    } catch (error) {
        console.error('Error eliminando fuente:', error);
        showNotification(error.message || 'Error al eliminar la fuente', 'error');
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
window.loadSources = loadSources;
window.openCreateModal = openCreateModal;
window.editSource = editSource;
window.saveSource = saveSource;
window.deleteSource = deleteSource;
window.confirmDelete = confirmDelete;

