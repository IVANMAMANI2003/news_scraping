/**
 * BizNews Scrapers Management
 * Gestión de scrapers de noticias
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// Fuentes disponibles
const SOURCES = [
    { id: 'pachamama', name: 'Pachamama Radio', icon: 'fa-radio' },
    { id: 'punonoticias', name: 'Puno Noticias', icon: 'fa-newspaper' },
    { id: 'losandes', name: 'Los Andes', icon: 'fa-book' },
    { id: 'sinfronteras', name: 'Sin Fronteras', icon: 'fa-globe' }
];

let currentScrapingType = 'complete';
let selectedSources = [];
let scrapingInProgress = false;
let scrapingResults = [];
let currentJobId = null;
let pollingInterval = null;

/**
 * Inicializar página
 */
document.addEventListener('DOMContentLoaded', () => {
    initializePage();
    setupEventListeners();
});

/**
 * Inicializar página
 */
function initializePage() {
    loadSources();
    updateStats();
    setTodayAsDefault();
}

/**
 * Configurar event listeners
 */
function setupEventListeners() {
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (window.authManager) {
                window.authManager.logout();
            }
        });
    }

    // Date input - set max to today
    const dateInput = document.getElementById('scrapingDate');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('max', today);
    }
}

/**
 * Cargar fuentes disponibles desde la API
 */
async function loadSources() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/scrapers/sources`);
        if (!response.ok) {
            throw new Error('Error al cargar fuentes');
        }
        
        const data = await response.json();
        const apiSources = data.sources || [];
        
        // Actualizar SOURCES con datos de la API si están disponibles
        if (apiSources.length > 0) {
            SOURCES.length = 0;
            apiSources.forEach(source => {
                // Mapear iconos según el ID
                const iconMap = {
                    'pachamama': 'fa-radio',
                    'punonoticias': 'fa-newspaper',
                    'losandes': 'fa-book',
                    'sinfronteras': 'fa-globe'
                };
                SOURCES.push({
                    id: source.id,
                    name: source.name,
                    icon: iconMap[source.id] || 'fa-rss'
                });
            });
        }
    } catch (error) {
        console.error('Error cargando fuentes desde API, usando fuentes por defecto:', error);
        // Si falla, usar las fuentes por defecto ya definidas
    }
    
    // Renderizar fuentes
    const sourcesList = document.getElementById('sourcesList');
    const singleSourceSelect = document.getElementById('singleSourceSelect');
    
    if (sourcesList) {
        sourcesList.innerHTML = SOURCES.map(source => `
            <div class="source-checkbox">
                <input type="checkbox" 
                       id="source_${source.id}" 
                       value="${source.id}"
                       onchange="updateSelectedSources()">
                <label for="source_${source.id}" class="mb-0">
                    <i class="fas ${source.icon} me-2"></i>
                    ${source.name}
                </label>
            </div>
        `).join('');
    }

    if (singleSourceSelect) {
        singleSourceSelect.innerHTML = '<option value="">-- Selecciona una fuente --</option>' +
            SOURCES.map(source => `
                <option value="${source.id}">
                    ${source.name}
                </option>
            `).join('');
    }
    
    // Renderizar filtro de fuente
    renderSourceFilter();
}

/**
 * Renderizar selector de filtro de fuente
 */
function renderSourceFilter() {
    const sourceFilter = document.getElementById('sourceFilter');
    if (sourceFilter) {
        sourceFilter.innerHTML = '<option value="">Todas las fuentes</option>' +
            SOURCES.map(source => `
                <option value="${source.id}">
                    ${source.name}
                </option>
            `).join('');
    }
}

/**
 * Seleccionar tipo de scraping
 */
function selectScrapingType(type) {
    currentScrapingType = type;
    
    // Mostrar/ocultar filtro de fuente según el tipo
    const sourceFilterSection = document.getElementById('sourceFilterSection');
    if (sourceFilterSection) {
        // Mostrar filtro de fuente para tipos basados en fecha (excepto single que ya tiene su selector)
        if (['date', 'today', 'yesterday', 'week', 'month', 'dateRange'].includes(type)) {
            sourceFilterSection.style.display = 'block';
        } else {
            sourceFilterSection.style.display = 'none';
        }
    }
    
    // Update radio button
    const typeId = `type${type.charAt(0).toUpperCase() + type.slice(1)}`;
    const radioBtn = document.getElementById(typeId);
    if (radioBtn) {
        radioBtn.checked = true;
    }
    
    // Remove active class from all options
    document.querySelectorAll('.scraper-option').forEach(opt => {
        opt.classList.remove('active');
    });
    
    // Add active class to selected option
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
    
    // Show/hide relevant sections
    const sourceSelection = document.getElementById('sourceSelection');
    const singleSourceSelection = document.getElementById('singleSourceSelection');
    const dateSelection = document.getElementById('dateSelection');
    const dateRangeSelection = document.getElementById('dateRangeSelection');
    
    sourceSelection.style.display = (type === 'selected') ? 'block' : 'none';
    singleSourceSelection.style.display = (type === 'single') ? 'block' : 'none';
    dateSelection.style.display = (type === 'date') ? 'block' : 'none';
    dateRangeSelection.style.display = (type === 'dateRange') ? 'block' : 'none';
    
    // Set default dates
    if (type === 'today') {
        const today = new Date().toISOString().split('T')[0];
        if (dateSelection.querySelector('#scrapingDate')) {
            dateSelection.querySelector('#scrapingDate').value = today;
        }
    } else if (type === 'yesterday') {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        if (dateSelection.querySelector('#scrapingDate')) {
            dateSelection.querySelector('#scrapingDate').value = yesterdayStr;
        }
    } else if (type === 'dateRange') {
        const today = new Date().toISOString().split('T')[0];
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        const weekAgoStr = weekAgo.toISOString().split('T')[0];
        
        const startInput = document.getElementById('scrapingDateStart');
        const endInput = document.getElementById('scrapingDateEnd');
        if (startInput) startInput.value = weekAgoStr;
        if (endInput) endInput.value = today;
    }
}

/**
 * Actualizar fuentes seleccionadas
 */
function updateSelectedSources() {
    selectedSources = Array.from(document.querySelectorAll('#sourcesList input[type="checkbox"]:checked'))
        .map(cb => cb.value);
}

/**
 * Establecer fecha de hoy por defecto
 */
function setTodayAsDefault() {
    const dateInput = document.getElementById('scrapingDate');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
}

/**
 * Iniciar scraping
 */
async function startScraping() {
    if (scrapingInProgress) {
        alert('Ya hay un scraping en progreso. Por favor espera a que termine.');
        return;
    }

    // Validar selección
    if (currentScrapingType === 'selected' && selectedSources.length === 0) {
        alert('Por favor selecciona al menos una fuente.');
        return;
    }

    if (currentScrapingType === 'single') {
        const singleSource = document.getElementById('singleSourceSelect').value;
        if (!singleSource) {
            alert('Por favor selecciona una fuente.');
            return;
        }
    }

    if (currentScrapingType === 'date') {
        const date = document.getElementById('scrapingDate').value;
        if (!date) {
            alert('Por favor selecciona una fecha.');
            return;
        }
    }

    if (currentScrapingType === 'dateRange') {
        const dateStart = document.getElementById('scrapingDateStart').value;
        const dateEnd = document.getElementById('scrapingDateEnd').value;
        if (!dateStart || !dateEnd) {
            alert('Por favor selecciona ambas fechas del rango.');
            return;
        }
        if (dateStart > dateEnd) {
            alert('La fecha de inicio debe ser anterior a la fecha de fin.');
            return;
        }
    }

    // Preparar UI
    scrapingInProgress = true;
    currentJobId = null;
    const startBtn = document.getElementById('startScrapingBtn');
    const cancelBtn = document.getElementById('cancelScrapingBtn');
    
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
    cancelBtn.style.display = 'block';
    
    const progressContainer = document.getElementById('progressContainer');
    progressContainer.classList.add('active');
    
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.style.display = 'block';
    
    const logContainer = document.getElementById('logContainer');
    logContainer.style.display = 'block';
    
    clearLogs();
    clearResults();

    // Construir configuración de scraping
    const scrapingConfig = buildScrapingConfig();
    
    // Agregar log inicial
    addLog('info', '🚀 Iniciando proceso de scraping...');
    addLog('info', `📋 Configuración: ${JSON.stringify(scrapingConfig, null, 2)}`);

    try {
        // Ejecutar scraping real usando la API
        // NO restaurar UI aquí, el polling lo hará cuando termine
        await executeScraping(scrapingConfig);
    } catch (error) {
        addLog('error', `❌ Error durante el scraping: ${error.message}`);
        updateProgress(100, 'Error en el proceso');
        
        // Solo restaurar UI si hay un error que impide iniciar el scraping
        scrapingInProgress = false;
        const startBtn = document.getElementById('startScrapingBtn');
        const cancelBtn = document.getElementById('cancelScrapingBtn');
        
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Scraping';
        cancelBtn.style.display = 'none';
        
        const progressContainer = document.getElementById('progressContainer');
        progressContainer.classList.remove('active');
    }
    // NO usar finally aquí - el polling restaurará la UI cuando termine
}

/**
 * Construir configuración de scraping
 */
function buildScrapingConfig() {
    const config = {
        type: currentScrapingType,
        timestamp: new Date().toISOString()
    };

    switch (currentScrapingType) {
        case 'complete':
            config.sources = SOURCES.map(s => s.id);
            break;
        case 'selected':
            config.sources = selectedSources;
            break;
        case 'single':
            config.source = document.getElementById('singleSourceSelect').value;
            break;
        case 'date':
            config.date = document.getElementById('scrapingDate').value;
            break;
        case 'today':
            config.date = new Date().toISOString().split('T')[0];
            break;
        case 'yesterday':
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            config.date = yesterday.toISOString().split('T')[0];
            break;
        case 'week':
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            config.date_start = weekAgo.toISOString().split('T')[0];
            config.date_end = new Date().toISOString().split('T')[0];
            break;
        case 'month':
            const monthAgo = new Date();
            monthAgo.setDate(monthAgo.getDate() - 30);
            config.date_start = monthAgo.toISOString().split('T')[0];
            config.date_end = new Date().toISOString().split('T')[0];
            break;
        case 'dateRange':
            config.date_start = document.getElementById('scrapingDateStart').value;
            config.date_end = document.getElementById('scrapingDateEnd').value;
            break;
    }

    // Agregar filtros avanzados
    const limitSelect = document.getElementById('scrapingLimit');
    if (limitSelect && limitSelect.value) {
        config.limit = parseInt(limitSelect.value);
    }

    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter && categoryFilter.value) {
        config.categoria = categoryFilter.value;
    }

    // Agregar filtro de fuente para tipos basados en fecha
    if (['date', 'today', 'yesterday', 'week', 'month', 'dateRange'].includes(currentScrapingType)) {
        const sourceFilter = document.getElementById('sourceFilter');
        if (sourceFilter && sourceFilter.value) {
            // Si hay filtro de fuente, cambiar el tipo a 'single' con esa fuente
            config.source = sourceFilter.value;
            // Mantener el tipo original pero agregar source
        }
    }

    return config;
}

/**
 * Ejecutar scraping real usando la API
 */
async function executeScraping(config) {
    try {
        // Iniciar scraping en la API
        const response = await fetch(`${API_BASE_URL}/api/scrapers/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: config.type,
                sources: config.sources,
                source: config.source,
                date: config.date,
                date_start: config.date_start,
                date_end: config.date_end,
                limit: config.limit,
                categoria: config.categoria
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al iniciar scraping');
        }

        const result = await response.json();
        const jobId = result.job_id;
        currentJobId = jobId;

        addLog('info', `📊 Trabajo de scraping iniciado (ID: ${jobId})`);
        addLog('info', `📋 Procesando según configuración...`);

        // Polling para obtener estado (no esperar, se ejecuta en background)
        // El polling restaurará la UI cuando termine
        pollScrapingStatus(jobId).catch(error => {
            console.error('Error en polling:', error);
            // Si el polling falla, restaurar UI
            scrapingInProgress = false;
            const startBtn = document.getElementById('startScrapingBtn');
            const cancelBtn = document.getElementById('cancelScrapingBtn');
            
            if (startBtn) {
                startBtn.disabled = false;
                startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Scraping';
            }
            if (cancelBtn) {
                cancelBtn.style.display = 'none';
            }
            
            const progressContainer = document.getElementById('progressContainer');
            if (progressContainer) {
                progressContainer.classList.remove('active');
            }
        });

    } catch (error) {
        addLog('error', `❌ Error durante el scraping: ${error.message}`);
        updateProgress(100, 'Error en el proceso');
        
        // Restaurar UI inmediatamente si hay error al iniciar
        scrapingInProgress = false;
        currentJobId = null;
        const startBtn = document.getElementById('startScrapingBtn');
        const cancelBtn = document.getElementById('cancelScrapingBtn');
        
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Scraping';
        }
        if (cancelBtn) {
            cancelBtn.style.display = 'none';
        }
        
        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            progressContainer.classList.remove('active');
        }
        
        throw error;
    }
}

/**
 * Cancelar scraping en progreso
 */
async function cancelScraping() {
    if (!scrapingInProgress || !currentJobId) {
        return;
    }

    if (!confirm('¿Estás seguro de que deseas cancelar el scraping en progreso?')) {
        return;
    }

    try {
        // Detener polling
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }

        // Nota: La API actualmente no tiene endpoint para cancelar, pero podemos detener el polling
        addLog('warning', '⚠️  Cancelando scraping...');
        
        scrapingInProgress = false;
        currentJobId = null;

        const startBtn = document.getElementById('startScrapingBtn');
        const cancelBtn = document.getElementById('cancelScrapingBtn');
        
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Scraping';
        cancelBtn.style.display = 'none';

        const progressContainer = document.getElementById('progressContainer');
        progressContainer.classList.remove('active');

        addLog('info', '❌ Scraping cancelado por el usuario');
    } catch (error) {
        addLog('error', `Error al cancelar scraping: ${error.message}`);
    }
}

/**
 * Polling para obtener estado del scraping
 */
async function pollScrapingStatus(jobId) {
    const maxAttempts = 300; // 5 minutos máximo (1 segundo por intento)
    let attempts = 0;
    let lastLogCount = 0;

    pollingInterval = setInterval(async () => {
        attempts++;

        try {
            const response = await fetch(`${API_BASE_URL}/api/scrapers/status/${jobId}`);
            
            if (!response.ok) {
                throw new Error('Error al obtener estado del scraping');
            }

            const status = await response.json();

            // Actualizar progreso
            updateProgress(status.progress, status.current_source || 'Procesando...');

            // Agregar nuevos logs
            if (status.logs && status.logs.length > lastLogCount) {
                const newLogs = status.logs.slice(lastLogCount);
                newLogs.forEach(log => {
                    // Determinar tipo de log basado en contenido
                    let logType = 'info';
                    if (log.includes('✅') || log.includes('🎉')) {
                        logType = 'success';
                    } else if (log.includes('❌') || log.includes('Error')) {
                        logType = 'error';
                    } else if (log.includes('⚠️')) {
                        logType = 'warning';
                    }
                    addLog(logType, log);
                });
                lastLogCount = status.logs.length;
            }

            // Agregar resultados
            if (status.results && status.results.length > scrapingResults.length) {
                const newResults = status.results.slice(scrapingResults.length);
                newResults.forEach(result => {
                    addResult({
                        source: result.source,
                        status: result.status,
                        newsCount: result.newsCount || 0,
                        errors: result.status === 'error' ? 1 : 0,
                        timestamp: result.timestamp || new Date().toISOString(),
                        message: result.message
                    });
                });
            }

            // Verificar si completó
            if (status.status === 'completed' || status.status === 'error') {
                clearInterval(pollingInterval);
                pollingInterval = null;
                
                if (status.status === 'completed') {
                    updateProgress(100, 'Scraping completado');
                    addLog('success', `\n🎉 Scraping completado exitosamente!`);
                    
                    // Contar noticias procesadas
                    const successCount = status.results.filter(r => r.status === 'success').length;
                    const totalNews = status.results.reduce((sum, r) => sum + (r.inserted_count || 0), 0);
                    updateScrapingStats(successCount);
                    
                    // Mostrar notificación toast solo si se insertaron noticias
                    if (totalNews > 0) {
                        showScrapingNotification(totalNews);
                    }
                } else {
                    updateProgress(100, 'Error en el proceso');
                    addLog('error', `\n❌ Scraping finalizado con errores`);
                }
                
                // Restaurar UI
                scrapingInProgress = false;
                const startBtn = document.getElementById('startScrapingBtn');
                const cancelBtn = document.getElementById('cancelScrapingBtn');
                startBtn.disabled = false;
                startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Scraping';
                cancelBtn.style.display = 'none';
            }

            // Timeout después de maxAttempts
            if (attempts >= maxAttempts) {
                clearInterval(pollingInterval);
                pollingInterval = null;
                addLog('warning', `\n⚠️  Timeout: El scraping está tomando más tiempo del esperado`);
                
                // Restaurar UI
                scrapingInProgress = false;
                const startBtn = document.getElementById('startScrapingBtn');
                const cancelBtn = document.getElementById('cancelScrapingBtn');
                startBtn.disabled = false;
                startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Scraping';
                cancelBtn.style.display = 'none';
            }

        } catch (error) {
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
            addLog('error', `❌ Error al obtener estado: ${error.message}`);
            updateProgress(100, 'Error al obtener estado');
            
            // Restaurar UI
            scrapingInProgress = false;
            const startBtn = document.getElementById('startScrapingBtn');
            const cancelBtn = document.getElementById('cancelScrapingBtn');
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Scraping';
            cancelBtn.style.display = 'none';
        }
    }, 1000); // Poll cada segundo
}

/**
 * Obtener fuentes a procesar según configuración
 */
function getSourcesToProcess(config) {
    switch (config.type) {
        case 'complete':
            return SOURCES.map(s => s.id);
        case 'selected':
            return config.sources || [];
        case 'single':
            return [config.source];
        case 'date':
        case 'today':
            return SOURCES.map(s => s.id);
        default:
            return [];
    }
}

/**
 * Obtener nombre de fuente
 */
function getSourceName(sourceId) {
    const source = SOURCES.find(s => s.id === sourceId);
    return source ? source.name : sourceId;
}

/**
 * Agregar resultado
 */
function addResult(result) {
    // Evitar duplicados
    const existing = scrapingResults.find(r => r.source === result.source && r.timestamp === result.timestamp);
    if (existing) {
        return;
    }
    
    scrapingResults.push(result);
    
    const resultsList = document.getElementById('resultsList');
    if (!resultsList) return;
    
    const statusClass = result.status === 'success' ? 'status-success' : 
                       result.status === 'error' ? 'status-error' : 'status-pending';
    
    const statusIcon = result.status === 'success' ? 'fa-check-circle' : 
                      result.status === 'error' ? 'fa-exclamation-circle' : 'fa-clock';
    
    const message = result.message || (result.newsCount > 0 ? `${result.newsCount} noticia(s) extraída(s)` : 'Procesado');
    
    const resultHTML = `
        <div class="result-item">
            <div>
                <strong><i class="fas ${statusIcon} me-2"></i>${result.source}</strong>
                <div class="text-muted mt-1" style="font-size: 0.875rem;">
                    ${message}
                    ${result.errors > 0 ? ` • ${result.errors} error(es)` : ''}
                </div>
            </div>
            <div>
                <span class="result-status ${statusClass}">
                    <i class="fas ${statusIcon}"></i>
                    ${result.status === 'success' ? 'Completado' : 
                      result.status === 'error' ? 'Con Errores' : 'Pendiente'}
                </span>
            </div>
        </div>
    `;
    
    resultsList.innerHTML += resultHTML;
}

/**
 * Agregar log
 */
function addLog(type, message) {
    const logOutput = document.getElementById('logOutput');
    if (!logOutput) return;
    
    const logClass = `log-${type}`;
    const timestamp = new Date().toLocaleTimeString();
    
    const logHTML = `<div class="log-line ${logClass}">[${timestamp}] ${message}</div>`;
    logOutput.innerHTML += logHTML;
    
    // Auto-scroll to bottom
    logOutput.scrollTop = logOutput.scrollHeight;
}

/**
 * Actualizar progreso
 */
function updateProgress(percentage, text) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        progressBar.textContent = `${Math.round(percentage)}%`;
    }
    
    if (progressText) {
        progressText.textContent = text || 'Procesando...';
    }
}

/**
 * Limpiar resultados
 */
function clearResults() {
    scrapingResults = [];
    const resultsList = document.getElementById('resultsList');
    if (resultsList) {
        resultsList.innerHTML = '';
    }
}

/**
 * Limpiar logs
 */
function clearLogs() {
    const logOutput = document.getElementById('logOutput');
    if (logOutput) {
        logOutput.innerHTML = '';
    }
}

/**
 * Actualizar estadísticas de scraping
 */
function updateScrapingStats(newsCount) {
    const totalScraped = document.getElementById('totalScraped');
    if (totalScraped) {
        const current = parseInt(totalScraped.textContent) || 0;
        totalScraped.textContent = current + newsCount;
    }
    
    const lastScraping = document.getElementById('lastScraping');
    if (lastScraping) {
        const now = new Date();
        lastScraping.textContent = now.toLocaleTimeString();
    }
}

/**
 * Actualizar estadísticas generales
 */
async function updateStats() {
    try {
        // En producción, esto obtendría datos reales de la API
        const totalScraped = document.getElementById('totalScraped');
        if (totalScraped) {
            totalScraped.textContent = '0';
        }
    } catch (error) {
        console.error('Error actualizando estadísticas:', error);
    }
}

/**
 * Utilidad: Sleep
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Migración de datos: noticias → noticias_limpia
 */
let migrationJobId = null;
let migrationCheckInterval = null;

async function startMigration() {
    try {
        // Verificar que authManager esté disponible
        if (!window.authManager) {
            throw new Error('AuthManager no está disponible. Por favor, recarga la página.');
        }
        
        const btnStart = document.getElementById('btnStartMigration');
        const btnCheck = document.getElementById('btnCheckMigration');
        const statusDiv = document.getElementById('migrationStatus');
        
        btnStart.disabled = true;
        btnStart.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Iniciando...';
        
        const response = await window.authManager.authenticatedFetch(`${API_BASE_URL}/api/scrapers/migrate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Error al iniciar la migración');
        }
        
        const data = await response.json();
        migrationJobId = data.job_id;
        
        btnStart.style.display = 'none';
        btnCheck.style.display = 'inline-block';
        statusDiv.style.display = 'block';
        
        // Iniciar verificación periódica
        if (migrationCheckInterval) {
            clearInterval(migrationCheckInterval);
        }
        migrationCheckInterval = setInterval(checkMigrationStatus, 2000);
        
        // Verificar inmediatamente
        await checkMigrationStatus();
        
    } catch (error) {
        console.error('Error iniciando migración:', error);
        alert('Error al iniciar la migración: ' + error.message);
        document.getElementById('btnStartMigration').disabled = false;
        document.getElementById('btnStartMigration').innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Migración';
    }
}

async function checkMigrationStatus() {
    if (!migrationJobId) {
        return;
    }
    
    try {
        // Verificar que authManager esté disponible
        if (!window.authManager) {
            throw new Error('AuthManager no está disponible. Por favor, recarga la página.');
        }
        
        const response = await window.authManager.authenticatedFetch(`${API_BASE_URL}/api/scrapers/migrate/status/${migrationJobId}`);
        
        if (!response.ok) {
            throw new Error('Error al obtener el estado de la migración');
        }
        
        const data = await response.json();
        
        // Actualizar estado
        const statusText = document.getElementById('migrationStatusText');
        const progressBar = document.getElementById('migrationProgress');
        const stepText = document.getElementById('migrationStep');
        const logsDiv = document.getElementById('migrationLogs');
        const resultsDiv = document.getElementById('migrationResults');
        
        statusText.textContent = data.status === 'running' ? 'En progreso...' : 
                                 data.status === 'completed' ? 'Completado' : 
                                 data.status === 'error' ? 'Error' : data.status;
        
        progressBar.style.width = `${data.progress}%`;
        progressBar.textContent = `${Math.round(data.progress)}%`;
        
        if (data.current_step) {
            stepText.textContent = `Paso actual: ${data.current_step}`;
        } else {
            stepText.textContent = '';
        }
        
        // Actualizar logs
        if (data.logs && data.logs.length > 0) {
            logsDiv.innerHTML = data.logs.map(log => `<div>${escapeHtml(log)}</div>`).join('');
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }
        
        // Mostrar resultados si está completado
        if (data.status === 'completed' && data.results) {
            const results = data.results;
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h5><i class="fas fa-check-circle me-2"></i>Migración Completada</h5>
                    <ul class="mb-0">
                        <li><strong>Registros antes:</strong> ${results.count_before || 0}</li>
                        <li><strong>Registros nuevos insertados:</strong> ${results.new_records || 0}</li>
                        <li><strong>Registros omitidos (duplicados):</strong> ${results.total_skipped || 0}</li>
                        <li><strong>Total en noticias_limpia:</strong> ${results.total_count || 0}</li>
                    </ul>
                    ${results.fuentes ? `
                        <hr>
                        <h6>Distribución por fuente:</h6>
                        <ul class="mb-0">
                            ${Object.entries(results.fuentes).map(([fuente, cantidad]) => 
                                `<li>${escapeHtml(fuente)}: ${cantidad}</li>`
                            ).join('')}
                        </ul>
                    ` : ''}
                </div>
            `;
            
            // Detener verificación periódica
            if (migrationCheckInterval) {
                clearInterval(migrationCheckInterval);
                migrationCheckInterval = null;
            }
            
            // Restaurar botón
            document.getElementById('btnStartMigration').style.display = 'inline-block';
            document.getElementById('btnStartMigration').disabled = false;
            document.getElementById('btnStartMigration').innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Migración';
            document.getElementById('btnCheckMigration').style.display = 'none';
        } else if (data.status === 'error') {
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h5><i class="fas fa-exclamation-circle me-2"></i>Error en la Migración</h5>
                    <p>Revisa los logs para más detalles.</p>
                </div>
            `;
            
            // Detener verificación periódica
            if (migrationCheckInterval) {
                clearInterval(migrationCheckInterval);
                migrationCheckInterval = null;
            }
            
            // Restaurar botón
            document.getElementById('btnStartMigration').style.display = 'inline-block';
            document.getElementById('btnStartMigration').disabled = false;
            document.getElementById('btnStartMigration').innerHTML = '<i class="fas fa-play me-2"></i>Iniciar Migración';
            document.getElementById('btnCheckMigration').style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error verificando estado de migración:', error);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Hacer funciones disponibles globalmente
window.selectScrapingType = selectScrapingType;
window.updateSelectedSources = updateSelectedSources;
window.startScraping = startScraping;
window.cancelScraping = cancelScraping;
window.clearResults = clearResults;
window.clearLogs = clearLogs;
window.startMigration = startMigration;
window.checkMigrationStatus = checkMigrationStatus;

/**
 * Mostrar notificación después del scraping
 */
function showScrapingNotification(totalNews) {
    try {
        const toastElement = document.getElementById('notificationToast');
        const toastMessage = document.getElementById('toastMessage');
        
        if (!toastElement || !toastMessage) {
            console.warn('Toast elements not found');
            return;
        }
        
        // Configurar mensaje
        toastMessage.textContent = `✅ Scraping completado: ${totalNews} noticia(s) extraída(s). ¿Deseas migrar los datos a noticias_limpia?`;
        
        // Remover listeners anteriores si existen (usando una función nombrada para poder removerla)
        const clickHandler = function(e) {
            // No redirigir si se hace clic en el botón de cerrar
            if (e.target.classList.contains('btn-close') || e.target.closest('.btn-close')) {
                return;
            }
            
            // Hacer scroll a la sección de migración
            const migrationSection = document.querySelector('#btnStartMigration')?.closest('.scraper-card');
            if (migrationSection) {
                migrationSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Resaltar la sección brevemente
                migrationSection.style.transition = 'background-color 0.3s';
                migrationSection.style.backgroundColor = '#e7f3ff';
                setTimeout(() => {
                    migrationSection.style.backgroundColor = '';
                }, 2000);
            }
            
            // Cerrar el toast
            const toastInstance = bootstrap.Toast.getInstance(toastElement);
            if (toastInstance) {
                toastInstance.hide();
            }
            
            // Remover el listener después de usarlo
            toastElement.removeEventListener('click', clickHandler);
        };
        
        // Remover listener anterior si existe
        toastElement.removeEventListener('click', clickHandler);
        
        // Hacer el toast clickeable para redirigir a la sección de migración
        toastElement.style.cursor = 'pointer';
        toastMessage.style.cursor = 'pointer';
        toastElement.addEventListener('click', clickHandler);
        
        // Mostrar el toast
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 8000 // 8 segundos
        });
        toast.show();
        
    } catch (error) {
        console.error('Error mostrando notificación:', error);
    }
}

