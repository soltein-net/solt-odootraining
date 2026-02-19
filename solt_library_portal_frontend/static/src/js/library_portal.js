/**
 * ============================================================================
 * JAVASCRIPT PARA EL PORTAL DE BIBLIOTECA
 * ============================================================================
 *
 * Este archivo contiene la funcionalidad JavaScript para el portal de biblioteca.
 *
 * CONCEPTOS CLAVE PARA LA CAPACITACIÓN:
 * =====================================
 *
 * 1. SISTEMA DE MÓDULOS DE ODOO 17:
 *    - Usa OWL (Odoo Web Library) como framework
 *    - Módulos ES6 con import/export
 *    - Servicios y componentes registrados globalmente
 *
 * 2. LLAMADAS JSON-RPC:
 *    - Odoo usa JSON-RPC 2.0 para comunicación AJAX
 *    - Formato específico con jsonrpc, method, params
 *    - Respuestas incluyen result o error
 *
 * 3. INTEGRACIÓN CON EL PORTAL:
 *    - El portal usa jQuery por compatibilidad
 *    - Podemos mezclar jQuery con vanilla JS
 *    - Event delegation para elementos dinámicos
 */

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

/**
 * Objeto principal del portal de biblioteca.
 * Agrupa todas las funcionalidades relacionadas.
 */
const LibraryPortal = {

    // ========================================================================
    // CONFIGURACIÓN
    // ========================================================================

    config: {
        // URLs de los endpoints
        endpoints: {
            search: '/library/search',
            categories: '/library/categories',
            authors: '/library/authors',
            checkAvailability: '/library/check_availability',
            memberStats: '/library/my/stats',
        },
        // Configuración de búsqueda
        searchDelay: 300, // ms de debounce
        minSearchLength: 2,
    },

    // ========================================================================
    // UTILIDADES
    // ========================================================================

    /**
     * Realiza una llamada JSON-RPC al servidor.
     *
     * FORMATO JSON-RPC 2.0:
     * ---------------------
     * {
     *   "jsonrpc": "2.0",
     *   "method": "call",
     *   "params": { ... },
     *   "id": <número único>
     * }
     *
     * @param {string} url - URL del endpoint
     * @param {object} params - Parámetros de la llamada
     * @returns {Promise} - Promesa con el resultado
     */
    async jsonRpc(url, params = {}) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: params,
                    id: Math.floor(Math.random() * 1000000),
                }),
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error.message || 'Error en la solicitud');
            }

            return data.result;
        } catch (error) {
            console.error('Error en JSON-RPC:', error);
            throw error;
        }
    },

    /**
     * Función de debounce para limitar llamadas frecuentes.
     *
     * Útil para búsquedas en tiempo real, evita hacer
     * una petición por cada tecla presionada.
     *
     * @param {function} func - Función a ejecutar
     * @param {number} wait - Tiempo de espera en ms
     * @returns {function} - Función con debounce
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Muestra una notificación tipo toast.
     *
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo: success, warning, danger, info
     */
    showNotification(message, type = 'info') {
        // Crear contenedor si no existe
        let container = document.querySelector('.library-notifications');
        if (!container) {
            container = document.createElement('div');
            container.className = 'library-notifications position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        // Crear toast
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        toast.role = 'alert';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        container.appendChild(toast);

        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 150);
        }, 5000);
    },

    // ========================================================================
    // BÚSQUEDA DE LIBROS
    // ========================================================================

    /**
     * Inicializa la funcionalidad de búsqueda en tiempo real.
     */
    initSearch() {
        const searchInput = document.querySelector('.library-search-bar input[name="search"]');
        if (!searchInput) return;

        // Crear contenedor de sugerencias
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'library-search-suggestions position-absolute w-100 mt-1 d-none';
        suggestionsContainer.style.zIndex = '1000';
        searchInput.parentNode.style.position = 'relative';
        searchInput.parentNode.appendChild(suggestionsContainer);

        // Búsqueda con debounce
        const performSearch = this.debounce(async (query) => {
            if (query.length < this.config.minSearchLength) {
                suggestionsContainer.classList.add('d-none');
                return;
            }

            try {
                const result = await this.jsonRpc(this.config.endpoints.search, {
                    query: query,
                    limit: 5,
                });

                if (result.status === 'success' && result.books.length > 0) {
                    this.renderSearchSuggestions(suggestionsContainer, result.books);
                    suggestionsContainer.classList.remove('d-none');
                } else {
                    suggestionsContainer.classList.add('d-none');
                }
            } catch (error) {
                console.error('Error en búsqueda:', error);
            }
        }, this.config.searchDelay);

        // Event listener para input
        searchInput.addEventListener('input', (e) => {
            performSearch(e.target.value);
        });

        // Cerrar sugerencias al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                suggestionsContainer.classList.add('d-none');
            }
        });
    },

    /**
     * Renderiza las sugerencias de búsqueda.
     *
     * @param {HTMLElement} container - Contenedor de sugerencias
     * @param {Array} books - Lista de libros encontrados
     */
    renderSearchSuggestions(container, books) {
        container.innerHTML = `
            <div class="list-group shadow">
                ${books.map(book => `
                    <a href="/my/library/book/${book.id}" class="list-group-item list-group-item-action">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${this.escapeHtml(book.name)}</strong>
                                <br>
                                <small class="text-muted">
                                    ${this.escapeHtml(book.authors.join(', '))}
                                </small>
                            </div>
                            <span class="badge bg-${book.state === 'available' ? 'success' : (book.state === 'low_stock' ? 'warning' : 'danger')}">
                                ${book.available_qty} disp.
                            </span>
                        </div>
                    </a>
                `).join('')}
            </div>
        `;
    },

    /**
     * Escapa HTML para prevenir XSS.
     *
     * SEGURIDAD:
     * ----------
     * SIEMPRE escapar datos que vienen del servidor o del usuario
     * antes de insertarlos en el DOM.
     *
     * @param {string} text - Texto a escapar
     * @returns {string} - Texto escapado
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // ========================================================================
    // VERIFICACIÓN DE DISPONIBILIDAD
    // ========================================================================

    /**
     * Inicializa la verificación de disponibilidad en tiempo real.
     * Útil en la página de detalle del libro.
     */
    initAvailabilityCheck() {
        const bookDetailPage = document.querySelector('.book-detail-image');
        if (!bookDetailPage) return;

        // Obtener ID del libro de la URL
        const pathParts = window.location.pathname.split('/');
        const bookId = pathParts[pathParts.length - 1];

        if (!bookId || isNaN(bookId)) return;

        // Verificar disponibilidad cada 30 segundos
        setInterval(async () => {
            try {
                const result = await this.jsonRpc(this.config.endpoints.checkAvailability, {
                    book_id: parseInt(bookId),
                });

                if (result.status === 'success') {
                    this.updateAvailabilityDisplay(result);
                }
            } catch (error) {
                console.error('Error verificando disponibilidad:', error);
            }
        }, 30000);
    },

    /**
     * Actualiza la visualización de disponibilidad.
     *
     * @param {object} data - Datos de disponibilidad
     */
    updateAvailabilityDisplay(data) {
        const alertElement = document.querySelector('.alert.alert-success, .alert.alert-warning, .alert.alert-danger');
        if (!alertElement) return;

        // Actualizar clase del alert
        alertElement.classList.remove('alert-success', 'alert-warning', 'alert-danger');
        const alertClass = data.state === 'available' ? 'success' :
                          (data.state === 'low_stock' ? 'warning' : 'danger');
        alertElement.classList.add(`alert-${alertClass}`);

        // Actualizar texto de disponibilidad
        const strongElement = alertElement.querySelector('strong');
        if (strongElement) {
            if (data.state === 'unavailable') {
                strongElement.textContent = 'No disponible';
            } else if (data.available_qty === 1) {
                strongElement.textContent = '1 copia disponible';
            } else {
                strongElement.textContent = `${data.available_qty} copias disponibles`;
            }
        }
    },

    // ========================================================================
    // ESTADÍSTICAS DEL MIEMBRO
    // ========================================================================

    /**
     * Inicializa la actualización de estadísticas del miembro.
     */
    async initMemberStats() {
        const statsContainer = document.querySelector('.library-member-stats');
        if (!statsContainer) return;

        try {
            const result = await this.jsonRpc(this.config.endpoints.memberStats);

            if (result.status === 'success') {
                // Las estadísticas ya están en la página, pero podemos actualizar
                // si hay cambios en tiempo real
                console.log('Estadísticas del miembro cargadas:', result.member);
            }
        } catch (error) {
            // Es normal que falle si el usuario no está autenticado
            console.log('No se pudieron cargar estadísticas del miembro');
        }
    },

    // ========================================================================
    // ANIMACIONES
    // ========================================================================

    /**
     * Inicializa animaciones de entrada.
     */
    initAnimations() {
        // Observador de intersección para animaciones al scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
        });

        // Observar tarjetas de libros
        document.querySelectorAll('.library-book-card').forEach(card => {
            observer.observe(card);
        });
    },

    // ========================================================================
    // FORMULARIOS
    // ========================================================================

    /**
     * Mejora los formularios con validación del lado del cliente.
     */
    initForms() {
        // Validación de formularios Bootstrap
        const forms = document.querySelectorAll('.needs-validation');

        forms.forEach(form => {
            form.addEventListener('submit', (event) => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    },

    // ========================================================================
    // INICIALIZACIÓN PRINCIPAL
    // ========================================================================

    /**
     * Inicializa todas las funcionalidades del portal.
     *
     * Se llama cuando el DOM está listo.
     */
    init() {
        console.log('Inicializando Library Portal...');

        // Inicializar módulos
        this.initSearch();
        this.initAvailabilityCheck();
        this.initMemberStats();
        this.initAnimations();
        this.initForms();

        console.log('Library Portal inicializado correctamente');
    },
};

// ============================================================================
// PUNTO DE ENTRADA
// ============================================================================

/**
 * Esperar a que el DOM esté listo.
 *
 * En Odoo 17, también podemos usar el sistema de módulos OWL,
 * pero para el portal es más simple usar vanilla JS.
 */
document.addEventListener('DOMContentLoaded', () => {
    LibraryPortal.init();
});

