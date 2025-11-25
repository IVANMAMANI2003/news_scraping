/**
 * Gestión de Noticias - CRUD Completo
 * BizNews Admin
 */

const API_BASE_URL = "http://127.0.0.1:8000";
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;
let deleteNewsId = null;

// Formatos disponibles por plan
const EXPORT_FORMATS = {
    "admin": ["json", "csv", "xml", "parquet"], // Admin tiene acceso a todo
    "free": ["json"],
    "pro": ["json", "csv"],
    "business": ["json", "csv", "xml"],
    "enterprise": ["json", "csv", "xml", "parquet"]
};

// Iconos y colores por formato
const FORMAT_INFO = {
    "json": { icon: "fa-file-code", color: "success", label: "JSON" },
    "csv": { icon: "fa-file-csv", color: "info", label: "CSV" },
    "xml": { icon: "fa-file-code", color: "warning", label: "XML" },
    "parquet": { icon: "fa-file-archive", color: "danger", label: "Parquet" }
};

/**
 * Inicializar página
 */
document.addEventListener('DOMContentLoaded', () => {
    loadSources();
    loadCategories();
    loadNews();
    
    // Cargar botones de exportación - intentar varias veces si es necesario
    function tryLoadExportButtons(attempts = 0) {
        if (attempts > 10) {
            console.error('No se pudo cargar los botones de exportación después de varios intentos');
            const container = document.getElementById('exportButtons');
            if (container) {
                container.innerHTML = '<span class="text-danger">Error: No se pudo cargar los formatos de exportación</span>';
            }
            return;
        }
        
        if (window.authManager) {
            loadExportButtons();
        } else {
            setTimeout(() => tryLoadExportButtons(attempts + 1), 200);
        }
    }
    
    tryLoadExportButtons();
    
    // Búsqueda en tiempo real
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadNews();
            }, 500);
        });
    }
    
    // Enter en búsqueda
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                currentPage = 1;
                loadNews();
            }
        });
    }
});

/**
 * Cargar fuentes para filtro y datalist
 */
async function loadSources() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/sources`);
        if (response.ok) {
            const sources = await response.json();
            const filterSource = document.getElementById('filterSource');
            const sourcesList = document.getElementById('sourcesList');
            
            if (filterSource) {
                sources.forEach(source => {
                    const option = document.createElement('option');
                    option.value = source.nombre;
                    option.textContent = `${source.nombre} (${source.total_noticias})`;
                    filterSource.appendChild(option);
                });
            }
            
            if (sourcesList) {
                sources.forEach(source => {
                    const option = document.createElement('option');
                    option.value = source.nombre;
                    sourcesList.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error cargando fuentes:', error);
    }
}

/**
 * Cargar categorías para filtro y datalist
 */
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/categories`);
        if (response.ok) {
            const categories = await response.json();
            const filterCategory = document.getElementById('filterCategory');
            const categoriesList = document.getElementById('categoriesList');
            
            if (filterCategory) {
                categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.nombre;
                    option.textContent = `${category.nombre} (${category.total_noticias})`;
                    filterCategory.appendChild(option);
                });
            }
            
            if (categoriesList) {
                categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.nombre;
                    categoriesList.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error cargando categorías:', error);
    }
}

/**
 * Cargar noticias
 */
async function loadNews() {
    const tbody = document.getElementById('newsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="7" class="text-center"><div class="spinner-border text-primary"></div></td></tr>';
    
    try {
        // Construir parámetros de búsqueda
        const params = new URLSearchParams();
        params.append('skip', (currentPage - 1) * pageSize);
        params.append('limit', pageSize);
        params.append('order', 'desc');
        
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput.value.trim()) {
            params.append('q', searchInput.value.trim());
        }
        
        const filterSource = document.getElementById('filterSource');
        if (filterSource && filterSource.value) {
            params.append('fuente', filterSource.value);
        }
        
        const filterCategory = document.getElementById('filterCategory');
        if (filterCategory && filterCategory.value) {
            params.append('categoria', filterCategory.value);
        }
        
        const filterDateFrom = document.getElementById('filterDateFrom');
        if (filterDateFrom && filterDateFrom.value) {
            params.append('date_from', filterDateFrom.value);
        }
        
        const filterDateTo = document.getElementById('filterDateTo');
        if (filterDateTo && filterDateTo.value) {
            params.append('date_to', filterDateTo.value);
        }
        
        const response = await fetch(`${API_BASE_URL}/news?${params.toString()}`);
        if (!response.ok) throw new Error('Error al cargar noticias');
        
        const data = await response.json();
        const news = data.items || [];
        const total = data.total || 0;
        
        // Actualizar contador
        const totalCount = document.getElementById('totalCount');
        if (totalCount) totalCount.textContent = total;
        
        // Calcular páginas
        totalPages = Math.ceil(total / pageSize);
        renderPagination();
        
        // Renderizar tabla
        if (news.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No se encontraron noticias</td></tr>';
            return;
        }
        
        tbody.innerHTML = news.map(article => {
            const hasImage = article.imagen_principal || article.imagenes;
            const imageUrl = article.imagen_principal || article.imagenes || '';
            return `
            <tr>
                <td>${article.id || '-'}</td>
                <td>
                    <div style="max-width: 300px;">
                        <strong>${truncateText(article.titulo || 'Sin título', 60)}</strong>
                    </div>
                </td>
                <td>${article.fuente || '-'}</td>
                <td>${article.categoria || '-'}</td>
                <td>${article.fecha ? new Date(article.fecha).toLocaleDateString('es-ES') : '-'}</td>
                <td>
                    ${hasImage ? `
                        <img src="${imageUrl}" alt="Imagen" 
                             style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px; cursor: pointer;"
                             onclick="showImageModal('${escapeHtml(imageUrl)}')"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';"
                             title="Click para ver imagen">
                        <span style="display: none; color: #dc3545;">
                            <i class="fas fa-exclamation-triangle" title="Imagen no disponible"></i>
                        </span>
                    ` : `
                        <span class="text-muted" title="Sin imagen">
                            <i class="fas fa-image"></i>
                            <small>Sin imagen</small>
                        </span>
                    `}
                </td>
                <td>
                    <a href="${article.url || '#'}" target="_blank" class="text-decoration-none" title="${article.url || ''}">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </td>
                <td>
                    <div class="table-actions">
                        <button class="btn btn-sm btn-primary btn-action" onclick="editNews(${article.id})" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger btn-action" onclick="deleteNews(${article.id}, '${escapeHtml(article.titulo || '')}')" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        }).join('');
        
    } catch (error) {
        console.error('Error cargando noticias:', error);
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Error al cargar las noticias</td></tr>';
        showNotification('Error al cargar las noticias', 'error');
    }
}

/**
 * Renderizar paginación
 */
function renderPagination() {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Números de página
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1); return false;">1</a></li>`;
        if (startPage > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages}); return false;">${totalPages}</a></li>`;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

/**
 * Cambiar página
 */
function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadNews();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Limpiar filtros
 */
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filterSource').value = '';
    document.getElementById('filterCategory').value = '';
    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value = '';
    currentPage = 1;
    loadNews();
}

/**
 * Cargar botones de exportación según el plan del usuario
 */
async function loadExportButtons() {
    const exportButtonsContainer = document.getElementById('exportButtons');
    if (!exportButtonsContainer) {
        console.warn('Contenedor de botones de exportación no encontrado');
        return;
    }
    
    try {
        // Esperar a que authManager esté disponible
        if (!window.authManager) {
            console.log('Esperando authManager...');
            setTimeout(loadExportButtons, 200);
            return;
        }
        
        // Obtener información del usuario actual desde la sesión
        let userPlan = 'free';
        let userRole = 'user';
        
        const currentUser = window.authManager.getCurrentUser();
        console.log('Usuario actual desde sesión:', currentUser);
        
        if (currentUser) {
            userPlan = (currentUser.plan || 'free').toLowerCase();
            userRole = (currentUser.rol || 'user').toLowerCase();
        } else {
            // Si no hay usuario en la sesión, intentar obtenerlo del endpoint
            try {
                const response = await window.authManager.authenticatedFetch('http://127.0.0.1:8000/auth/me');
                if (response.ok) {
                    const userData = await response.json();
                    userPlan = (userData.plan || 'free').toLowerCase();
                    userRole = (userData.rol || 'user').toLowerCase();
                    console.log('Usuario obtenido desde /auth/me:', userData);
                } else {
                    throw new Error('No se pudo obtener información del usuario');
                }
            } catch (e) {
                console.error('Error obteniendo usuario:', e);
                exportButtonsContainer.innerHTML = '<span class="text-danger">Error: No se pudo obtener información del usuario</span>';
                return;
            }
        }
        
        console.log('Plan:', userPlan, 'Rol:', userRole);
        
        // Admin tiene acceso a todos los formatos
        const availableFormats = userRole === 'admin' 
            ? EXPORT_FORMATS.admin 
            : (EXPORT_FORMATS[userPlan] || EXPORT_FORMATS.free);
        
        console.log('Formatos disponibles:', availableFormats);
        
        // Limpiar contenedor
        exportButtonsContainer.innerHTML = '';
        
        // Si no hay formatos disponibles, mostrar mensaje
        if (!availableFormats || availableFormats.length === 0) {
            exportButtonsContainer.innerHTML = '<span class="text-muted">No hay formatos de exportación disponibles para tu plan</span>';
            return;
        }
        
        // Crear botones para cada formato disponible
        availableFormats.forEach(format => {
            const formatInfo = FORMAT_INFO[format];
            if (!formatInfo) {
                console.warn('Formato no encontrado:', format);
                return;
            }
            
            const button = document.createElement('button');
            button.className = `btn btn-sm btn-outline-${formatInfo.color} me-1 mb-1`;
            button.innerHTML = `<i class="fas ${formatInfo.icon} me-1"></i>${formatInfo.label}`;
            button.title = `Exportar a ${formatInfo.label}`;
            button.onclick = () => exportNews(format);
            
            exportButtonsContainer.appendChild(button);
        });
        
        console.log('Botones de exportación cargados correctamente');
        
    } catch (error) {
        console.error('Error cargando botones de exportación:', error);
        exportButtonsContainer.innerHTML = `<span class="text-danger">Error: ${error.message || 'Error desconocido'}</span>`;
    }
}

/**
 * Exportar noticias según el formato seleccionado
 */
async function exportNews(format) {
    try {
        // Obtener filtros actuales
        const filters = getCurrentFilters();
        
        // Construir URL de exportación
        const params = new URLSearchParams();
        params.append('format', format);
        
        if (filters.q) params.append('q', filters.q);
        if (filters.fuente) params.append('fuente', filters.fuente);
        if (filters.categoria) params.append('categoria', filters.categoria);
        if (filters.dateFrom) params.append('date_from', filters.dateFrom);
        if (filters.dateTo) params.append('date_to', filters.dateTo);
        
        // Obtener token de autenticación
        const token = window.authManager?.getAccessToken();
        if (!token) {
            showNotification('Error: No hay sesión activa', 'error');
            return;
        }
        
        // Mostrar indicador de carga
        showNotification('Exportando noticias...', 'info');
        
        // Hacer petición de exportación
        const response = await fetch(`${API_BASE_URL}/api/export?${params.toString()}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        // Obtener el nombre del archivo del header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `noticias_${new Date().toISOString().split('T')[0]}.${format}`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        // Descargar archivo
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification(`Noticias exportadas exitosamente a ${FORMAT_INFO[format].label}`, 'success');
        
    } catch (error) {
        console.error('Error exportando noticias:', error);
        showNotification(`Error al exportar: ${error.message}`, 'error');
    }
}

/**
 * Obtener filtros actuales del formulario
 */
function getCurrentFilters() {
    return {
        q: document.getElementById('searchInput')?.value || '',
        fuente: document.getElementById('filterSource')?.value || '',
        categoria: document.getElementById('filterCategory')?.value || '',
        dateFrom: document.getElementById('filterDateFrom')?.value || '',
        dateTo: document.getElementById('filterDateTo')?.value || ''
    };
}

/**
 * Abrir modal para crear noticia
 */
function openCreateModal() {
    const modal = new bootstrap.Modal(document.getElementById('newsModal'));
    document.getElementById('modalTitle').textContent = 'Nueva Noticia';
    document.getElementById('newsForm').reset();
    document.getElementById('newsId').value = '';
    clearImagePreview();
    updateImageFields();
    modal.show();
}

/**
 * Editar noticia
 */
async function editNews(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/news/${id}`);
        if (!response.ok) throw new Error('Error al cargar noticia');
        
        const news = await response.json();
        
        // Llenar formulario
        document.getElementById('newsId').value = news.id;
        document.getElementById('newsTitulo').value = news.titulo || '';
        document.getElementById('newsUrl').value = news.url || '';
        document.getElementById('newsFuente').value = news.fuente || '';
        document.getElementById('newsCategoria').value = news.categoria || '';
        document.getElementById('newsAutor').value = news.autor || '';
        document.getElementById('newsDominio').value = news.dominio || '';
        document.getElementById('newsResumen').value = news.resumen || '';
        document.getElementById('newsContenido').value = news.contenido || '';
        document.getElementById('newsKeywords').value = news.keywords || news.tags || '';
        const imagenUrl = news.imagen_principal || news.imagenes || '';
        document.getElementById('newsImagen').value = imagenUrl;
        if (imagenUrl) {
            previewImage(imagenUrl);
        } else {
            clearImagePreview();
        }
        document.getElementById('newsCantidadImagenes').value = news.cantidad_imagenes || 0;
        document.getElementById('newsTieneImagenes').checked = news.tiene_imagenes || false;
        document.getElementById('newsTipoContenido').value = news.tipo_contenido || '';
        updateImageFields();
        
        // Fecha y hora
        if (news.fecha) {
            const fecha = new Date(news.fecha);
            document.getElementById('newsFecha').value = fecha.toISOString().split('T')[0];
        }
        if (news.hora) {
            const hora = news.hora.split(':');
            document.getElementById('newsHora').value = `${hora[0]}:${hora[1]}`;
        }
        
        document.getElementById('modalTitle').textContent = 'Editar Noticia';
        const modal = new bootstrap.Modal(document.getElementById('newsModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error cargando noticia:', error);
        showNotification('Error al cargar la noticia', 'error');
    }
}

/**
 * Guardar noticia (crear o actualizar)
 */
async function saveNews() {
    const form = document.getElementById('newsForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const id = document.getElementById('newsId').value;
    const isEdit = !!id;
    
    // Preparar datos
    const newsData = {
        titulo: document.getElementById('newsTitulo').value,
        url: document.getElementById('newsUrl').value,
        fuente: document.getElementById('newsFuente').value || null,
        categoria: document.getElementById('newsCategoria').value || null,
        autor: document.getElementById('newsAutor').value || null,
        dominio: document.getElementById('newsDominio').value || null,
        resumen: document.getElementById('newsResumen').value || null,
        contenido: document.getElementById('newsContenido').value || null,
        keywords: document.getElementById('newsKeywords').value || null,
        imagen_principal: document.getElementById('newsImagen').value || null,
        cantidad_imagenes: parseInt(document.getElementById('newsCantidadImagenes').value) || 0,
        tiene_imagenes: document.getElementById('newsTieneImagenes').checked,
        tipo_contenido: document.getElementById('newsTipoContenido').value || null
    };
    
    // Fecha y hora
    const fecha = document.getElementById('newsFecha').value;
    if (fecha) newsData.fecha = fecha;
    
    const hora = document.getElementById('newsHora').value;
    if (hora) newsData.hora = hora + ':00';
    
    try {
        let response;
        if (isEdit) {
            // Actualizar
            response = await fetch(`${API_BASE_URL}/api/admin/news/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newsData)
            });
        } else {
            // Crear
            response = await fetch(`${API_BASE_URL}/api/admin/news`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newsData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar noticia');
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('newsModal'));
        modal.hide();
        
        showNotification(isEdit ? 'Noticia actualizada exitosamente' : 'Noticia creada exitosamente', 'success');
        loadNews();
        
    } catch (error) {
        console.error('Error guardando noticia:', error);
        showNotification(error.message || 'Error al guardar la noticia', 'error');
    }
}

/**
 * Eliminar noticia
 */
function deleteNews(id, title) {
    deleteNewsId = id;
    document.getElementById('deleteNewsTitle').textContent = title || `Noticia #${id}`;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

/**
 * Confirmar eliminación
 */
async function confirmDelete() {
    if (!deleteNewsId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/news/${deleteNewsId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar noticia');
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        modal.hide();
        
        showNotification('Noticia eliminada exitosamente', 'success');
        loadNews();
        deleteNewsId = null;
        
    } catch (error) {
        console.error('Error eliminando noticia:', error);
        showNotification(error.message || 'Error al eliminar la noticia', 'error');
    }
}

/**
 * Utilidades
 */
function truncateText(text, maxLength) {
    if (!text) return '-';
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

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

/**
 * Vista previa de imagen
 */
function previewImage(url) {
    const preview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    
    if (!url || !url.trim()) {
        clearImagePreview();
        return;
    }
    
    // Intentar cargar la imagen
    previewImg.src = url;
    previewImg.onload = () => {
        preview.style.display = 'block';
    };
    previewImg.onerror = () => {
        preview.style.display = 'none';
        showNotification('No se pudo cargar la imagen. Verifica que la URL sea correcta.', 'error');
    };
}

/**
 * Limpiar vista previa
 */
function clearImagePreview() {
    const preview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const imagenInput = document.getElementById('newsImagen');
    
    if (preview) preview.style.display = 'none';
    if (previewImg) previewImg.src = '';
    if (imagenInput) imagenInput.value = '';
}

/**
 * Probar URL de imagen
 */
function testImageUrl() {
    const imagenInput = document.getElementById('newsImagen');
    const url = imagenInput.value.trim();
    
    if (!url) {
        showNotification('Ingresa una URL de imagen primero', 'error');
        return;
    }
    
    previewImage(url);
}

/**
 * Actualizar campos relacionados con imágenes
 */
function updateImageFields() {
    const tieneImagenes = document.getElementById('newsTieneImagenes').checked;
    const imagenUrl = document.getElementById('newsImagen').value.trim();
    const cantidadInput = document.getElementById('newsCantidadImagenes');
    
    // Si tiene imágenes y hay URL, actualizar cantidad
    if (tieneImagenes && imagenUrl) {
        cantidadInput.value = Math.max(1, parseInt(cantidadInput.value) || 1);
    } else if (!tieneImagenes && !imagenUrl) {
        cantidadInput.value = 0;
    }
}

/**
 * Mostrar modal con imagen grande
 */
function showImageModal(imageUrl) {
    // Crear modal dinámico si no existe
    let modal = document.getElementById('imageModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'imageModal';
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Vista Previa de Imagen</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <img id="modalImage" src="" alt="Imagen" class="img-fluid" style="max-height: 70vh;">
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    const modalImage = document.getElementById('modalImage');
    if (modalImage) {
        modalImage.src = imageUrl;
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

// Hacer funciones disponibles globalmente
window.loadNews = loadNews;
window.changePage = changePage;
window.clearFilters = clearFilters;
window.openCreateModal = openCreateModal;
window.editNews = editNews;
window.saveNews = saveNews;
window.deleteNews = deleteNews;
window.confirmDelete = confirmDelete;
window.previewImage = previewImage;
window.clearImagePreview = clearImagePreview;
window.testImageUrl = testImageUrl;
window.updateImageFields = updateImageFields;
window.showImageModal = showImageModal;

