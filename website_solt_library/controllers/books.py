from odoo import http
from odoo.http import request


class LibraryBooksController(http.Controller):
    @http.route([
        "/libros",
    ], auth='public', type='http', website=True)
    def list_books(self, **kwargs):
        category_id = kwargs.get('category_id')
        search_query = kwargs.get('book-name', '').strip()
        domain = [('website_id', 'in', [False, request.website.id]), ('website_published', '=', True)]
        if category_id:
            domain.append(('category_id', '=', int(category_id)))
        if search_query:
            domain.append(('name', 'ilike', search_query))
        books = request.env['library.book'].search(domain, limit=10)
        categories = request.env['library.category'].search([])
        return request.render('website_solt_library.books_list', {
            'books': books,
            'categories': categories,
            'selected_category': int(category_id) if category_id else None,
            'search_query': search_query,
        })