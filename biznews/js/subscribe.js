/**
 * Sistema de Suscripción - BizNews
 * Maneja el registro de usuarios desde la página de servicios
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// Nombres de planes
const PLAN_NAMES = {
    'free': 'FREE - Starter',
    'pro': 'PRO - Profesional',
    'business': 'BUSINESS - Corporativo',
    'enterprise': 'ENTERPRISE - A la Medida'
};

let selectedPlan = null;
let currentStep = 1; // 1 = user info, 2 = payment
let selectedPaymentMethod = null;

// Precios de los planes
const PLAN_PRICES = {
    'free': 0,
    'pro': 5,
    'business': 10,
    'enterprise': 20
};

/**
 * Abrir modal de suscripción
 */
function openSubscribeModal(plan) {
    try {
        selectedPlan = plan;
        currentStep = 1;
        selectedPaymentMethod = null;
        
        // Verificar que los elementos existan
        const selectedPlanInput = document.getElementById('selectedPlan');
        const selectedPlanName = document.getElementById('selectedPlanName');
        const planDisplayName = document.getElementById('planDisplayName');
        const subscribeForm = document.getElementById('subscribeForm');
        const subscribeError = document.getElementById('subscribeError');
        const modalElement = document.getElementById('subscribeModal');
        
        if (!modalElement) {
            console.error('Modal subscribeModal no encontrado');
            alert('Error: No se pudo abrir el modal. Por favor, recarga la página.');
            return;
        }
        
        // Actualizar el modal con la información del plan
        if (selectedPlanInput) selectedPlanInput.value = plan;
        if (selectedPlanName) selectedPlanName.textContent = PLAN_NAMES[plan] || plan.toUpperCase();
        if (planDisplayName) planDisplayName.textContent = PLAN_NAMES[plan] || plan.toUpperCase();
        
        // Limpiar formulario
        if (subscribeForm) subscribeForm.reset();
        if (subscribeError) {
            subscribeError.classList.add('d-none');
            subscribeError.textContent = '';
        }
        
        // Resetear pasos
        resetSteps();
        
        // Limpiar cualquier backdrop residual antes de mostrar
        const existingBackdrops = document.querySelectorAll('.modal-backdrop');
        existingBackdrops.forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // Mostrar modal - intentar con bootstrap 5
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            console.log('✅ Bootstrap disponible, creando modal...');
            
            // Asegurar que el modal no tenga aria-hidden cuando se muestre
            modalElement.setAttribute('aria-hidden', 'false');
            
            const modal = new bootstrap.Modal(modalElement, {
                backdrop: true,
                keyboard: true
            });
            
            // Guardar referencia del modal para poder cerrarlo correctamente
            window.currentModal = modal;
            
            // Configurar listeners cuando el modal se muestre completamente
            const onModalShown = function() {
                console.log('🎯 EVENTO: Modal mostrado (shown.bs.modal)');
                
                // Asegurar que aria-hidden esté correcto
                modalElement.removeAttribute('aria-hidden');
                
                // Configurar listeners de botones
                setupButtonListener();
                setupCardFormatting();
                
                console.log('✅ Modal listo para suscripción');
            };
            
            modalElement.addEventListener('shown.bs.modal', onModalShown, { once: true });
            console.log('✅ Event listener para shown.bs.modal agregado');
            
            // Configurar listeners para cuando el modal se cierre
            const onModalHidden = function() {
                console.log('🔒 Modal cerrado, limpiando...');
                
                // Pequeño delay para asegurar que Bootstrap termine su limpieza
                setTimeout(() => {
                    // Limpiar backdrop si queda
                    const backdrops = document.querySelectorAll('.modal-backdrop');
                    backdrops.forEach(backdrop => {
                        console.log('🧹 Eliminando backdrop');
                        backdrop.remove();
                    });
                    
                    // Limpiar clases del body
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                    
                    // Restablecer aria-hidden
                    modalElement.setAttribute('aria-hidden', 'true');
                    modalElement.classList.remove('show');
                    modalElement.style.display = 'none';
                    
                    // Limpiar referencia
                    window.currentModal = null;
                }, 100);
            };
            
            modalElement.addEventListener('hidden.bs.modal', onModalHidden, { once: true });
            
            // También agregar listener al botón cancelar directamente
            const cancelBtn = document.getElementById('cancelBtn');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', function(e) {
                    console.log('🔒 Botón Cancelar clickeado');
                    // El data-bs-dismiss="modal" de Bootstrap se encargará del cierre
                    // Pero también limpiamos manualmente por si acaso
                    setTimeout(() => {
                        onModalHidden();
                    }, 200);
                });
            }
            
            console.log('🚀 Mostrando modal...');
            modal.show();
            
            // Asegurar que aria-hidden se quite después de mostrar
            setTimeout(() => {
                modalElement.removeAttribute('aria-hidden');
            }, 100);
        } else if (typeof $ !== 'undefined' && $.fn.modal) {
            // Fallback para jQuery Bootstrap (versiones antiguas)
            $(modalElement).on('shown.bs.modal', function() {
                setupCardFormatting();
                setupButtonListener();
            });
            $(modalElement).modal('show');
        } else {
            console.error('Bootstrap no está cargado');
            // Intentar mostrar el modal manualmente
            modalElement.style.display = 'block';
            modalElement.classList.add('show');
            document.body.classList.add('modal-open');
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = 'modalBackdrop';
            document.body.appendChild(backdrop);
            
            // Configurar listeners después de mostrar manualmente
            setTimeout(() => {
                setupCardFormatting();
                setupButtonListener();
            }, 100);
            
            alert('Error: Bootstrap no está cargado correctamente. Por favor, recarga la página.');
        }
    } catch (error) {
        console.error('Error al abrir modal:', error);
        alert('Error al abrir el modal de suscripción. Por favor, intenta nuevamente.');
    }
}

/**
 * Resetear pasos del modal
 */
function resetSteps() {
    currentStep = 1;
    selectedPaymentMethod = null;
    
    // Mostrar paso 1, ocultar paso 2 con animación
    const stepUserInfo = document.getElementById('stepUserInfo');
    const stepPayment = document.getElementById('stepPayment');
    
    stepUserInfo.classList.add('active');
    stepUserInfo.classList.remove('prev');
    stepPayment.classList.remove('active');
    stepPayment.classList.add('prev');
    
    // Botones
    document.getElementById('backBtn').classList.add('d-none');
    document.getElementById('nextBtn').classList.remove('d-none');
    document.getElementById('payBtn').classList.add('d-none');
    
    // Actualizar indicadores de progreso
    updateProgressIndicator(1);
    
    // Limpiar selección de método de pago
    document.querySelectorAll('.payment-method-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Ocultar formularios de pago
    document.getElementById('paymentFormContainer').classList.add('d-none');
    document.querySelectorAll('.payment-form').forEach(form => {
        form.classList.add('d-none');
    });
}

/**
 * Actualizar indicador de progreso
 */
function updateProgressIndicator(step) {
    const step1Indicator = document.getElementById('step1Indicator');
    const step2Indicator = document.getElementById('step2Indicator');
    const progressLine = document.getElementById('progressLine');
    const modalIcon = document.getElementById('modalIcon');
    const modalTitleText = document.getElementById('modalTitleText');
    
    if (step === 1) {
        step1Indicator.classList.add('active');
        step1Indicator.classList.remove('completed');
        step2Indicator.classList.remove('active', 'completed');
        progressLine.classList.remove('completed');
        
        if (modalIcon) modalIcon.className = 'fas fa-user-plus me-2';
        if (modalTitleText) {
            const planName = PLAN_NAMES[selectedPlan] || selectedPlan.toUpperCase();
            modalTitleText.innerHTML = `Suscribirse al Plan <span id="selectedPlanName">${planName}</span>`;
        }
    } else if (step === 2) {
        step1Indicator.classList.remove('active');
        step1Indicator.classList.add('completed');
        step2Indicator.classList.add('active');
        step2Indicator.classList.remove('completed');
        progressLine.classList.add('completed');
        
        if (modalIcon) modalIcon.className = 'fas fa-credit-card me-2';
        if (modalTitleText) {
            const planName = PLAN_NAMES[selectedPlan] || selectedPlan.toUpperCase();
            modalTitleText.innerHTML = `Método de Pago - ${planName}`;
        }
    }
}

/**
 * Manejar el botón "Continuar" - determina si avanzar a pago o procesar directamente
 */
function handleNextButton() {
    console.log('🎯🎯🎯 handleNextButton LLAMADO');
    console.log('   - currentStep:', currentStep);
    console.log('   - selectedPlan:', selectedPlan);
    
    try {
        if (currentStep === 1) {
            console.log('✅ Paso 1 detectado, llamando a nextStep()...');
            const result = nextStep();
            console.log('✅ nextStep() ejecutado, resultado:', result);
        } else {
            console.log('✅ Paso 2 detectado, llamando a processPayment()...');
            processPayment();
        }
    } catch (error) {
        console.error('❌ Error en handleNextButton:', error);
        console.error('Stack trace:', error.stack);
        alert('Error al procesar: ' + error.message);
    }
}

/**
 * Avanzar al siguiente paso
 */
function nextStep() {
    console.log('🚀 nextStep llamado, currentStep:', currentStep);
    
    if (currentStep === 1) {
        console.log('📋 Validando formulario...');
        
        // Validar formulario de usuario
        const form = document.getElementById('subscribeForm');
        if (!form) {
            console.error('❌ Formulario no encontrado');
            alert('Error: No se encontró el formulario. Por favor, recarga la página.');
            return false;
        }
        
        if (!form.checkValidity()) {
            console.log('⚠️ Formulario inválido');
            form.reportValidity();
            return false;
        }
        
        const password = document.getElementById('subscribePassword').value;
        const passwordConfirm = document.getElementById('subscribePasswordConfirm').value;
        
        if (password !== passwordConfirm) {
            console.log('⚠️ Contraseñas no coinciden');
            const errorDiv = document.getElementById('subscribeError');
            if (errorDiv) {
                errorDiv.textContent = 'Las contraseñas no coinciden';
                errorDiv.classList.remove('d-none');
            }
            return false;
        }
        
        if (password.length < 6) {
            console.log('⚠️ Contraseña muy corta');
            const errorDiv = document.getElementById('subscribeError');
            if (errorDiv) {
                errorDiv.textContent = 'La contraseña debe tener al menos 6 caracteres';
                errorDiv.classList.remove('d-none');
            }
            return false;
        }
        
        // Si el plan es free, saltar el paso de pago y registrar directamente
        if (selectedPlan === 'free') {
            console.log('🆓 Plan FREE detectado, saltando pago y registrando directamente');
            // Ir directamente al registro sin pasar por pago
            submitSubscription();
            return true;
        }
        
        console.log('💳 Avanzando al paso de pago para plan:', selectedPlan);
        
        // Avanzar al paso de pago para planes de pago
        currentStep = 2;
        
        const stepUserInfo = document.getElementById('stepUserInfo');
        const stepPayment = document.getElementById('stepPayment');
        const backBtn = document.getElementById('backBtn');
        const nextBtn = document.getElementById('nextBtn');
        const payBtn = document.getElementById('payBtn');
        
        console.log('🔍 Buscando elementos del DOM...');
        console.log('   - stepUserInfo:', stepUserInfo ? '✅' : '❌');
        console.log('   - stepPayment:', stepPayment ? '✅' : '❌');
        console.log('   - backBtn:', backBtn ? '✅' : '❌');
        console.log('   - nextBtn:', nextBtn ? '✅' : '❌');
        console.log('   - payBtn:', payBtn ? '✅' : '❌');
        
        if (!stepUserInfo || !stepPayment || !backBtn || !nextBtn || !payBtn) {
            console.error('❌ Elementos del DOM no encontrados');
            alert('Error: No se encontraron los elementos necesarios. Por favor, recarga la página.');
            return false;
        }
        
        console.log('✅ Todos los elementos encontrados, aplicando cambios...');
        
        // Animación de transición entre páginas
        stepUserInfo.classList.remove('active');
        stepUserInfo.classList.add('prev');
        console.log('   - stepUserInfo: active removido, prev agregado');
        
        // Pequeño delay para la animación
        setTimeout(() => {
            stepPayment.classList.remove('prev');
            stepPayment.classList.add('active');
            console.log('   - stepPayment: prev removido, active agregado');
        }, 50);
        
        backBtn.classList.remove('d-none');
        nextBtn.classList.add('d-none');
        payBtn.classList.remove('d-none');
        console.log('   - Botones actualizados');
        
        // Actualizar indicador de progreso
        updateProgressIndicator(2);
        console.log('   - Indicador de progreso actualizado');
        
        // Configurar event listeners para métodos de pago
        setupPaymentMethodListeners();
        console.log('   - Listeners de métodos de pago configurados');
        
        console.log('✅✅✅ Paso de pago mostrado correctamente');
        return true;
    }
    
    return false;
}

/**
 * Volver al paso anterior
 */
function goBackToUserInfo() {
    currentStep = 1;
    
    const stepUserInfo = document.getElementById('stepUserInfo');
    const stepPayment = document.getElementById('stepPayment');
    
    // Animación de transición hacia atrás
    stepPayment.classList.remove('active');
    stepPayment.classList.add('prev');
    
    setTimeout(() => {
        stepUserInfo.classList.remove('prev');
        stepUserInfo.classList.add('active');
    }, 50);
    
    document.getElementById('backBtn').classList.add('d-none');
    document.getElementById('nextBtn').classList.remove('d-none');
    document.getElementById('payBtn').classList.add('d-none');
    selectedPaymentMethod = null;
    
    // Actualizar indicador de progreso
    updateProgressIndicator(1);
}

/**
 * Configurar listeners para métodos de pago
 */
function setupPaymentMethodListeners() {
    // Remover listeners anteriores si existen
    document.querySelectorAll('.payment-method-card').forEach(card => {
        const newCard = card.cloneNode(true);
        card.parentNode.replaceChild(newCard, card);
    });
    
    // Agregar listeners a los nuevos elementos
    document.querySelectorAll('.payment-method-card').forEach(card => {
        card.addEventListener('click', function() {
            console.log('💳 Método de pago seleccionado:', this.dataset.method);
            
            // Remover selección anterior
            document.querySelectorAll('.payment-method-card').forEach(c => {
                c.classList.remove('selected');
            });
            
            // Seleccionar este método
            this.classList.add('selected');
            selectedPaymentMethod = this.dataset.method;
            
            // Mostrar formulario correspondiente
            const paymentFormContainer = document.getElementById('paymentFormContainer');
            if (paymentFormContainer) {
                paymentFormContainer.classList.remove('d-none');
            }
            
            document.querySelectorAll('.payment-form').forEach(form => {
                form.classList.add('d-none');
            });
            
            if (selectedPaymentMethod === 'card') {
                const cardForm = document.getElementById('cardPaymentForm');
                if (cardForm) cardForm.classList.remove('d-none');
            } else if (selectedPaymentMethod === 'paypal') {
                const paypalForm = document.getElementById('paypalPaymentForm');
                if (paypalForm) paypalForm.classList.remove('d-none');
            } else if (selectedPaymentMethod === 'transfer') {
                const transferForm = document.getElementById('transferPaymentForm');
                if (transferForm) transferForm.classList.remove('d-none');
            } else if (selectedPaymentMethod === 'crypto') {
                const cryptoForm = document.getElementById('cryptoPaymentForm');
                if (cryptoForm) cryptoForm.classList.remove('d-none');
            }
        });
    });
    
    console.log('✅ Listeners de métodos de pago configurados');
}

/**
 * Procesar pago (simulado)
 */
async function processPayment() {
    console.log('💳 processPayment llamado');
    console.log('   - selectedPaymentMethod:', selectedPaymentMethod);
    
    if (!selectedPaymentMethod) {
        alert('Por favor, selecciona un método de pago');
        return;
    }
    
    // Validar formulario de tarjeta si es necesario
    if (selectedPaymentMethod === 'card') {
        const cardNumber = document.getElementById('cardNumber')?.value;
        const cardExpiry = document.getElementById('cardExpiry')?.value;
        const cardCVV = document.getElementById('cardCVV')?.value;
        const cardName = document.getElementById('cardName')?.value;
        
        if (!cardNumber || !cardExpiry || !cardCVV || !cardName) {
            alert('Por favor, completa todos los campos de la tarjeta');
            return;
        }
        
        // Validación básica de formato
        if (cardNumber.replace(/\s/g, '').length < 13) {
            alert('El número de tarjeta no es válido (mínimo 13 dígitos)');
            return;
        }
        
        if (!/^\d{2}\/\d{2}$/.test(cardExpiry)) {
            alert('La fecha de vencimiento debe tener el formato MM/AA');
            return;
        }
        
        if (cardCVV.length < 3) {
            alert('El CVV debe tener al menos 3 dígitos');
            return;
        }
        
        console.log('✅ Validación de tarjeta pasada');
    } else {
        // Para otros métodos (PayPal, transferencia, crypto), no se requiere validación
        console.log('✅ Método de pago seleccionado:', selectedPaymentMethod);
    }
    
    const payBtn = document.getElementById('payBtn');
    if (!payBtn) {
        console.error('❌ Botón payBtn no encontrado');
        alert('Error: No se encontró el botón de pago');
        return;
    }
    
    const originalHTML = payBtn.innerHTML;
    payBtn.disabled = true;
    payBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando pago...';
    
    console.log('⏳ Simulando procesamiento de pago...');
    
    // Simular procesamiento de pago (2-3 segundos)
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 1000));
    
    console.log('✅ Pago simulado exitoso');
    
    // Simular éxito del pago (siempre exitoso en demo)
    payBtn.innerHTML = '<i class="fas fa-check me-2"></i>Pago Exitoso!';
    payBtn.classList.remove('btn-success');
    payBtn.classList.add('btn-success');
    
    // Esperar un momento y proceder con el registro
    await new Promise(resolve => setTimeout(resolve, 800));
    
    console.log('📝 Procediendo con el registro...');
    
    // Proceder con el registro
    await submitSubscription();
}

/**
 * Copiar dirección de criptomoneda
 */
function copyCryptoAddress() {
    const address = document.getElementById('cryptoAddress').textContent;
    navigator.clipboard.writeText(address).then(() => {
        const btn = event.target.closest('button');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i>';
        btn.classList.remove('btn-outline-primary');
        btn.classList.add('btn-success');
        
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('btn-success');
            btn.classList.add('btn-outline-primary');
        }, 2000);
    }).catch(err => {
        console.error('Error copiando:', err);
        alert('No se pudo copiar al portapapeles');
    });
}

/**
 * Enviar suscripción
 */
async function submitSubscription() {
    console.log('🚀 submitSubscription llamado');
    
    const form = document.getElementById('subscribeForm');
    const errorDiv = document.getElementById('subscribeError');
    const nextBtn = document.getElementById('nextBtn');
    
    // Validar formulario
    if (!form) {
        console.error('Formulario no encontrado');
        alert('Error: No se encontró el formulario');
        return;
    }
    
    if (!form.checkValidity()) {
        console.log('Formulario inválido');
        form.reportValidity();
        return;
    }
    
    // Obtener datos del formulario
    const email = document.getElementById('subscribeEmail').value;
    const nombre = document.getElementById('subscribeNombre').value;
    const apellido = document.getElementById('subscribeApellido').value;
    const password = document.getElementById('subscribePassword').value;
    const passwordConfirm = document.getElementById('subscribePasswordConfirm').value;
    const plan = document.getElementById('selectedPlan').value;
    
    console.log('Datos del formulario:', { email, nombre, plan });
    
    // Validar contraseñas
    if (password !== passwordConfirm) {
        errorDiv.textContent = 'Las contraseñas no coinciden';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    if (password.length < 6) {
        errorDiv.textContent = 'La contraseña debe tener al menos 6 caracteres';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    // Deshabilitar botón
    if (nextBtn) {
        nextBtn.disabled = true;
        nextBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
    }
    errorDiv.classList.add('d-none');
    
    try {
        // Registrar usuario
        const registerResponse = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                nombre: nombre,
                apellido: apellido,
                password: password,
                plan: plan
            })
        });
        
        if (!registerResponse.ok) {
            const errorData = await registerResponse.json();
            throw new Error(errorData.detail || 'Error al registrar usuario');
        }
        
        const userData = await registerResponse.json();
        
        // Iniciar sesión automáticamente
        const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        if (!loginResponse.ok) {
            throw new Error('Usuario registrado pero no se pudo iniciar sesión automáticamente');
        }
        
        const loginData = await loginResponse.json();
        
        // Guardar sesión
        const session = {
            access_token: loginData.access_token,
            refresh_token: loginData.refresh_token,
            user: loginData.user,
            loginTime: new Date().getTime(),
            expiresAt: new Date().getTime() + (loginData.expires_in * 1000),
            rememberMe: true
        };
        localStorage.setItem('biznews_admin_session', JSON.stringify(session));
        
        // Verificar que el token funciona correctamente haciendo una petición autenticada
        console.log('Verificando sesión con el servidor...');
        const verifyResponse = await fetch(`${API_BASE_URL}/auth/me`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${loginData.access_token}`
            }
        });
        
        if (!verifyResponse.ok) {
            throw new Error('Error al verificar la sesión. Por favor, intenta iniciar sesión manualmente.');
        }
        
        const verifiedUser = await verifyResponse.json();
        console.log('Sesión verificada correctamente:', verifiedUser);
        
        // Actualizar la sesión con los datos verificados
        session.user = verifiedUser;
        localStorage.setItem('biznews_admin_session', JSON.stringify(session));
        
        // Crear API Key automáticamente
        let apiKey = null;
        try {
            console.log('🔑 Creando API Key automáticamente...');
            console.log('   - Usuario ID:', verifiedUser.id);
            console.log('   - Plan:', plan);
            
            const apiKeyResponse = await fetch(`${API_BASE_URL}/api-keys`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${loginData.access_token}`
                },
                body: JSON.stringify({
                    usuario_id: verifiedUser.id,
                    nombre: `API Key ${PLAN_NAMES[plan]}`,
                    plan: plan
                })
            });
            
            if (apiKeyResponse.ok) {
                const apiKeyData = await apiKeyResponse.json();
                apiKey = apiKeyData.key;
                console.log('✅ API Key creada exitosamente:', apiKey);
            } else {
                const errorData = await apiKeyResponse.json().catch(() => ({}));
                console.warn('⚠️ No se pudo crear API Key:', errorData.detail || apiKeyResponse.statusText);
                console.warn('   - Status:', apiKeyResponse.status);
            }
        } catch (apiKeyError) {
            console.warn('⚠️ Error al crear API Key automáticamente:', apiKeyError);
            // No es crítico, el usuario puede crear una después
        }
        
        // Cerrar modal de suscripción primero
        console.log('🔒 Cerrando modal de suscripción...');
        const subscribeModalElement = document.getElementById('subscribeModal');
        const subscribeModal = bootstrap.Modal.getInstance(subscribeModalElement);
        
        if (subscribeModal) {
            subscribeModal.hide();
        } else if (subscribeModalElement) {
            // Si no hay instancia, crear una y cerrarla
            const modal = new bootstrap.Modal(subscribeModalElement);
            modal.hide();
        }
        
        // Esperar a que el modal se cierre completamente antes de mostrar el de éxito
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Limpiar cualquier backdrop residual
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        console.log('✅ Modal de suscripción cerrado');
        
        // Actualizar información del usuario en el modal de éxito
        const userName = verifiedUser.nombre + (verifiedUser.apellido ? ' ' + verifiedUser.apellido : '');
        const userEmail = verifiedUser.email;
        
        // Actualizar información del usuario verificado
        const verifiedUserNameEl = document.getElementById('verifiedUserName');
        const verifiedUserEmailEl = document.getElementById('verifiedUserEmail');
        const generatedApiKeyEl = document.getElementById('generatedApiKey');
        
        if (verifiedUserNameEl) {
            verifiedUserNameEl.textContent = userName;
        }
        if (verifiedUserEmailEl) {
            verifiedUserEmailEl.textContent = userEmail;
        }
        
        // Mostrar API Key
        if (generatedApiKeyEl) {
            if (apiKey) {
                generatedApiKeyEl.textContent = apiKey;
                console.log('✅ API Key generada:', apiKey);
            } else {
                generatedApiKeyEl.textContent = 'No se pudo generar. Puedes crear una desde el panel de administración.';
                console.warn('⚠️ No se pudo generar API Key automáticamente');
            }
        }
        
        // Mostrar modal de éxito
        console.log('🎉 Mostrando modal de éxito...');
        const successModalElement = document.getElementById('successModal');
        if (successModalElement) {
            const successModal = new bootstrap.Modal(successModalElement, {
                backdrop: true,
                keyboard: true
            });
            successModal.show();
            
            // Guardar referencia para redirección
            window.verifiedSession = {
                user: verifiedUser,
                apiKey: apiKey,
                plan: plan
            };
            
            console.log('✅ Modal de éxito mostrado');
        } else {
            console.error('❌ No se encontró el modal de éxito');
            // Fallback: mostrar alerta
            alert(`¡Registro exitoso!\n\nUsuario: ${userName}\nEmail: ${userEmail}\n\n${apiKey ? `Tu API Key: ${apiKey}` : 'Puedes crear tu API Key desde el panel de administración.'}`);
        }
        
    } catch (error) {
        console.error('Error en suscripción:', error);
        
        // Mostrar error en el modal de suscripción
        const errorDiv = document.getElementById('subscribeError');
        if (errorDiv) {
            errorDiv.textContent = error.message || 'Error al procesar la suscripción. Por favor, intenta nuevamente.';
            errorDiv.classList.remove('d-none');
        } else {
            // Si no hay errorDiv (estamos en paso 2), mostrar alerta
            alert('Error: ' + (error.message || 'Error al procesar la suscripción. Por favor, intenta nuevamente.'));
        }
        
        // Restaurar botones
        const nextBtn = document.getElementById('nextBtn');
        const payBtn = document.getElementById('payBtn');
        
        if (nextBtn) {
            nextBtn.disabled = false;
            nextBtn.innerHTML = '<i class="fas fa-arrow-right me-2"></i>Continuar';
        }
        
        if (payBtn) {
            payBtn.disabled = false;
            payBtn.innerHTML = '<i class="fas fa-lock me-2"></i>Pagar y Suscribirse';
        }
    }
}

/**
 * Copiar API Key al portapapeles
 */
function copyApiKey() {
    const apiKey = document.getElementById('generatedApiKey').textContent;
    if (apiKey && apiKey !== 'Se creará después del login') {
        navigator.clipboard.writeText(apiKey).then(() => {
            // Mostrar feedback visual
            const btn = event.target.closest('button');
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check"></i> Copiado!';
            btn.classList.remove('btn-outline-success');
            btn.classList.add('btn-success');
            
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-success');
            }, 2000);
        }).catch(err => {
            console.error('Error copiando:', err);
            alert('No se pudo copiar al portapapeles. Por favor, copia manualmente.');
        });
    }
}

/**
 * Cerrar modal de suscripción correctamente
 */
function closeSubscribeModal() {
    console.log('🔒 Cerrando modal de suscripción...');
    
    const modalElement = document.getElementById('subscribeModal');
    if (!modalElement) {
        console.warn('Modal no encontrado');
        // Limpiar backdrop de todas formas
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        return;
    }
    
    // Cerrar usando Bootstrap si está disponible
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            modalInstance.hide();
        } else if (window.currentModal) {
            window.currentModal.hide();
        } else {
            // Cerrar manualmente
            const modal = new bootstrap.Modal(modalElement);
            modal.hide();
        }
    }
    
    // Limpiar backdrop manualmente si queda
    setTimeout(() => {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            console.log('🧹 Eliminando backdrop residual');
            backdrop.remove();
        });
        
        // Limpiar clases del body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // Restablecer aria-hidden
        modalElement.setAttribute('aria-hidden', 'true');
        modalElement.classList.remove('show');
        modalElement.style.display = 'none';
    }, 300);
}

// Exponer inmediatamente para que esté disponible
window.closeSubscribeModal = closeSubscribeModal;

/**
 * Redirigir al panel de administración
 */
function goToDashboard() {
    // Verificar que la sesión esté guardada
    const session = localStorage.getItem('biznews_admin_session');
    if (session) {
        try {
            const sessionData = JSON.parse(session);
            if (sessionData.access_token) {
                console.log('Redirigiendo al dashboard con sesión activa...');
                // Redirigir directamente al dashboard (el auth.js verificará la sesión)
                window.location.href = '../admin/dashboard.html';
                return;
            }
        } catch (e) {
            console.error('Error al leer sesión:', e);
        }
    }
    // Si no hay sesión válida, ir al login
    console.warn('No hay sesión válida, redirigiendo al login...');
    window.location.href = '../admin/login.html';
}

// ============================================
// EXPOSICIÓN GLOBAL DE FUNCIONES
// ============================================
// Exponer todas las funciones globalmente después de que todas estén definidas
// Nota: closeSubscribeModal ya se expuso arriba
window.openSubscribeModal = openSubscribeModal;
window.submitSubscription = submitSubscription;
window.copyApiKey = copyApiKey;
window.goToDashboard = goToDashboard;
window.nextStep = nextStep;
window.handleNextButton = handleNextButton;
window.goBackToUserInfo = goBackToUserInfo;
window.processPayment = processPayment;
window.copyCryptoAddress = copyCryptoAddress;
window.setupButtonListener = setupButtonListener;
// closeSubscribeModal ya está expuesta arriba

// Debug: verificar que las funciones estén disponibles
console.log('subscribe.js cargado completamente');
console.log('openSubscribeModal disponible:', typeof window.openSubscribeModal === 'function');
console.log('handleNextButton disponible:', typeof window.handleNextButton === 'function');
console.log('nextStep disponible:', typeof window.nextStep === 'function');
console.log('setupButtonListener disponible:', typeof window.setupButtonListener === 'function');

// También asegurarnos de que estén disponibles cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        window.openSubscribeModal = openSubscribeModal;
        window.submitSubscription = submitSubscription;
        window.copyApiKey = copyApiKey;
        window.nextStep = nextStep;
        window.handleNextButton = handleNextButton;
        window.goBackToUserInfo = goBackToUserInfo;
        window.processPayment = processPayment;
        window.copyCryptoAddress = copyCryptoAddress;
        console.log('Funciones de suscripción reasignadas después de DOMContentLoaded');
        console.log('handleNextButton disponible:', typeof window.handleNextButton === 'function');
        
        // Configurar formateo automático para campos de tarjeta
        setupCardFormatting();
    });
} else {
    // Si el DOM ya está listo, configurar inmediatamente
    setupCardFormatting();
}

/**
 * Configurar event listener para el botón Continuar
 */
function setupButtonListener() {
    console.log('🔧 setupButtonListener llamado');
    const nextBtn = document.getElementById('nextBtn');
    if (!nextBtn) {
        console.error('❌ Botón nextBtn no encontrado en setupButtonListener');
        return false;
    }
    
    console.log('✅ Botón nextBtn encontrado');
    console.log('   - Clases:', nextBtn.className);
    console.log('   - Visible:', !nextBtn.classList.contains('d-none'));
    console.log('   - Ya tiene listener:', nextBtn.hasAttribute('data-listener-added'));
    
    // Verificar si ya tiene el listener
    if (nextBtn.hasAttribute('data-listener-added')) {
        console.log('⚠️ Listener ya agregado al botón, pero lo reconfiguraremos...');
        // Remover el atributo para permitir reconfiguración
        nextBtn.removeAttribute('data-listener-added');
    }
    
    // Crear una función de handler que podamos referenciar
    const clickHandler = function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('🎯🎯🎯 BOTÓN CONTINUAR CLICKEADO!!!');
        console.log('   - currentStep:', currentStep);
        console.log('   - selectedPlan:', selectedPlan);
        console.log('   - handleNextButton tipo:', typeof handleNextButton);
        console.log('   - window.handleNextButton tipo:', typeof window.handleNextButton);
        
        // Intentar llamar la función
        try {
            if (typeof handleNextButton === 'function') {
                console.log('✅ Llamando handleNextButton directamente...');
                handleNextButton();
            } else if (typeof window.handleNextButton === 'function') {
                console.log('✅ Llamando window.handleNextButton...');
                window.handleNextButton();
            } else {
                console.error('❌ handleNextButton no está disponible');
                console.error('Funciones disponibles:', {
                    handleNextButton: typeof handleNextButton,
                    windowHandleNextButton: typeof window.handleNextButton,
                    nextStep: typeof nextStep,
                    windowNextStep: typeof window.nextStep
                });
                alert('Error: La función de pago no está disponible. Por favor, recarga la página.');
            }
        } catch (error) {
            console.error('❌ Error al ejecutar handleNextButton:', error);
            alert('Error: ' + error.message);
        }
    };
    
    // Remover cualquier listener anterior
    const newNextBtn = nextBtn.cloneNode(true);
    nextBtn.parentNode.replaceChild(newNextBtn, nextBtn);
    
    // Obtener la nueva referencia
    const actualNextBtn = document.getElementById('nextBtn');
    
    // Agregar listener directamente
    actualNextBtn.addEventListener('click', clickHandler, true); // Usar capture phase
    
    // También agregar como onclick como respaldo
    actualNextBtn.onclick = clickHandler;
    
    // Asegurar que el botón no esté deshabilitado
    actualNextBtn.disabled = false;
    actualNextBtn.removeAttribute('disabled');
    
    // Marcar que el listener fue agregado
    actualNextBtn.setAttribute('data-listener-added', 'true');
    console.log('✅✅✅ Event listener configurado para botón Continuar');
    console.log('   - Botón disabled:', actualNextBtn.disabled);
    console.log('   - Botón onclick:', typeof actualNextBtn.onclick);
    
    return true;
}

/**
 * Configurar formateo automático para campos de tarjeta
 */
function setupCardFormatting() {
    // Formatear número de tarjeta (agregar espacios cada 4 dígitos)
    const cardNumberInput = document.getElementById('cardNumber');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s/g, '');
            let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
            if (formattedValue.length <= 19) {
                e.target.value = formattedValue;
            } else {
                e.target.value = e.target.value.slice(0, -1);
            }
        });
    }
    
    // Formatear fecha de vencimiento (MM/AA)
    const cardExpiryInput = document.getElementById('cardExpiry');
    if (cardExpiryInput) {
        cardExpiryInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
        });
    }
    
    // Solo números para CVV
    const cardCVVInput = document.getElementById('cardCVV');
    if (cardCVVInput) {
        cardCVVInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }
}

// ============================================
// EXPOSICIÓN GLOBAL DE FUNCIONES
// ============================================
// Exponer todas las funciones globalmente después de que todas estén definidas
window.openSubscribeModal = openSubscribeModal;
window.submitSubscription = submitSubscription;
window.copyApiKey = copyApiKey;
window.goToDashboard = goToDashboard;
window.nextStep = nextStep;
window.handleNextButton = handleNextButton;
window.goBackToUserInfo = goBackToUserInfo;
window.processPayment = processPayment;
window.copyCryptoAddress = copyCryptoAddress;

// Debug: verificar que las funciones estén disponibles
console.log('subscribe.js cargado completamente');
console.log('openSubscribeModal disponible:', typeof window.openSubscribeModal === 'function');
console.log('handleNextButton disponible:', typeof window.handleNextButton === 'function');
console.log('nextStep disponible:', typeof window.nextStep === 'function');

