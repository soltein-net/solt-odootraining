# -*- coding: utf-8 -*-
"""
================================================================================
CONTROLADOR DEL PORTAL DE BIBLIOTECA
================================================================================

Este archivo contiene los controladores HTTP que exponen la funcionalidad
de la biblioteca a través del portal web de Odoo.

CONCEPTOS CLAVE PARA LA CAPACITACIÓN:
-------------------------------------

1. HERENCIA DE CONTROLADORES:
   - CustomerPortal es la clase base del portal de Odoo
   - Heredamos para agregar nuestras propias secciones al portal
   - Usamos super() para mantener funcionalidad existente

2. DECORADORES DE RUTA:
   - @http.route(): Define una URL accesible
   - type='http': Retorna HTML (vs 'json' para API)
   - auth='user': Requiere usuario autenticado
   - auth='public': Acceso público
   - website=True: Usa el layout del website

3. ACCESO A DATOS:
   - request.env: Acceso al ORM
   - sudo(): Ejecución con permisos elevados
   - search_read(): Búsqueda optimizada

4. PAGINACIÓN:
   - portal_pager(): Helper para crear paginación
   - limit/offset: Control de registros mostrados

5. SEGURIDAD:
   - _document_check_access(): Verificar acceso a documentos
   - Dominios de búsqueda restringidos
"""

from collections import OrderedDict
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import AND, OR


class LibraryPortal(CustomerPortal):
    """
    Controlador del portal para el módulo de biblioteca.

    Hereda de CustomerPortal para integrar las funcionalidades
    de biblioteca en el portal existente de Odoo.
    """

    # =========================================================================
    # Función _prepare_home_portal_values
    # =========================================================================
    # Esta función se llama cuando se renderiza la página principal del portal.
    # Se usa para agregar contadores de nuestros modelos en la barra lateral.

    def _prepare_home_portal_values(self, counters):
        """
        Prepara los valores para la página principal del portal.

        Esta función es CLAVE para integrar nuestro módulo en el portal.
        Agrega contadores que aparecerán en la barra lateral del portal.

        Args:
            counters: Lista de contadores solicitados por el template

        Returns:
            dict: Valores actualizados con nuestros contadores
        """
        # IMPORTANTE: Siempre llamar a super() primero
        values = super()._prepare_home_portal_values(counters)

        # Obtener el miembro de biblioteca asociado al usuario actual
        partner = request.env.user.partner_id
        LibraryMember = request.env['library.member'].sudo()

        # Buscar si el usuario tiene un perfil de miembro
        member = LibraryMember.search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        # Agregar contador de préstamos activos si se solicita
        if 'loan_count' in counters:
            if member:
                values['loan_count'] = request.env['library.loan'].sudo().search_count([
                    ('member_id', '=', member.id),
                    ('state', '=', 'loaned')
                ])
            else:
                values['loan_count'] = 0

        # Agregar contador de libros disponibles (acceso público)
        if 'book_count' in counters:
            values['book_count'] = request.env['library.book'].sudo().search_count([
                ('state', '!=', 'unavailable')
            ])

        return values

    # =========================================================================
    # PÁGINA PRINCIPAL DEL CATÁLOGO DE LIBROS
    # =========================================================================

    @http.route(
        ['/my/library', '/my/library/page/<int:page>'],
        type='http',
        auth='public',
        website=True
    )
    def portal_my_library(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """
        Muestra el catálogo de libros en el portal.

        DECORADOR @http.route():
        ------------------------
        - Lista de URLs: Permite múltiples rutas para el mismo método
        - type='http': Retorna HTML renderizado
        - auth='public': Acceso sin autenticación (también usuarios anónimos)
        - website=True: Usa el contexto del website (layout, menús, etc.)

        PARÁMETROS:
        -----------
        - page: Número de página para paginación
        - sortby: Campo de ordenamiento
        - filterby: Filtro activo
        - search: Término de búsqueda
        - **kw: Parámetros adicionales
        """
        Book = request.env['library.book'].sudo()

        # Dominio base: Solo libros activos
        domain = [('active', '=', True)]

        # =====================================================================
        # OPCIONES DE ORDENAMIENTO
        # =====================================================================
        # Definimos las opciones disponibles para ordenar resultados.
        # Cada opción tiene una etiqueta y el campo(s) de ordenamiento.

        searchbar_sortings = {
            'name': {'label': 'Título', 'order': 'name asc'},
            'date': {'label': 'Fecha de Publicación', 'order': 'publication_date desc'},
            'category': {'label': 'Categoría', 'order': 'category_id, name'},
            'availability': {'label': 'Disponibilidad', 'order': 'available_qty desc'},
        }

        # Ordenamiento por defecto
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        # =====================================================================
        # OPCIONES DE FILTRADO
        # =====================================================================
        # Filtros predefinidos que el usuario puede seleccionar.
        # Cada filtro modifica el dominio de búsqueda.

        searchbar_filters = {
            'all': {'label': 'Todos', 'domain': []},
            'available': {'label': 'Disponibles', 'domain': [('state', '=', 'available')]},
            'low_stock': {'label': 'Pocas Copias', 'domain': [('state', '=', 'low_stock')]},
        }

        # Filtro por defecto
        if not filterby:
            filterby = 'all'
        domain = AND([domain, searchbar_filters[filterby]['domain']])

        # =====================================================================
        # BÚSQUEDA POR TEXTO
        # =====================================================================
        # Permitir búsqueda en múltiples campos.

        if search:
            search_domain = OR([
                [('name', 'ilike', search)],
                [('isbn', 'ilike', search)],
                [('author_ids.name', 'ilike', search)],
                [('category_id.name', 'ilike', search)],
            ])
            domain = AND([domain, search_domain])

        # =====================================================================
        # PAGINACIÓN
        # =====================================================================
        # Usamos portal_pager para generar la paginación.
        # Esto crea los enlaces de navegación entre páginas.

        book_count = Book.search_count(domain)

        pager = portal_pager(
            url='/my/library',
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=book_count,
            page=page,
            step=12  # Libros por página
        )

        # =====================================================================
        # CONSULTA DE DATOS
        # =====================================================================
        # search_read es más eficiente que search + read por separado.

        books = Book.search(
            domain,
            order=order,
            limit=12,
            offset=pager['offset']
        )

        # Obtener categorías para filtro adicional
        categories = request.env['library.category'].sudo().search([])

        # =====================================================================
        # PREPARAR VALORES PARA EL TEMPLATE
        # =====================================================================

        values = {
            'books': books,
            'book_count': book_count,
            'page_name': 'library',
            'default_url': '/my/library',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'search': search,
            'categories': categories,
        }

        return request.render('solt_library_portal_frontend.portal_my_library', values)

    # =========================================================================
    # DETALLE DE UN LIBRO
    # =========================================================================

    @http.route(
        ['/my/library/book/<int:book_id>'],
        type='http',
        auth='public',
        website=True
    )
    def portal_book_detail(self, book_id, **kw):
        """
        Muestra el detalle de un libro específico.

        PARÁMETROS EN LA URL:
        ---------------------
        - <int:book_id>: Captura el ID del libro de la URL
          Ejemplo: /my/library/book/5 -> book_id = 5

        SEGURIDAD:
        ----------
        - Usamos sudo() porque los usuarios del portal no tienen
          acceso directo a library.book
        - Validamos que el libro existe y está activo
        """
        Book = request.env['library.book'].sudo()

        # Buscar el libro
        book = Book.browse(book_id)

        # Verificar que existe y está activo
        if not book.exists() or not book.active:
            # Redirigir al catálogo si no se encuentra
            return request.redirect('/my/library')

        # Obtener libros relacionados (misma categoría)
        related_books = Book.search([
            ('category_id', '=', book.category_id.id),
            ('id', '!=', book.id),
            ('state', '!=', 'unavailable')
        ], limit=4)

        values = {
            'book': book,
            'related_books': related_books,
            'page_name': 'library_book',
        }

        return request.render('solt_library_portal_frontend.portal_book_detail', values)

    # =========================================================================
    # PRÉSTAMOS DEL USUARIO
    # =========================================================================

    @http.route(
        ['/my/loans', '/my/loans/page/<int:page>'],
        type='http',
        auth='user',  # REQUIERE AUTENTICACIÓN
        website=True
    )
    def portal_my_loans(self, page=1, sortby=None, filterby=None, **kw):
        """
        Muestra los préstamos del usuario autenticado.

        AUTH='USER':
        ------------
        A diferencia del catálogo (public), esta ruta REQUIERE
        que el usuario esté autenticado. Si no lo está, Odoo
        redirige automáticamente al login.

        ACCESO A DATOS PROPIOS:
        -----------------------
        Solo mostramos los préstamos del miembro asociado al
        usuario actual. Esto es una restricción de seguridad
        importante.
        """
        Loan = request.env['library.loan'].sudo()
        partner = request.env.user.partner_id

        # Buscar el miembro de biblioteca
        member = request.env['library.member'].sudo().search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not member:
            # Si no es miembro, mostrar página vacía
            values = {
                'loans': [],
                'page_name': 'loans',
                'is_member': False,
            }
            return request.render('solt_library_portal_frontend.portal_my_loans', values)

        # Dominio base: Solo préstamos de este miembro
        domain = [('member_id', '=', member.id)]

        # Opciones de ordenamiento
        searchbar_sortings = {
            'date': {'label': 'Fecha de Préstamo', 'order': 'loan_date desc'},
            'return': {'label': 'Fecha de Devolución', 'order': 'expected_return_date asc'},
            'book': {'label': 'Libro', 'order': 'book_id'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Opciones de filtrado
        searchbar_filters = {
            'all': {'label': 'Todos', 'domain': []},
            'active': {'label': 'Activos', 'domain': [('state', '=', 'loaned')]},
            'overdue': {'label': 'Vencidos', 'domain': [('state', '=', 'loaned'), ('days_overdue', '>', 0)]},
            'returned': {'label': 'Devueltos', 'domain': [('state', '=', 'returned')]},
        }

        if not filterby:
            filterby = 'active'
        domain = AND([domain, searchbar_filters[filterby]['domain']])

        # Paginación
        loan_count = Loan.search_count(domain)
        pager = portal_pager(
            url='/my/loans',
            url_args={'sortby': sortby, 'filterby': filterby},
            total=loan_count,
            page=page,
            step=10
        )

        # Consultar préstamos
        loans = Loan.search(domain, order=order, limit=10, offset=pager['offset'])

        values = {
            'loans': loans,
            'member': member,
            'page_name': 'loans',
            'default_url': '/my/loans',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'is_member': True,
        }

        return request.render('solt_library_portal_frontend.portal_my_loans', values)

    # =========================================================================
    # DETALLE DE UN PRÉSTAMO
    # =========================================================================

    @http.route(
        ['/my/loans/<int:loan_id>'],
        type='http',
        auth='user',
        website=True
    )
    def portal_loan_detail(self, loan_id, **kw):
        """
        Muestra el detalle de un préstamo específico.

        VERIFICACIÓN DE ACCESO:
        -----------------------
        Es CRÍTICO verificar que el préstamo pertenece al usuario
        actual. Nunca confiar solo en el ID recibido.
        """
        partner = request.env.user.partner_id

        # Buscar el miembro
        member = request.env['library.member'].sudo().search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not member:
            return request.redirect('/my/loans')

        # Buscar el préstamo verificando que pertenece al miembro
        loan = request.env['library.loan'].sudo().search([
            ('id', '=', loan_id),
            ('member_id', '=', member.id)  # IMPORTANTE: Verificar propiedad
        ], limit=1)

        if not loan:
            return request.redirect('/my/loans')

        values = {
            'loan': loan,
            'page_name': 'loan_detail',
        }

        return request.render('solt_library_portal_frontend.portal_loan_detail', values)

    # =========================================================================
    # PERFIL DEL MIEMBRO
    # =========================================================================

    @http.route(
        ['/my/library/profile'],
        type='http',
        auth='user',
        website=True
    )
    def portal_member_profile(self, **kw):
        """
        Muestra el perfil del miembro de biblioteca.

        Incluye:
        - Información de membresía
        - Estadísticas de préstamos
        - Recargos pendientes
        """
        partner = request.env.user.partner_id

        member = request.env['library.member'].sudo().search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        values = {
            'member': member,
            'page_name': 'library_profile',
            'is_member': bool(member),
        }

        return request.render('solt_library_portal_frontend.portal_member_profile', values)
