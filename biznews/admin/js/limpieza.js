/**
 * Gestión de Limpieza de Noticias con IA
 * BizNews Admin
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// Variables de paginación para noticias limpiadas
let currentPageLimpiadas = 1;
let pageSizeLimpiadas = 20;
let totalPagesLimpiadas = 1;

// Cargar categorías y fuentes al iniciar
document.addEventListener('DOMContentLoaded', () => {
    // Esperar a que authManager esté disponible
    function initLimpieza() {
        if (!window.authManager) {
            console.log('⏳ Esperando authManager...');
            setTimeout(initLimpieza, 100);
            return;
        }
        
        console.log('✅ authManager disponible, inicializando limpieza...');
        loadCategories();
        loadSources();
        setupEventListeners();
        loadNoticiasLimpiadas(); // Cargar noticias limpiadas al iniciar
    }
    
    initLimpieza();
});

/**
 * Cargar categorías disponibles
 */
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/news/categorias/listar`);
        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById('categoria');
            
            // La API devuelve directamente un array, no un objeto con propiedad 'categorias'
            const categorias = Array.isArray(data) ? data : (data.categorias || []);
            
            if (!select) {
                console.warn('⚠️ No se encontró el elemento select#categoria');
                return;
            }
            
            categorias.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                select.appendChild(option);
            });
            
            console.log(`✅ ${categorias.length} categorías cargadas`);
        } else {
            console.error('Error en respuesta de categorías:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('Error cargando categorías:', error);
    }
}

/**
 * Cargar fuentes disponibles
 */
async function loadSources() {
    try {
        const response = await fetch(`${API_BASE_URL}/news/fuentes/listar`);
        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById('fuente');
            
            // La API devuelve directamente un array, no un objeto con propiedad 'fuentes'
            const fuentes = Array.isArray(data) ? data : (data.fuentes || []);
            
            if (!select) {
                console.warn('⚠️ No se encontró el elemento select#fuente');
                return;
            }
            
            fuentes.forEach(fuente => {
                const option = document.createElement('option');
                option.value = fuente;
                option.textContent = fuente;
                select.appendChild(option);
            });
            
            console.log(`✅ ${fuentes.length} fuentes cargadas`);
        } else {
            console.error('Error en respuesta de fuentes:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('Error cargando fuentes:', error);
    }
}

/**
 * Configurar event listeners
 */
function setupEventListeners() {
    const form = document.getElementById('limpiezaForm');
    const btnLimpiarFormulario = document.getElementById('btnLimpiarFormulario');
    const btnBuscarTitulo = document.getElementById('btnBuscarTitulo');
    const btnSeleccionarTodos = document.getElementById('btnSeleccionarTodos');
    const btnDeseleccionarTodos = document.getElementById('btnDeseleccionarTodos');
    const btnProcesarSeleccionadas = document.getElementById('btnProcesarSeleccionadas');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await procesarLimpieza();
    });
    
    btnLimpiarFormulario.addEventListener('click', () => {
        form.reset();
        document.getElementById('resultadosCard').style.display = 'none';
        document.getElementById('resultadosBusquedaCard').style.display = 'none';
    });
    
    // Buscar por título
    if (btnBuscarTitulo) {
        btnBuscarTitulo.addEventListener('click', async () => {
            const titulo = document.getElementById('titulo').value.trim();
            if (!titulo) {
                alert('⚠️ Por favor, ingresa un término de búsqueda');
                return;
            }
            await buscarNoticiasPorTitulo(titulo);
        });
        
        // También buscar al presionar Enter
        const tituloInput = document.getElementById('titulo');
        if (tituloInput) {
            tituloInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    btnBuscarTitulo.click();
                }
            });
        }
    }
    
    // Seleccionar todas
    if (btnSeleccionarTodos) {
        btnSeleccionarTodos.addEventListener('click', () => {
            document.querySelectorAll('#resultadosBusqueda input[type="checkbox"]').forEach(cb => {
                cb.checked = true;
            });
        });
    }
    
    // Deseleccionar todas
    if (btnDeseleccionarTodos) {
        btnDeseleccionarTodos.addEventListener('click', () => {
            document.querySelectorAll('#resultadosBusqueda input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
        });
    }
    
    // Procesar seleccionadas
    if (btnProcesarSeleccionadas) {
        btnProcesarSeleccionadas.addEventListener('click', async () => {
            const seleccionadas = Array.from(document.querySelectorAll('#resultadosBusqueda input[type="checkbox"]:checked'))
                .map(cb => parseInt(cb.value));
            
            if (seleccionadas.length === 0) {
                alert('⚠️ Por favor, selecciona al menos una noticia para procesar');
                return;
            }
            
            await procesarNoticiasSeleccionadas(seleccionadas);
        });
    }
}

/**
 * Procesar limpieza de noticias
 */
async function procesarLimpieza() {
    const btnLimpiar = document.getElementById('btnLimpiar');
    const resultadosCard = document.getElementById('resultadosCard');
    
    // Obtener valores del formulario
    const request = {
        noticia_id: document.getElementById('noticiaId').value ? parseInt(document.getElementById('noticiaId').value) : null,
        titulo: document.getElementById('titulo').value.trim() || null,
        categoria: document.getElementById('categoria').value || null,
        fuente: document.getElementById('fuente').value || null,
        cantidad: document.getElementById('cantidad').value ? parseInt(document.getElementById('cantidad').value) : null,
        fecha_desde: document.getElementById('fechaDesde').value || null,
        fecha_hasta: document.getElementById('fechaHasta').value || null,
        prompt_personalizado: document.getElementById('promptPersonalizado').value.trim() || null,
        modelo: document.getElementById('modelo').value,
        tabla_origen: document.getElementById('tablaOrigen').value
    };
    
    // Validar que al menos haya un filtro o cantidad
    // Nota: Si se usa búsqueda por título, se debe usar el botón "Buscar" primero para seleccionar noticias
    if (!request.noticia_id && !request.categoria && !request.fuente && !request.cantidad) {
        // Si hay título pero no otros filtros, sugerir usar el botón de búsqueda
        if (request.titulo) {
            alert('⚠️ Para buscar por título, usa el botón "Buscar" para ver y seleccionar las noticias encontradas.');
            return;
        }
        alert('⚠️ Por favor, especifica al menos un filtro (ID, categoría, fuente) o una cantidad de noticias a procesar.\n\nPara buscar por título, usa el botón "Buscar" junto al campo de título.');
        return;
    }
    
    // Deshabilitar botón y mostrar loading
    btnLimpiar.disabled = true;
    btnLimpiar.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
    
    try {
        // Usar authManager.authenticatedFetch que maneja la autenticación automáticamente
        if (!window.authManager) {
            throw new Error('AuthManager no está disponible. Por favor, recarga la página.');
        }
        
        // Debug: Verificar sesión
        const session = window.authManager.getSession();
        console.log('🔍 Sesión actual:', session ? 'Existe' : 'No existe');
        if (session) {
            console.log('🔍 Sesión expira en:', new Date(session.expiresAt).toLocaleString());
            console.log('🔍 Token disponible:', session.access_token ? 'Sí' : 'No');
        } else {
            // Si no hay sesión, verificar localStorage directamente
            const sessionData = localStorage.getItem('biznews_admin_session');
            console.log('🔍 Datos de sesión en localStorage:', sessionData ? 'Existen' : 'No existen');
            if (sessionData) {
                try {
                    const parsed = JSON.parse(sessionData);
                    console.log('🔍 Datos parseados:', {
                        access_token: parsed.access_token ? 'Existe (' + parsed.access_token.substring(0, 20) + '...)' : 'No existe',
                        expiresAt: parsed.expiresAt ? new Date(parsed.expiresAt).toLocaleString() : 'No existe',
                        usuario: parsed.usuario || 'No existe'
                    });
                } catch (e) {
                    console.error('Error parseando sesión:', e);
                }
            }
        }
        
        // Usar authenticatedFetch de authManager (maneja tokens automáticamente)
        // Si no hay token, authenticatedFetch lanzará un error apropiado
        console.log('📡 Enviando petición a /api/nlp/limpiar...');
        const response = await window.authManager.authenticatedFetch(`${API_BASE_URL}/api/nlp/limpiar`, {
            method: 'POST',
            body: JSON.stringify(request)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error procesando noticias');
        }
        
        const result = await response.json();
        
        // Mostrar resultados
        mostrarResultados(result);
        
    } catch (error) {
        console.error('Error:', error);
        alert(`❌ Error: ${error.message}`);
    } finally {
        // Restaurar botón
        btnLimpiar.disabled = false;
        btnLimpiar.innerHTML = '<i class="fas fa-magic me-2"></i>Iniciar Limpieza';
    }
}

/**
 * Mostrar resultados de la limpieza
 */
function mostrarResultados(result) {
    const resultadosCard = document.getElementById('resultadosCard');
    const totalProcesadas = document.getElementById('totalProcesadas');
    const totalExitosas = document.getElementById('totalExitosas');
    const totalErrores = document.getElementById('totalErrores');
    const detallesResultados = document.getElementById('detallesResultados');
    
    // Actualizar estadísticas
    totalProcesadas.textContent = result.procesadas;
    totalExitosas.textContent = result.exitosas;
    totalErrores.textContent = result.errores;
    
    // Mostrar detalles
    let html = '<div class="table-responsive"><table class="table table-hover">';
    html += '<thead><tr><th>ID</th><th>Título</th><th>Estado</th><th>Relevantes</th><th>Irrelevantes</th></tr></thead>';
    html += '<tbody>';
    
    result.detalles.forEach(detalle => {
        const estadoClass = detalle.estado === 'exitoso' ? 'status-exitoso' : 'status-error';
        const estadoText = detalle.estado === 'exitoso' ? '✅ Exitoso' : '❌ Error';
        
        html += '<tr>';
        html += `<td>${detalle.noticia_id}</td>`;
        html += `<td>${detalle.titulo || 'N/A'}</td>`;
        html += `<td><span class="status-badge ${estadoClass}">${estadoText}</span></td>`;
        
        if (detalle.estado === 'exitoso') {
            html += `<td>${detalle.relevantes || 0}</td>`;
            html += `<td>${detalle.irrelevantes || 0}</td>`;
        } else {
            html += `<td colspan="2"><small class="text-danger">${detalle.error || 'Error desconocido'}</small></td>`;
        }
        
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    detallesResultados.innerHTML = html;
    
    // Mostrar card de resultados
    resultadosCard.style.display = 'block';
    
    // Scroll a resultados
    resultadosCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Cargar noticias limpiadas
 */
async function loadNoticiasLimpiadas() {
    const container = document.getElementById('noticiasLimpiadasContainer');
    if (!container) return;
    
    try {
        container.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2 text-muted">Cargando noticias limpiadas...</p>
            </div>
        `;
        
        // Obtener término de búsqueda
        const searchTerm = document.getElementById('buscarLimpiadas')?.value || '';
        
        // Construir URL con parámetros de paginación
        const skip = (currentPageLimpiadas - 1) * pageSizeLimpiadas;
        let url = `${API_BASE_URL}/api/nlp/limpiadas?skip=${skip}&limit=${pageSizeLimpiadas}&order=desc`;
        if (searchTerm) {
            url += `&q=${encodeURIComponent(searchTerm)}`;
        }
        
        const response = await window.authManager.authenticatedFetch(url);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            console.error('❌ Error en respuesta:', errorData);
            throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Calcular total de páginas
        totalPagesLimpiadas = Math.ceil(data.total / pageSizeLimpiadas);
        
        if (data.items.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay noticias limpiadas aún.</p>
                </div>
            `;
            renderPaginationLimpiadas();
            return;
        }
        
        // Renderizar noticias
        let html = '<div class="table-responsive"><table class="table table-hover table-striped">';
        html += '<thead><tr>';
        html += '<th>ID</th>';
        html += '<th>Título</th>';
        html += '<th>Fuente</th>';
        html += '<th>Modelo</th>';
        html += '<th>Relevantes</th>';
        html += '<th>Irrelevantes</th>';
        html += '<th>% Relevancia</th>';
        html += '<th>Procesado</th>';
        html += '<th>Acciones</th>';
        html += '</tr></thead><tbody>';
        
        data.items.forEach(noticia => {
            const porcentaje = noticia.porcentaje_relevancia || 0;
            const porcentajeClass = porcentaje >= 70 ? 'text-success' : porcentaje >= 50 ? 'text-warning' : 'text-danger';
            
            html += '<tr>';
            html += `<td>${noticia.id}</td>`;
            html += `<td><strong>${noticia.titulo?.substring(0, 60) || 'Sin título'}${noticia.titulo && noticia.titulo.length > 60 ? '...' : ''}</strong></td>`;
            html += `<td>${noticia.fuente || 'N/A'}</td>`;
            html += `<td><span class="badge bg-info">${noticia.modelo_usado || 'N/A'}</span></td>`;
            html += `<td><span class="badge bg-success">${noticia.num_parrafos_relevantes || 0}</span></td>`;
            html += `<td><span class="badge bg-danger">${noticia.num_parrafos_irrelevantes || 0}</span></td>`;
            html += `<td><strong class="${porcentajeClass}">${porcentaje.toFixed(1)}%</strong></td>`;
            html += `<td><small>${noticia.procesado_at ? new Date(noticia.procesado_at).toLocaleDateString('es-ES') : 'N/A'}</small></td>`;
            html += `<td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-primary" onclick="verNoticiaLimpiada(${noticia.id})" title="Ver detalles">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${noticia.noticia_id ? `
                        <button class="btn btn-sm btn-warning" onclick="reprocesarNoticia(${noticia.noticia_id}, '${noticia.titulo?.replace(/'/g, "\\'") || 'Sin título'}')" title="Reprocesar con IA">
                            <i class="fas fa-redo"></i>
                        </button>
                    ` : ''}
                </div>
            </td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        html += `<div class="mt-3 d-flex justify-content-between align-items-center">
            <small class="text-muted">Mostrando ${(currentPageLimpiadas - 1) * pageSizeLimpiadas + 1} - ${Math.min(currentPageLimpiadas * pageSizeLimpiadas, data.total)} de ${data.total} noticias limpiadas</small>
        </div>`;
        
        container.innerHTML = html;
        
        // Renderizar paginación
        renderPaginationLimpiadas();
        
    } catch (error) {
        console.error('Error cargando noticias limpiadas:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error cargando noticias limpiadas: ${error.message}
            </div>
        `;
    }
}

// Event listeners para búsqueda y refrescar
document.addEventListener('DOMContentLoaded', () => {
    const buscarInput = document.getElementById('buscarLimpiadas');
    const btnRefrescar = document.getElementById('btnRefrescarLimpiadas');
    
    if (buscarInput) {
        let searchTimeout;
        buscarInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPageLimpiadas = 1; // Resetear a primera página al buscar
                loadNoticiasLimpiadas();
            }, 500); // Esperar 500ms después de que el usuario deje de escribir
        });
        
        // Enter en búsqueda
        buscarInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                currentPageLimpiadas = 1;
                loadNoticiasLimpiadas();
            }
        });
    }
    
    if (btnRefrescar) {
        btnRefrescar.addEventListener('click', () => {
            currentPageLimpiadas = 1;
            loadNoticiasLimpiadas();
        });
    }
});

/**
 * Renderizar paginación para noticias limpiadas
 */
function renderPaginationLimpiadas() {
    const pagination = document.getElementById('paginationLimpiadas');
    if (!pagination) return;
    
    if (totalPagesLimpiadas <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Botón anterior
    html += `
        <li class="page-item ${currentPageLimpiadas === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePageLimpiadas(${currentPageLimpiadas - 1}); return false;">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Números de página
    const startPage = Math.max(1, currentPageLimpiadas - 2);
    const endPage = Math.min(totalPagesLimpiadas, currentPageLimpiadas + 2);
    
    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePageLimpiadas(1); return false;">1</a></li>`;
        if (startPage > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPageLimpiadas ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePageLimpiadas(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPagesLimpiadas) {
        if (endPage < totalPagesLimpiadas - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePageLimpiadas(${totalPagesLimpiadas}); return false;">${totalPagesLimpiadas}</a></li>`;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${currentPageLimpiadas === totalPagesLimpiadas ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePageLimpiadas(${currentPageLimpiadas + 1}); return false;">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

/**
 * Cambiar página de noticias limpiadas
 */
function changePageLimpiadas(page) {
    if (page < 1 || page > totalPagesLimpiadas) return;
    currentPageLimpiadas = page;
    loadNoticiasLimpiadas();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Hacer la función global
window.changePageLimpiadas = changePageLimpiadas;

/**
 * Ver detalles de una noticia limpiada en un modal
 */
async function verNoticiaLimpiada(noticiaId) {
    const modal = new bootstrap.Modal(document.getElementById('modalNoticiaLimpiada'));
    const modalBody = document.getElementById('modalNoticiaLimpiadaBody');
    const modalTitle = document.getElementById('modalNoticiaLimpiadaLabel');
    
    // Mostrar loading
    modalBody.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando detalles de la noticia...</p>
        </div>
    `;
    
    modal.show();
    
    try {
        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/api/nlp/limpiadas/${noticiaId}`
        );
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(errorData.detail || `Error ${response.status}`);
        }
        
        const noticia = await response.json();
        
        // Calcular porcentaje de relevancia
        const porcentaje = noticia.porcentaje_relevancia || 0;
        const porcentajeClass = porcentaje >= 70 ? 'text-success' : porcentaje >= 50 ? 'text-warning' : 'text-danger';
        
        // Construir HTML del modal
        let html = `
            <div class="row mb-3">
                <div class="col-md-8">
                    <h4>${noticia.titulo || 'Sin título'}</h4>
                </div>
                <div class="col-md-4 text-end">
                    <span class="badge bg-primary">ID: ${noticia.id}</span>
                    ${noticia.noticia_id ? `<span class="badge bg-secondary">Noticia ID: ${noticia.noticia_id}</span>` : ''}
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong><i class="fas fa-newspaper me-2"></i>Fuente:</strong> ${noticia.fuente || 'N/A'}<br>
                    <strong><i class="fas fa-robot me-2"></i>Modelo:</strong> <span class="badge bg-info">${noticia.modelo_usado || 'N/A'}</span><br>
                    <strong><i class="fas fa-calendar me-2"></i>Fecha:</strong> ${noticia.fecha ? new Date(noticia.fecha).toLocaleDateString('es-ES') : 'N/A'}<br>
                    <strong><i class="fas fa-clock me-2"></i>Procesado:</strong> ${noticia.procesado_at ? new Date(noticia.procesado_at).toLocaleString('es-ES') : 'N/A'}
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-chart-pie me-2"></i>Estadísticas:</strong><br>
                    <span class="badge bg-success">Relevantes: ${noticia.num_parrafos_relevantes || 0}</span>
                    <span class="badge bg-danger">Irrelevantes: ${noticia.num_parrafos_irrelevantes || 0}</span>
                    <span class="badge bg-secondary">Total: ${noticia.num_parrafos_total || 0}</span><br>
                    <strong class="${porcentajeClass} mt-2 d-inline-block">% Relevancia: ${porcentaje.toFixed(1)}%</strong>
                </div>
            </div>
            
            ${noticia.url ? `<div class="mb-3"><strong><i class="fas fa-link me-2"></i>URL:</strong> <a href="${noticia.url}" target="_blank" class="text-break">${noticia.url}</a></div>` : ''}
            
            ${noticia.resumen ? `
            <div class="mb-3">
                <h5><i class="fas fa-align-left me-2"></i>Resumen</h5>
                <div class="p-3 bg-light rounded">${noticia.resumen}</div>
            </div>
            ` : ''}
            
            ${noticia.contenido_limpio ? `
            <div class="mb-3">
                <h5><i class="fas fa-magic me-2"></i>Contenido Limpio</h5>
                <div class="p-3 bg-light rounded" style="max-height: 300px; overflow-y: auto;">
                    ${noticia.contenido_limpio.split('\n').map(p => `<p class="mb-2">${p}</p>`).join('')}
                </div>
            </div>
            ` : ''}
        `;
        
        // Párrafos relevantes
        if (noticia.parrafos_relevantes && noticia.parrafos_relevantes.length > 0) {
            html += `
                <div class="mb-3">
                    <h5><i class="fas fa-check-circle text-success me-2"></i>Párrafos Relevantes (${noticia.parrafos_relevantes.length})</h5>
                    <div class="p-3 bg-success bg-opacity-10 rounded" style="max-height: 300px; overflow-y: auto;">
                        ${noticia.parrafos_relevantes.map((p, idx) => `
                            <div class="mb-2 p-2 bg-white rounded border border-success">
                                <strong class="text-success">#${idx + 1}</strong>
                                <p class="mb-0">${p}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Párrafos irrelevantes
        if (noticia.parrafos_irrelevantes && noticia.parrafos_irrelevantes.length > 0) {
            html += `
                <div class="mb-3">
                    <h5><i class="fas fa-times-circle text-danger me-2"></i>Párrafos Irrelevantes (${noticia.parrafos_irrelevantes.length})</h5>
                    <div class="p-3 bg-danger bg-opacity-10 rounded" style="max-height: 300px; overflow-y: auto;">
                        ${noticia.parrafos_irrelevantes.map((p, idx) => `
                            <div class="mb-2 p-2 bg-white rounded border border-danger">
                                <strong class="text-danger">#${idx + 1}</strong>
                                <p class="mb-0">${p}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Contenido raw (opcional, colapsable)
        if (noticia.contenido_raw) {
            html += `
                <div class="mb-3">
                    <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#contenidoRaw">
                        <i class="fas fa-code me-1"></i>Ver Contenido Original
                    </button>
                    <div class="collapse mt-2" id="contenidoRaw">
                        <div class="p-3 bg-light rounded" style="max-height: 300px; overflow-y: auto; font-size: 0.9em;">
                            ${noticia.contenido_raw.split('\n').map(p => `<p class="mb-1">${p}</p>`).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        modalBody.innerHTML = html;
        
    } catch (error) {
        console.error('Error cargando detalle de noticia:', error);
        modalBody.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error cargando detalles: ${error.message}
            </div>
        `;
    }
}

// Hacer la función global para que pueda ser llamada desde onclick
window.verNoticiaLimpiada = verNoticiaLimpiada;

/**
 * Reprocesar una noticia con IA
 */
async function reprocesarNoticia(noticiaId, titulo) {
    if (!noticiaId) {
        alert('⚠️ No se puede reprocesar: ID de noticia no disponible');
        return;
    }

    const confirmacion = confirm(
        `¿Estás seguro de que deseas reprocesar esta noticia con IA?\n\n` +
        `Título: ${titulo}\n` +
        `ID: ${noticiaId}\n\n` +
        `Esto actualizará el contenido limpio y los párrafos relevantes/irrelevantes.`
    );

    if (!confirmacion) {
        return;
    }

    // Obtener el modelo seleccionado del formulario o usar el predeterminado
    const modeloSelect = document.getElementById('modelo');
    const modelo = modeloSelect ? modeloSelect.value : 'llama3.2';

    // Obtener la tabla origen del formulario o usar la predeterminada
    const tablaOrigenSelect = document.getElementById('tablaOrigen');
    const tablaOrigen = tablaOrigenSelect ? tablaOrigenSelect.value : 'noticias_limpia';

    // Mostrar loading
    const loadingToast = showToast('info', 'Reprocesando noticia...', 'Por favor espera mientras se procesa la noticia con IA.');

    try {
        if (!window.authManager) {
            throw new Error('AuthManager no está disponible. Por favor, recarga la página.');
        }

        const request = {
            noticia_id: noticiaId,
            modelo: modelo,
            tabla_origen: tablaOrigen
        };

        console.log('🔄 Reprocesando noticia:', request);

        const response = await window.authManager.authenticatedFetch(
            `${API_BASE_URL}/api/nlp/limpiar`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request)
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(errorData.detail || `Error ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ Respuesta de reprocesamiento:', data);

        // Ocultar loading
        hideToast(loadingToast);

        if (data.exitosas > 0) {
            showToast('success', '✅ Noticia reprocesada exitosamente', 
                `La noticia ha sido reprocesada con IA. ${data.detalles && data.detalles.length > 0 ? data.detalles[0].relevantes + ' párrafos relevantes encontrados.' : ''}`);
            
            // Recargar la tabla de noticias limpiadas después de un breve delay
            setTimeout(() => {
                loadNoticiasLimpiadas();
            }, 1000);
        } else {
            throw new Error('No se pudo reprocesar la noticia. Verifica los detalles.');
        }

    } catch (error) {
        console.error('❌ Error reprocesando noticia:', error);
        hideToast(loadingToast);
        showToast('error', '❌ Error al reprocesar', error.message || 'Ocurrió un error al reprocesar la noticia.');
    }
}

// Hacer la función global
window.reprocesarNoticia = reprocesarNoticia;

/**
 * Buscar noticias por título
 */
async function buscarNoticiasPorTitulo(titulo) {
    const resultadosCard = document.getElementById('resultadosBusquedaCard');
    const resultadosDiv = document.getElementById('resultadosBusqueda');
    const totalEncontradas = document.getElementById('totalEncontradas');
    
    if (!resultadosCard || !resultadosDiv) return;
    
    // Mostrar loading
    resultadosCard.style.display = 'block';
    resultadosDiv.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Buscando noticias...</p></div>';
    
    try {
        // Obtener tabla origen
        const tablaOrigen = document.getElementById('tablaOrigen').value;
        
        // Usar el endpoint de noticias para buscar
        let url = `${API_BASE_URL}/news?q=${encodeURIComponent(titulo)}&limit=100`;
        
        // Si la tabla origen es noticias_limpia, buscar directamente en esa tabla
        if (tablaOrigen === 'noticias_limpia') {
            // Usar el endpoint de noticias que busca en noticias_limpia
            url = `${API_BASE_URL}/news?q=${encodeURIComponent(titulo)}&limit=100`;
        }
        
        const response = await window.authManager.authenticatedFetch(url);
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        const noticias = data.items || [];
        
        if (noticias.length === 0) {
            resultadosDiv.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No se encontraron noticias con el término "${titulo}"
                </div>
            `;
            totalEncontradas.textContent = '0';
            return;
        }
        
        // Renderizar resultados con checkboxes
        let html = '<table class="table table-hover table-striped">';
        html += '<thead><tr>';
        html += '<th style="width: 40px;"><input type="checkbox" id="selectAllCheckbox"></th>';
        html += '<th>ID</th>';
        html += '<th>Título</th>';
        html += '<th>Fuente</th>';
        html += '<th>Categoría</th>';
        html += '<th>Fecha</th>';
        html += '</tr></thead><tbody>';
        
        noticias.forEach(noticia => {
            const fecha = noticia.fecha ? new Date(noticia.fecha).toLocaleDateString('es-ES') : 'N/A';
            html += '<tr>';
            html += `<td><input type="checkbox" class="noticia-checkbox" value="${noticia.id}"></td>`;
            html += `<td><strong>${noticia.id}</strong></td>`;
            html += `<td>${noticia.titulo || 'Sin título'}</td>`;
            html += `<td>${noticia.fuente || 'N/A'}</td>`;
            html += `<td><span class="badge bg-secondary">${noticia.categoria || 'N/A'}</span></td>`;
            html += `<td><small>${fecha}</small></td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        resultadosDiv.innerHTML = html;
        totalEncontradas.textContent = noticias.length;
        
        // Checkbox para seleccionar todas
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                document.querySelectorAll('.noticia-checkbox').forEach(cb => {
                    cb.checked = e.target.checked;
                });
            });
        }
        
    } catch (error) {
        console.error('Error buscando noticias:', error);
        resultadosDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error buscando noticias: ${error.message}
            </div>
        `;
        totalEncontradas.textContent = '0';
    }
}

/**
 * Procesar noticias seleccionadas
 */
async function procesarNoticiasSeleccionadas(ids) {
    if (!ids || ids.length === 0) {
        alert('⚠️ No hay noticias seleccionadas');
        return;
    }
    
    const confirmacion = confirm(
        `¿Estás seguro de que deseas procesar ${ids.length} noticia(s) con IA?\n\n` +
        `Esto puede tardar varios minutos dependiendo de la cantidad.`
    );
    
    if (!confirmacion) {
        return;
    }
    
    const btnProcesar = document.getElementById('btnProcesarSeleccionadas');
    const resultadosCard = document.getElementById('resultadosCard');
    
    // Deshabilitar botón y mostrar loading
    if (btnProcesar) {
        btnProcesar.disabled = true;
        btnProcesar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Procesando...';
    }
    
    try {
        // Obtener modelo y tabla origen
        const modelo = document.getElementById('modelo').value;
        const tablaOrigen = document.getElementById('tablaOrigen').value;
        
        // Procesar cada noticia individualmente
        let exitosas = 0;
        let errores = 0;
        const detalles = [];
        
        for (const id of ids) {
            try {
                const request = {
                    noticia_id: id,
                    modelo: modelo,
                    tabla_origen: tablaOrigen
                };
                
                const response = await window.authManager.authenticatedFetch(
                    `${API_BASE_URL}/api/nlp/limpiar`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(request)
                    }
                );
                
                if (!response.ok) {
                    throw new Error(`Error ${response.status}`);
                }
                
                const data = await response.json();
                if (data.exitosas > 0) {
                    exitosas++;
                } else {
                    errores++;
                }
                
                detalles.push(...data.detalles);
                
            } catch (error) {
                errores++;
                detalles.push({
                    noticia_id: id,
                    titulo: `Noticia ID ${id}`,
                    estado: 'error',
                    error: error.message
                });
            }
        }
        
        // Mostrar resultados
        if (resultadosCard) {
            resultadosCard.style.display = 'block';
            const detallesDiv = document.getElementById('detallesResultados');
            if (detallesDiv) {
                let html = `
                    <div class="alert alert-${exitosas > 0 ? 'success' : 'danger'}">
                        <h5><i class="fas fa-${exitosas > 0 ? 'check-circle' : 'exclamation-triangle'} me-2"></i>Procesamiento Completado</h5>
                        <p><strong>Procesadas:</strong> ${ids.length}</p>
                        <p><strong>Exitosas:</strong> ${exitosas}</p>
                        <p><strong>Errores:</strong> ${errores}</p>
                    </div>
                    <h6>Detalles:</h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-striped">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Título</th>
                                    <th>Estado</th>
                                    <th>Detalles</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                detalles.forEach(detalle => {
                    const estadoClass = detalle.estado === 'exitoso' ? 'success' : 
                                       detalle.estado === 'advertencia' ? 'warning' : 'danger';
                    html += `
                        <tr>
                            <td>${detalle.noticia_id}</td>
                            <td>${detalle.titulo || 'N/A'}</td>
                            <td><span class="badge bg-${estadoClass}">${detalle.estado}</span></td>
                            <td>${detalle.error || detalle.mensaje || (detalle.relevantes ? `${detalle.relevantes} relevantes, ${detalle.irrelevantes} irrelevantes` : '')}</td>
                        </tr>
                    `;
                });
                
                html += '</tbody></table></div>';
                detallesDiv.innerHTML = html;
            }
        }
        
        // Recargar noticias limpiadas (resetear a primera página)
        currentPageLimpiadas = 1;
        loadNoticiasLimpiadas();
        
        // Ocultar resultados de búsqueda
        document.getElementById('resultadosBusquedaCard').style.display = 'none';
        
    } catch (error) {
        console.error('Error procesando noticias seleccionadas:', error);
        alert(`❌ Error procesando noticias: ${error.message}`);
    } finally {
        if (btnProcesar) {
            btnProcesar.disabled = false;
            btnProcesar.innerHTML = '<i class="fas fa-magic me-1"></i> Procesar Seleccionadas';
        }
    }
}

/**
 * Mostrar toast/notificación
 */
function showToast(type, title, message) {
    // Crear contenedor de toast si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(toastContainer);
    }

    const toastId = 'toast-' + Date.now();
    const bgColor = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : type === 'info' ? 'bg-info' : 'bg-warning';
    const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : type === 'info' ? 'fa-info-circle' : 'fa-exclamation-triangle';

    const toastHTML = `
        <div id="${toastId}" class="toast show align-items-center text-white ${bgColor} border-0" role="alert" style="min-width: 300px;">
            <div class="d-flex">
                <div class="toast-body">
                    <strong><i class="fas ${icon} me-2"></i>${title}</strong><br>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);

    // Auto-ocultar después de 5 segundos (excepto para info que puede durar más)
    if (type !== 'info') {
        setTimeout(() => {
            hideToast(toastElement);
        }, 5000);
    }

    return toastElement;
}

/**
 * Ocultar toast
 */
function hideToast(toastElement) {
    if (toastElement) {
        const bsToast = bootstrap.Toast.getOrCreateInstance(toastElement);
        bsToast.hide();
        setTimeout(() => {
            toastElement.remove();
        }, 300);
    }
}

