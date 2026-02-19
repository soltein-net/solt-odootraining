# -*- coding: utf-8 -*-
"""
================================================================================
EXTENSIÓN DEL MODELO BOOK PARA EL PORTAL
================================================================================

Este archivo extiende el modelo library.book para agregar funcionalidades
necesarias en el contexto del portal web.

CONCEPTOS CLAVE PARA LA CAPACITACIÓN:
-------------------------------------

1. HERENCIA DE MODELOS (_inherit):
   - Usamos _inherit para agregar campos y métodos
   - El modelo original NO se modifica directamente
   - Los campos se agregan a la tabla existente

2. CAMPOS COMPUTADOS PARA EL PORTAL:
   - Pueden preparar datos para visualización web
   - Evitan lógica compleja en los templates

3. MÉTODOS AUXILIARES:
   - Encapsulan lógica de negocio
   - Facilitan el uso desde controladores
"""

from odoo import api, fields, models


class LibraryBook(models.Model):
    _inherit = 'library.book'

    # =========================================================================
    # CAMPOS ADICIONALES PARA EL PORTAL
    # =========================================================================

    # URL amigable para el libro (para SEO)
    website_slug = fields.Char(
        string='URL Slug',
        compute='_compute_website_slug',
        store=True,
        help='Identificador único para URLs amigables'
    )

    # Indicador de libro destacado
    is_featured = fields.Boolean(
        string='Destacado en Portal',
        default=False,
        help='Mostrar este libro en la sección destacada del portal'
    )

    # Resumen corto para listados
    short_description = fields.Text(
        string='Descripción Corta',
        compute='_compute_short_description',
        help='Versión resumida de la descripción para listados'
    )

    # =========================================================================
    # MÉTODOS COMPUTADOS
    # =========================================================================

    @api.depends('name')
    def _compute_website_slug(self):
        """
        Genera un slug URL-friendly para el libro.

        SLUG:
        -----
        Un slug es un identificador amigable para URLs.
        Ejemplo: "El Quijote" -> "el-quijote-5"

        Útil para URLs como: /library/book/el-quijote-5
        en lugar de: /library/book/5

        NOTA: No podemos usar 'id' en @api.depends porque el id
        no existe durante la creación del registro. El campo se
        recalculará automáticamente al guardar gracias a store=True.
        """
        for book in self:
            if book.name:
                # Convertir a minúsculas y reemplazar espacios
                slug = book.name.lower()
                # Reemplazar caracteres especiales
                slug = ''.join(c if c.isalnum() else '-' for c in slug)
                # Eliminar guiones múltiples
                while '--' in slug:
                    slug = slug.replace('--', '-')
                # Agregar ID para unicidad (puede ser False si es nuevo)
                record_id = book.id or 'new'
                book.website_slug = f"{slug.strip('-')}-{record_id}"
            else:
                book.website_slug = str(book.id) if book.id else 'new'

    @api.depends('description')
    def _compute_short_description(self):
        """
        Genera una descripción corta para listados.

        Trunca la descripción a 150 caracteres máximo
        para mostrar en tarjetas de catálogo.
        """
        for book in self:
            if book.description:
                if len(book.description) > 150:
                    book.short_description = book.description[:147] + '...'
                else:
                    book.short_description = book.description
            else:
                book.short_description = ''

    # =========================================================================
    # MÉTODOS AUXILIARES PARA EL PORTAL
    # =========================================================================

    def get_portal_url(self):
        """
        Retorna la URL del libro en el portal.

        Esta función facilita la generación de URLs en templates
        y controladores.

        Returns:
            str: URL completa del libro en el portal
        """
        self.ensure_one()
        return f'/my/library/book/{self.id}'

    def get_availability_class(self):
        """
        Retorna la clase CSS basada en disponibilidad.

        Útil para aplicar estilos condicionales en el frontend.

        Returns:
            str: Nombre de clase CSS (success, warning, danger)
        """
        self.ensure_one()
        if self.state == 'available':
            return 'success'
        elif self.state == 'low_stock':
            return 'warning'
        else:
            return 'danger'

    def get_availability_text(self):
        """
        Retorna texto de disponibilidad para mostrar.

        Returns:
            str: Texto descriptivo del estado de disponibilidad
        """
        self.ensure_one()
        if self.state == 'unavailable':
            return 'No disponible'
        elif self.available_qty == 1:
            return '1 copia disponible'
        else:
            return f'{self.available_qty} copias disponibles'

    @api.model
    def get_featured_books(self, limit=6):
        """
        Obtiene libros destacados para el portal.

        Función de clase que busca libros marcados como destacados
        para mostrar en la página principal del portal.

        Args:
            limit: Número máximo de libros a retornar

        Returns:
            recordset: Libros destacados
        """
        return self.search([
            ('is_featured', '=', True),
            ('state', '!=', 'unavailable'),
            ('active', '=', True)
        ], limit=limit, order='name')

    @api.model
    def get_recent_books(self, limit=6):
        """
        Obtiene los libros más recientes del catálogo.

        Args:
            limit: Número máximo de libros a retornar

        Returns:
            recordset: Libros ordenados por fecha de creación
        """
        return self.search([
            ('state', '!=', 'unavailable'),
            ('active', '=', True)
        ], limit=limit, order='create_date desc')

    def format_authors_for_display(self):
        """
        Formatea la lista de autores para mostrar en el portal.

        Returns:
            str: Nombres de autores separados por coma
        """
        self.ensure_one()
        return ', '.join(self.author_ids.mapped('name'))
