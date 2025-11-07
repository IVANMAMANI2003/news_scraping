/**
 * BizNews Main JavaScript - Estilo Profesional
 * Versión 2.0.0
 * 
 * @author BizNews Team
 * @description JavaScript principal para funcionalidades comunes de BizNews
 */

(function ($) {
    "use strict";
    
    // ============================================
    // INICIALIZACIÓN
    // ============================================
    
    $(document).ready(function () {
        initializeComponents();
        initializeCarousels();
        initializeScrollEffects();
        initializeTooltips();
        initializeModals();
        initializeForms();
    });
    
    // ============================================
    // COMPONENTES PRINCIPALES
    // ============================================
    
    function initializeComponents() {
        // Dropdown on mouse hover (solo en desktop)
        function toggleNavbarMethod() {
            if ($(window).width() > 992) {
                $('.navbar .dropdown').on('mouseover', function () {
                    $('.dropdown-toggle', this).trigger('click');
                }).on('mouseout', function () {
                    $('.dropdown-toggle', this).trigger('click').blur();
                });
            } else {
                $('.navbar .dropdown').off('mouseover').off('mouseout');
            }
        }
        
        toggleNavbarMethod();
        $(window).resize(toggleNavbarMethod);
        
        // Inicializar tooltips de Bootstrap
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Inicializar popovers de Bootstrap
        var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // ============================================
    // CARRUSELES
    // ============================================
    
    function initializeCarousels() {
        // Carrusel principal
    $(".main-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        items: 1,
        dots: true,
        loop: true,
        center: true,
            nav: true,
            navText: [
                '<i class="fas fa-chevron-left"></i>',
                '<i class="fas fa-chevron-right"></i>'
            ],
            responsive: {
                0: {
                    items: 1,
                    nav: false
                },
                768: {
                    items: 1,
                    nav: true
                }
            }
        });
        
        // Carrusel de tendencias
        $(".trending-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 2000,
        items: 1,
        dots: false,
        loop: true,
            nav: true,
            navText: [
                '<i class="fas fa-chevron-left"></i>',
                '<i class="fas fa-chevron-right"></i>'
            ],
            responsive: {
                0: {
                    items: 1,
                    nav: false
                },
                768: {
        items: 1,
                    nav: true
                }
            }
        });
        
        // Carrusel de noticias pequeñas
        $(".small-news-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
            margin: 20,
        dots: false,
        loop: true,
            nav: true,
            navText: [
                '<i class="fas fa-chevron-left"></i>',
                '<i class="fas fa-chevron-right"></i>'
        ],
        responsive: {
                0: {
                    items: 1,
                    nav: false
                },
                576: {
                    items: 1,
                    nav: true
                },
                768: {
                    items: 2,
                    nav: true
                },
                992: {
                    items: 3,
                    nav: true
                }
            }
        });
        
        // Carrusel de noticias destacadas
        $(".featured-news-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1000,
        margin: 30,
        dots: false,
        loop: true,
            nav: true,
            navText: [
                '<i class="fas fa-chevron-left"></i>',
                '<i class="fas fa-chevron-right"></i>'
        ],
        responsive: {
                0: {
                    items: 1,
                    nav: false
                },
                576: {
                    items: 1,
                    nav: true
                },
                768: {
                    items: 2,
                    nav: true
                },
                992: {
                    items: 3,
                    nav: true
                },
                1200: {
                    items: 4,
                    nav: true
                }
            }
        });
    }
    
    // ============================================
    // EFECTOS DE SCROLL
    // ============================================
    
    function initializeScrollEffects() {
        // Botón de volver arriba
        $(window).scroll(function () {
            if ($(this).scrollTop() > 100) {
                $('.back-to-top').fadeIn('slow');
            } else {
                $('.back-to-top').fadeOut('slow');
            }
        });
        
        $('.back-to-top').click(function () {
            $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
            return false;
        });
        
        // Animaciones de scroll
        $(window).scroll(function () {
            $('.animate-on-scroll').each(function () {
                var elementTop = $(this).offset().top;
                var elementBottom = elementTop + $(this).outerHeight();
                var viewportTop = $(window).scrollTop();
                var viewportBottom = viewportTop + $(window).height();
                
                if (elementBottom > viewportTop && elementTop < viewportBottom) {
                    $(this).addClass('animated');
                }
            });
        });
        
        // Smooth scroll para enlaces internos
        $('a[href*="#"]:not([href="#"])').click(function () {
            if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
                var target = $(this.hash);
                target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
                if (target.length) {
                    $('html, body').animate({
                        scrollTop: target.offset().top - 80
                    }, 1000);
                    return false;
                }
            }
        });
    }
    
    // ============================================
    // TOOLTIPS Y POPOVERS
    // ============================================
    
    function initializeTooltips() {
        // Tooltips personalizados
        $('[data-toggle="tooltip"]').tooltip({
            trigger: 'hover',
            placement: 'top',
            container: 'body'
        });
        
        // Popovers personalizados
        $('[data-toggle="popover"]').popover({
            trigger: 'hover',
            placement: 'top',
            container: 'body'
        });
    }
    
    // ============================================
    // MODALES
    // ============================================
    
    function initializeModals() {
        // Modal de noticias
        $('.news-modal-trigger').click(function (e) {
            e.preventDefault();
            var newsId = $(this).data('news-id');
            var modal = $('#newsModal');
            
            if (newsId) {
                loadNewsModal(newsId, modal);
            }
        });
        
        // Cerrar modal al hacer clic fuera
        $(document).click(function (e) {
            if ($(e.target).hasClass('modal-overlay')) {
                $('.modal-overlay').fadeOut();
            }
        });
        
        // Cerrar modal con tecla Escape
        $(document).keyup(function (e) {
            if (e.keyCode === 27) {
                $('.modal-overlay').fadeOut();
            }
        });
    }
    
    // ============================================
    // FORMULARIOS
    // ============================================
    
    function initializeForms() {
        // Validación de formularios
        $('form').on('submit', function (e) {
            var form = $(this);
            var isValid = true;
            
            // Validar campos requeridos
            form.find('[required]').each(function () {
                if (!$(this).val()) {
                    $(this).addClass('is-invalid');
                    isValid = false;
                } else {
                    $(this).removeClass('is-invalid');
                }
            });
            
            // Validar email
            form.find('input[type="email"]').each(function () {
                var email = $(this).val();
                var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (email && !emailRegex.test(email)) {
                    $(this).addClass('is-invalid');
                    isValid = false;
                } else {
                    $(this).removeClass('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Por favor, complete todos los campos requeridos correctamente.', 'error');
            }
        });
        
        // Limpiar validación al escribir
        $('input, textarea, select').on('input change', function () {
            $(this).removeClass('is-invalid');
        });
    }
    
    // ============================================
    // FUNCIONES AUXILIARES
    // ============================================
    
    function loadNewsModal(newsId, modal) {
        // Mostrar loading
        modal.find('.modal-body').html('<div class="text-center p-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div></div>');
        modal.show();
        
        // Simular carga de datos (aquí iría la llamada a la API)
        setTimeout(function () {
            modal.find('.modal-body').html('<p>Contenido de la noticia con ID: ' + newsId + '</p>');
        }, 1000);
    }
    
    function showNotification(message, type) {
        var notification = $('<div class="notification ' + type + '">' + message + '</div>');
        $('body').append(notification);
        
        setTimeout(function () {
            notification.fadeOut(function () {
                notification.remove();
            });
        }, 5000);
    }
    
    // ============================================
    // FILTROS Y BÚSQUEDA
    // ============================================
    
    // Filtros de tiempo
    $('.time-filter-btn').click(function () {
        $('.time-filter-btn').removeClass('active');
        $(this).addClass('active');
        
        var filter = $(this).data('filter');
        applyTimeFilter(filter);
    });
    
    function applyTimeFilter(filter) {
        // Aquí iría la lógica para aplicar el filtro de tiempo
        console.log('Aplicando filtro de tiempo:', filter);
    }
    
    // Filtros de categoría
    $('.category-filter-btn').click(function () {
        $('.category-filter-btn').removeClass('active');
        $(this).addClass('active');
        
        var category = $(this).data('category');
        applyCategoryFilter(category);
    });
    
    function applyCategoryFilter(category) {
        // Aquí iría la lógica para aplicar el filtro de categoría
        console.log('Aplicando filtro de categoría:', category);
    }
    
    // ============================================
    // EFECTOS VISUALES
    // ============================================
    
    // Efecto de hover en cards
    $('.news-card').hover(
        function () {
            $(this).addClass('hover-lift');
        },
        function () {
            $(this).removeClass('hover-lift');
        }
    );
    
    // Efecto de hover en botones
    $('.btn').hover(
        function () {
            $(this).addClass('hover-lift');
        },
        function () {
            $(this).removeClass('hover-lift');
        }
    );
    
    // ============================================
    // UTILIDADES
    // ============================================
    
    // Función para formatear fechas
    function formatDate(dateString) {
        var date = new Date(dateString);
        var options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleDateString('es-ES', options);
    }
    
    // Función para truncar texto
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }
    
    // Función para limpiar HTML
    function cleanHtml(html) {
        var temp = document.createElement('div');
        temp.innerHTML = html;
        return temp.textContent || temp.innerText || '';
    }
    
    // ============================================
    // EVENTOS GLOBALES
    // ============================================
    
    // Prevenir envío de formularios vacíos
    $('form').on('submit', function (e) {
        var form = $(this);
        var hasContent = false;
        
        form.find('input, textarea, select').each(function () {
            if ($(this).val()) {
                hasContent = true;
                return false;
            }
        });
        
        if (!hasContent) {
            e.preventDefault();
            showNotification('Por favor, complete al menos un campo del formulario.', 'warning');
        }
    });
    
    // Manejar errores de AJAX
    $(document).ajaxError(function (event, xhr, settings, thrownError) {
        console.error('Error AJAX:', thrownError);
        showNotification('Error al cargar los datos. Por favor, intente nuevamente.', 'error');
    });
    
    // ============================================
    // INICIALIZACIÓN DE COMPONENTES ESPECÍFICOS
    // ============================================
    
    // Inicializar componentes cuando se carga el DOM
    $(document).ready(function () {
        // Inicializar tooltips
        $('[data-bs-toggle="tooltip"]').tooltip();
        
        // Inicializar popovers
        $('[data-bs-toggle="popover"]').popover();
        
        // Inicializar modales
        $('.modal').modal({
            backdrop: 'static',
            keyboard: false
        });
        
        // Inicializar dropdowns
        $('.dropdown-toggle').dropdown();
        
        // Inicializar collapse
        $('.collapse').collapse();
    });
    
    // ============================================
    // FUNCIONES PÚBLICAS
    // ============================================
    
    // Exponer funciones globales
    window.BizNews = {
        showNotification: showNotification,
        formatDate: formatDate,
        truncateText: truncateText,
        cleanHtml: cleanHtml,
        applyTimeFilter: applyTimeFilter,
        applyCategoryFilter: applyCategoryFilter
    };
    
})(jQuery);

// ============================================
// FUNCIONES GLOBALES
// ============================================

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    if (window.BizNews && window.BizNews.showNotification) {
        window.BizNews.showNotification(message, type);
    } else {
        console.log('BizNews not initialized');
    }
}

// Función para formatear fechas
function formatDate(dateString) {
    if (window.BizNews && window.BizNews.formatDate) {
        return window.BizNews.formatDate(dateString);
    } else {
        return new Date(dateString).toLocaleDateString('es-ES');
    }
}

// Función para truncar texto
function truncateText(text, maxLength) {
    if (window.BizNews && window.BizNews.truncateText) {
        return window.BizNews.truncateText(text, maxLength);
    } else {
        return text.length <= maxLength ? text : text.substr(0, maxLength) + '...';
    }
}

// Función para limpiar HTML
function cleanHtml(html) {
    if (window.BizNews && window.BizNews.cleanHtml) {
        return window.BizNews.cleanHtml(html);
    } else {
        var temp = document.createElement('div');
        temp.innerHTML = html;
        return temp.textContent || temp.innerText || '';
    }
}