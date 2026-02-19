# -*- coding: utf-8 -*-
"""
================================================================================
CONTROLADORES AUXILIARES Y API JSON
================================================================================

Este archivo contiene controladores adicionales para:
1. Búsquedas AJAX/JSON
2. Acciones específicas del portal
3. Descarga de documentos

CONCEPTOS CLAVE PARA LA CAPACITACIÓN:
-------------------------------------

1. CONTROLADORES JSON (type='json'):
   - Reciben y retornan JSON
   - Ideales para llamadas AJAX
   - Usan POST por defecto
   - Retornan dict que se serializa automáticamente

2. RESPUESTAS PERSONALIZADAS:
   - request.make_response(): Respuestas con headers personalizados
   - Binary fields: Manejo de archivos e imágenes

3. CSRF Y SEGURIDAD:
   - csrf=False: Deshabilita protección CSRF (usar con cuidado)
   - Validación de parámetros de entrada
"""

import json
from odoo import http
from odoo.http import request, Response


class LibraryController(http.Controller):
    """
    Controlador principal para funcionalidades adicionales del portal.

    A diferencia de LibraryPortal, este NO hereda de CustomerPortal.
    Es un controlador independiente para funcionalidades específicas.
    """

    # =========================================================================
    # BÚSQUEDA DE LIBROS (JSON/AJAX)
    # =========================================================================

    @http.route(
        '/library/search',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def search_books(self, query='', category_id=None, limit=10, **kw):
        """
        Búsqueda de libros vía AJAX.

        TYPE='JSON':
        ------------
        - Recibe datos JSON en el body de la petición
        - Los parámetros se extraen automáticamente del JSON
        - Retorna un dict que Odoo serializa a JSON
        - El Content-Type de la respuesta es application/json

        LLAMADA DESDE JAVASCRIPT:
        -------------------------
        ```javascript
        const result = await fetch('/library/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    query: 'Python',
                    category_id: 5,
                    limit: 20
                }
            })
        });
        ```

        Returns:
            dict: Lista de libros encontrados con datos básicos
        """
        Book = request.env['library.book'].sudo()

        domain = [
            ('active', '=', True),
            ('state', '!=', 'unavailable')
        ]

        # Agregar filtro de búsqueda
        if query:
            domain.append(('name', 'ilike', query))

        # Agregar filtro de categoría
        if category_id:
            domain.append(('category_id', '=', int(category_id)))

        # Buscar libros
        books = Book.search_read(
            domain,
            fields=['id', 'name', 'isbn', 'available_qty', 'state'],
            limit=limit,
            order='name'
        )

        # Agregar información de autores (Many2many requiere consulta adicional)
        for book in books:
            book_record = Book.browse(book['id'])
            book['authors'] = book_record.author_ids.mapped('name')
            book['category'] = book_record.category_id.name or ''

        return {
            'status': 'success',
            'count': len(books),
            'books': books
        }

    # =========================================================================
    # OBTENER CATEGORÍAS (JSON)
    # =========================================================================

    @http.route(
        '/library/categories',
        type='json',
        auth='public',
        methods=['POST']
    )
    def get_categories(self, **kw):
        """
        Obtiene lista de categorías para selectores dinámicos.

        Útil para poblar dropdowns o filtros en el frontend
        sin recargar la página completa.
        """
        Category = request.env['library.category'].sudo()

        categories = Category.search_read(
            [],
            fields=['id', 'complete_name', 'book_count'],
            order='complete_name'
        )

        return {
            'status': 'success',
            'categories': categories
        }

    # =========================================================================
    # OBTENER AUTORES (JSON)
    # =========================================================================

    @http.route(
        '/library/authors',
        type='json',
        auth='public',
        methods=['POST']
    )
    def get_authors(self, search='', limit=20, **kw):
        """
        Búsqueda de autores para autocompletado.

        Ejemplo de uso en campo de búsqueda con sugerencias.
        """
        Author = request.env['library.author'].sudo()

        domain = []
        if search:
            domain.append(('name', 'ilike', search))

        authors = Author.search_read(
            domain,
            fields=['id', 'name', 'nationality', 'book_count'],
            limit=limit,
            order='name'
        )

        return {
            'status': 'success',
            'authors': authors
        }

    # =========================================================================
    # VERIFICAR DISPONIBILIDAD (JSON)
    # =========================================================================

    @http.route(
        '/library/check_availability',
        type='json',
        auth='public',
        methods=['POST']
    )
    def check_availability(self, book_id, **kw):
        """
        Verifica la disponibilidad de un libro en tiempo real.

        Útil para actualizar la interfaz sin recargar la página
        cuando el usuario está viendo el detalle de un libro.
        """
        if not book_id:
            return {'status': 'error', 'message': 'ID de libro requerido'}

        Book = request.env['library.book'].sudo()
        book = Book.browse(int(book_id))

        if not book.exists():
            return {'status': 'error', 'message': 'Libro no encontrado'}

        return {
            'status': 'success',
            'book_id': book.id,
            'available_qty': book.available_qty,
            'total_qty': book.total_qty,
            'state': book.state,
            'is_available': book.state != 'unavailable'
        }

    # =========================================================================
    # ESTADÍSTICAS DEL MIEMBRO (JSON)
    # =========================================================================

    @http.route(
        '/library/my/stats',
        type='json',
        auth='user',
        methods=['POST']
    )
    def get_member_stats(self, **kw):
        """
        Obtiene estadísticas del miembro autenticado.

        AUTH='USER':
        ------------
        Para rutas JSON con auth='user', si el usuario no está
        autenticado, Odoo retorna un error JSON en lugar de
        redirigir al login.

        IMPORTANTE: Siempre verificar que el usuario tiene
        un perfil de miembro antes de consultar datos.
        """
        partner = request.env.user.partner_id

        member = request.env['library.member'].sudo().search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not member:
            return {
                'status': 'error',
                'message': 'No tienes un perfil de miembro de biblioteca'
            }

        return {
            'status': 'success',
            'member': {
                'code': member.code,
                'membership_type': member.membership_type,
                'state': member.state,
                'active_loans': member.active_loan_count,
                'overdue_loans': member.overdue_loan_count,
                'pending_fees': member.pending_fees,
                'max_loans': member.max_loans,
                'expiration_date': member.expiration_date.isoformat() if member.expiration_date else None,
            }
        }

    # =========================================================================
    # DESCARGA DE RECIBO DE PRÉSTAMO (HTTP)
    # =========================================================================

    @http.route(
        '/my/loans/<int:loan_id>/download',
        type='http',
        auth='user',
        website=True
    )
    def download_loan_receipt(self, loan_id, **kw):
        """
        Genera y descarga el recibo de préstamo en PDF.

        GENERACIÓN DE PDF:
        ------------------
        - Usamos el sistema de reportes de Odoo
        - report_action_id: ID del reporte definido en XML
        - render_qweb_pdf: Genera el PDF

        HEADERS DE DESCARGA:
        --------------------
        - Content-Type: application/pdf
        - Content-Disposition: Fuerza descarga con nombre de archivo
        """
        partner = request.env.user.partner_id

        # Verificar que el préstamo pertenece al usuario
        member = request.env['library.member'].sudo().search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not member:
            return request.redirect('/my/loans')

        loan = request.env['library.loan'].sudo().search([
            ('id', '=', loan_id),
            ('member_id', '=', member.id)
        ], limit=1)

        if not loan:
            return request.redirect('/my/loans')

        # Generar PDF usando el reporte definido en solt_library
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'solt_library.action_report_loan',
            [loan.id]
        )

        # Crear nombre de archivo
        filename = f'loan_receipt_{loan.reference}.pdf'

        # Retornar como descarga
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ]
        )

    # =========================================================================
    # IMAGEN DE LIBRO (HTTP)
    # =========================================================================

    @http.route(
        '/library/book/<int:book_id>/image',
        type='http',
        auth='public',
    )
    def book_image(self, book_id, **kw):
        """
        Sirve la imagen de portada de un libro.

        MANEJO DE IMÁGENES:
        -------------------
        - Las imágenes se almacenan en campos Binary
        - image_128, image_256, image_1920 son tamaños comunes
        - Usamos stream=True para respuestas binarias eficientes

        CACHÉ:
        ------
        - Los headers de caché mejoran el rendimiento
        - Las imágenes pueden cachearse por el navegador
        """
        Book = request.env['library.book'].sudo()
        book = Book.browse(book_id)

        if not book.exists() or not book.image_128:
            # Retornar imagen por defecto o 404
            return request.not_found()

        # Retornar imagen con headers de caché
        return request.env['ir.binary']._get_image_stream_from(
            book, 'image_256'
        ).get_response()

    # =========================================================================
    # AUTOR IMAGEN (HTTP)
    # =========================================================================

    @http.route(
        '/library/author/<int:author_id>/image',
        type='http',
        auth='public',
    )
    def author_image(self, author_id, **kw):
        """
        Sirve la imagen de avatar de un autor.
        """
        Author = request.env['library.author'].sudo()
        author = Author.browse(author_id)

        if not author.exists() or not author.avatar_128:
            return request.not_found()

        return request.env['ir.binary']._get_image_stream_from(
            author, 'avatar_256'
        ).get_response()
